import React from 'react';

export default function CanvasPane() {
  return (
    <section className="flex-1 flex flex-col bg-gray-900">
      <iframe
        title="canvas"
        sandbox="allow-scripts allow-downloads"
        className="flex-1 bg-gray-800"
      />
    </section>
  );
}
