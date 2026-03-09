import { trace, metrics, Context, SpanKind, SpanStatusCode } from '@opentelemetry/api';
import { WebTracerProvider } from '@opentelemetry/sdk-trace-web';
import { BatchSpanProcessor } from '@opentelemetry/sdk-trace-base';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { MeterProvider } from '@opentelemetry/sdk-metrics';
import { PeriodicExportingMetricReader } from '@opentelemetry/sdk-metrics';
import { OTLPMetricExporter } from '@opentelemetry/exporter-metrics-otlp-http';

const tracerProvider = new WebTracerProvider();
const traceExporter = new OTLPTraceExporter({
  url: '/v1/traces',
});

tracerProvider.addSpanProcessor(new BatchSpanProcessor(traceExporter));
tracerProvider.register();

const meterProvider = new MeterProvider();
const metricExporter = new OTLPMetricExporter({
  url: '/v1/metrics',
});

const metricReader = new PeriodicExportingMetricReader({
  exporter: metricExporter,
  exportIntervalMillis: 60000,
});

meterProvider.addMetricReader(metricReader);
metrics.setGlobalMeterProvider(meterProvider);

export const tracer = trace.getTracer('chatty-commander', '1.0.0');
export const meter = metrics.getMeter('chatty-commander', '1.0.0');

export const lcpHistogram = meter.createHistogram('lcp', {
  description: 'Largest Contentful Paint',
  unit: 'ms',
});

export const hydrationHistogram = meter.createHistogram('hydration', {
  description: 'React hydration time',
  unit: 'ms',
});

export function initTelemetry() {
  if (typeof window !== 'undefined' && 'performance' in window) {
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.entryType === 'largest-contentful-paint') {
          lcpHistogram.record(entry.startTime);
        }
      }
    });
    observer.observe({ entryTypes: ['largest-contentful-paint'] });
  }
}

export function recordHydration(startTime: number) {
  const endTime = performance.now();
  hydrationHistogram.record(endTime - startTime);
}

export function startSendSpan(): (span: ReturnType<typeof tracer.startSpan>) => void {
  const span = tracer.startSpan('chat.send', {
    kind: SpanKind.CLIENT,
    attributes: {
      'service.name': 'chatty-commander',
    },
  });

  return () => {
    span.end();
  };
}

export function traceCanvasLoad(src: string, onLoad: () => void) {
  const span = tracer.startSpan('canvas.load', {
    kind: SpanKind.CLIENT,
    attributes: {
      'canvas.src': src,
      'service.name': 'chatty-commander',
    },
  });

  const originalOnLoad = onLoad;
  const wrappedOnLoad = () => {
    span.setStatus({ code: SpanStatusCode.OK });
    span.end();
    originalOnLoad();
  };

  return wrappedOnLoad;
}

export function createSpan<T>(
  name: string,
  fn: (span: ReturnType<typeof tracer.startSpan>) => T,
  attributes?: Record<string, string>
): T {
  const span = tracer.startSpan(name, {
    kind: SpanKind.INTERNAL,
    attributes: {
      'service.name': 'chatty-commander',
      ...attributes,
    },
  });

  try {
    const result = fn(span);
    span.setStatus({ code: SpanStatusCode.OK });
    return result;
  } catch (error) {
    span.recordException(error as Error);
    span.setStatus({ code: SpanStatusCode.ERROR });
    throw error;
  } finally {
    span.end();
  }
}