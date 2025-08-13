import React from 'react';

interface Props {
  children: React.ReactNode[];
}

export default function GridLayout({ children }: Props) {
  return (
    <div className="flex flex-1 overflow-hidden">
      <section
        id="chat-pane"
        className="w-90 border-r border-gray-700 overflow-y-auto"
        aria-label="Chat"
        tabIndex={-1}
      >
        {children[0]}
      </section>
      <section
        id="canvas-pane"
        className="flex-1 flex flex-col"
        aria-label="Canvas"
        tabIndex={-1}
      >
        {children[1]}
      </section>
      <section
        id="review-pane"
        className="w-130 border-l border-gray-700 overflow-y-auto"
        aria-label="Review"
        tabIndex={-1}
      >
        {children[2]}
      </section>
    </div>
  );
}
