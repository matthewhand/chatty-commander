import React, { useEffect, useRef } from 'react';
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
  const logs = useCanvasStore(s => s.logs);
  const addLog = useCanvasStore(s => s.addLog);

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

  return (
    <section className="flex-1 flex flex-col">
      <iframe
        ref={iframeRef}
        title="canvas"
        sandbox="allow-scripts allow-downloads"
        className="flex-1 bg-white"
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
