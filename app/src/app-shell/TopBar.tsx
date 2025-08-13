import React from 'react';

export default function TopBar() {
  return (
    <header className="flex items-center px-4 py-2 bg-gray-800 text-gray-100 border-b border-gray-700">
      <h1 className="flex-1 text-lg font-semibold">Chatty Commander</h1>
      <div className="space-x-2">
        <button
          aria-label="Run"
          className="px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded"
        >
          ▶
        </button>
        <button
          aria-label="Stop"
          className="px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded"
        >
          ■
        </button>
      </div>
    </header>
  );
}
