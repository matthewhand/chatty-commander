import React, { useEffect, useRef } from 'react';
import { createBus } from '../lib/bus';
import { useCanvasStore } from '../stores/canvas';

const iframeSrcDoc = `
<script>
const send = line => parent.postMessage({ type: 'canvas:log', line }, '*');
['log','warn','error'].forEach(m => {
  const orig = console[m];
  console[m] = (...args) => { send(args.join(' ')); orig.apply(console, args); };
});
</script>
`;

export default function CanvasPane() {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const { logs, addLog, setStatus, asciiOnly } = useCanvasStore((s) => ({
    logs: s.logs,
    addLog: s.addLog,
    setStatus: s.setStatus,
    asciiOnly: s.asciiOnly,
  }));

  useEffect(() => {
    const es = new EventSource('/api/console/stream');
    es.addEventListener('line', (e) => {
      try {
        const data = JSON.parse((e as MessageEvent).data);
        if (data?.line) addLog(data.line);
      } catch {}
    });

    const handleMessage = (event: MessageEvent) => {
      if (event.data?.type === 'canvas:log') {
        addLog(event.data.line);
      }
    };
    window.addEventListener('message', handleMessage);
    return () => {
      es.close();
      window.removeEventListener('message', handleMessage);
    };
  }, [addLog]);

  useEffect(() => {
    const iframe = iframeRef.current;
    if (!iframe) return;

    let off: (() => void) | undefined;

    async function load() {
      setStatus('loading');
      try {
        const res = await fetch('/api/canvas/build', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ asciiOnly }),
        });
        const info = await res.json();
        iframe.src = info.bundleUrl;
        iframe.onload = () => {
          if (!iframe.contentWindow) return;
          const bus = createBus(iframe.contentWindow);
          off = bus.onAny((type, payload) => {
            if (type.startsWith('canvas:')) {
              addLog(`${type}: ${JSON.stringify(payload)}`);
            }
          });
          bus.post('canvas:init', info);
          setStatus('ready');
        };
      } catch (err: any) {
        addLog(`error: ${err.message}`);
        setStatus('error');
      }
    }

    load();

    return () => {
      off?.();
    };
  }, [addLog, asciiOnly, setStatus]);

  return (
    <section className="flex-1 flex flex-col bg-gray-900">
      <iframe
        title="canvas"
        sandbox="allow-scripts allow-downloads"
        className="flex-1 bg-gray-800"
        srcDoc={iframeSrcDoc}
      />
      <div className="h-40 overflow-auto bg-black text-green-400 text-xs p-2" aria-label="Console">
        {logs.map((l, i) => (
          <div key={i}>{l}</div>
        ))}
      </div>
    </section>
  );
}
