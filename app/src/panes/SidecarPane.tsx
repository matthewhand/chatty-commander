import React from 'react';

export default function SidecarPane() {
  return (
    <section
      id="review-pane"
      className="h-full p-2"
      aria-label="Review"
      tabIndex={-1}
    >
      <h2 className="font-semibold mb-2">Sidecar</h2>
      <div>Open files and notes will appear here.</div>
    </section>
  );
}
