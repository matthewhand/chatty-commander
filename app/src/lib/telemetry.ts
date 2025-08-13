import { trace, metrics } from '@opentelemetry/api';
import { WebTracerProvider } from '@opentelemetry/sdk-trace-web';
import { BatchSpanProcessor } from '@opentelemetry/sdk-trace-base';
import { Resource } from '@opentelemetry/resources';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { MeterProvider, PeriodicExportingMetricReader } from '@opentelemetry/sdk-metrics';
import { OTLPMetricExporter } from '@opentelemetry/exporter-metrics-otlp-http';

const resource = new Resource({ 'service.name': 'chatty-commander' });

const tracerProvider = new WebTracerProvider({ resource });
tracerProvider.addSpanProcessor(new BatchSpanProcessor(new OTLPTraceExporter()));
tracerProvider.register();

const meterProvider = new MeterProvider({ resource });
meterProvider.addMetricReader(
  new PeriodicExportingMetricReader({
    exporter: new OTLPMetricExporter(),
    exportIntervalMillis: 60000,
  })
);
metrics.setGlobalMeterProvider(meterProvider);

const tracer = trace.getTracer('app');
const meter = meterProvider.getMeter('app');
const lcpMetric = meter.createHistogram('lcp', { description: 'Largest Contentful Paint', unit: 'ms' });
const hydrationMetric = meter.createHistogram('hydration', { description: 'Hydration time', unit: 'ms' });

const SAMPLE_RATE = 0.1;
const metricsEnabled = Math.random() < SAMPLE_RATE;
let hydrationStart = performance.now();

export function initTelemetry() {
  if (metricsEnabled && 'PerformanceObserver' in window) {
    try {
      const po = new PerformanceObserver(list => {
        const entries = list.getEntries();
        const last = entries[entries.length - 1];
        lcpMetric.record(last.startTime);
      });
      po.observe({ type: 'largest-contentful-paint', buffered: true });
    } catch {
      // ignore observer errors
    }
  }
}

export function recordHydration() {
  if (metricsEnabled) {
    hydrationMetric.record(performance.now() - hydrationStart);
  }
}

export function startSendSpan() {
  const span = tracer.startSpan('send->first-token');
  let ended = false;
  return () => {
    if (!ended) {
      span.end();
      ended = true;
    }
  };
}

export function traceCanvasLoad(el: HTMLIFrameElement) {
  const span = tracer.startSpan('canvas-load');
  const onLoad = () => {
    span.end();
    el.removeEventListener('load', onLoad);
  };
  el.addEventListener('load', onLoad);
}
