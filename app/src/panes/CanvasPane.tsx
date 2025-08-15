import React, { useRef, useEffect } from 'react';
import { useCanvasStore } from '../stores/canvas';

export default function CanvasPane() {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const asciiOnly = useCanvasStore(s => s.asciiOnly);

  useEffect(() => {
    if (!asciiOnly || !iframeRef.current) return;
    const doc = iframeRef.current.contentDocument;
    if (!doc) return;
    const script = doc.createElement('script');
    script.textContent = `
      Object.defineProperty(window, 'localStorage', { get: () => undefined });
      Object.defineProperty(window, 'sessionStorage', { get: () => undefined });
      Object.defineProperty(window, 'indexedDB', { value: undefined });
    `;
    doc.head.appendChild(script);
  }, [asciiOnly]);
  return (
    <section className="flex-1 flex flex-col">
      <iframe
        ref={iframeRef}
        title="canvas"
        sandbox="allow-scripts allow-downloads"
        className="flex-1 bg-white"
      />
      <div className="h-40 overflow-auto bg-black text-green-400 text-xs p-2" aria-label="Console">
        Console output...
      </div>
    </section>
  );
}
