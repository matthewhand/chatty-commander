import React, { useRef } from 'react';

export default function CanvasPane() {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  return (
    <section className="flex-1 flex flex-col">
      <iframe
        ref={iframeRef}
        title="canvas"
        sandbox="allow-scripts allow-downloads"
        className="flex-1 bg-white"
      />
      <div
        id="console-pane"
        className="h-40 overflow-auto bg-black text-green-400 text-xs p-2"
        aria-label="Console"
        tabIndex={-1}
      >
        Console output...
      </div>
    </section>
  );
}
