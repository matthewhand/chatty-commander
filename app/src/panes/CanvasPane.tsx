import React, { useEffect, useRef, useState } from 'react';
import { createBus } from '../lib/bus';

export default function CanvasPane() {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [log, setLog] = useState<string[]>([]);

  useEffect(() => {
    const iframe = iframeRef.current;
    if (!iframe || !iframe.contentWindow) return;
    const bus = createBus(iframe.contentWindow);
    const off = bus.onAny((type, payload) => {
      if (type.startsWith('canvas:')) {
        setLog((l) => [...l, `${type}: ${JSON.stringify(payload)}`]);
      }
    });
    bus.post('canvas:ready');
    return () => off();
  }, []);

  return (
    <section className="flex-1 flex flex-col bg-gray-900">
      <iframe
        ref={iframeRef}
        title="canvas"
        sandbox="allow-scripts allow-downloads"
        className="flex-1 bg-gray-800"
      />
      <div className="h-40 overflow-auto bg-black text-green-400 text-xs p-2" aria-label="Console">
        {log.map((l, i) => (
          <div key={i}>{l}</div>
        ))}
      </div>
    </section>
  );
}
