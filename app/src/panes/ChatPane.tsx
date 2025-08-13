import React from 'react';

export default function ChatPane() {
  return (
    <section className="h-full flex flex-col">
      <div className="flex-1 overflow-auto p-2">Chat messages will appear here.</div>
      <textarea className="p-2 bg-gray-800" placeholder="Type a message" />
    </section>
  );
}
