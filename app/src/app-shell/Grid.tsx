import React from 'react';

interface Props {
  children: React.ReactNode[];
}

export default function GridLayout({ children }: Props) {
  return (
    <div className="flex flex-1 overflow-hidden">
      <div className="w-90 border-r border-gray-700 overflow-y-auto bg-gray-900" aria-label="Chat">
        {children[0]}
      </div>
      <div className="flex-1 flex flex-col bg-gray-900" aria-label="Canvas">
        {children[1]}
      </div>
      <div className="w-130 border-l border-gray-700 overflow-y-auto bg-gray-900" aria-label="Review">
        {children[2]}
      </div>
    </div>
  );
}
