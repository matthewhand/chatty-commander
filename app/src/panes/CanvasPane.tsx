import React, { useEffect, useRef } from 'react';
import { createBus } from '../lib/bus';
import { useCanvasStore } from '../stores/canvas';

export default function CanvasPane() {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const { logs, addLog, setStatus, asciiOnly } = useCanvasStore((s) => ({
    logs: s.logs,
    addLog: s.addLog,
    setStatus: s.setStatus,
    asciiOnly: s.asciiOnly,
  }));

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
        ref={iframeRef}
        title="canvas"
        sandbox="allow-scripts allow-downloads"
        className="flex-1 bg-gray-800"
      />
      <div className="h-40 overflow-auto bg-black text-green-400 text-xs p-2" aria-label="Console">
        {logs.map((l, i) => (
          <div key={i}>{l}</div>
        ))}
      </div>
    </section>
  );
}
