import React, { useRef, useEffect } from 'react';
import { useCanvasStore } from '../stores/canvas';

export default function CanvasPane() {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const consoleRef = useRef<HTMLPreElement>(null);
  const logs = useCanvasStore(s => s.logs);

  useEffect(() => {
    if (consoleRef.current) {
      consoleRef.current.textContent = logs.join('\n');
    }
  }, [logs]);

  return (
    <section className="flex-1 flex flex-col">
      <iframe
        ref={iframeRef}
        title="canvas"
        sandbox="allow-scripts allow-downloads"
        className="flex-1 bg-white"
      />
      <pre
        ref={consoleRef}
        className="h-40 overflow-auto bg-black text-green-400 text-xs p-2"
        aria-label="Console"
      />
    </section>
  );
}
