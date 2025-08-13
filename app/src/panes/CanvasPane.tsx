import React, { useRef } from 'react';

export default function CanvasPane() {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  return (
    <section className="flex-1 flex flex-col bg-gray-900">
      <iframe
        ref={iframeRef}
        title="canvas"
        sandbox="allow-scripts allow-downloads"
        className="flex-1 bg-gray-800"
      />
      <div className="h-40 overflow-auto bg-black text-green-400 text-xs p-2" aria-label="Console">
        Console output...
      </div>
    </section>
  );
}
