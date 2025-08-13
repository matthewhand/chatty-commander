import React, { useState, useEffect } from 'react';
import { useSidecarStore } from '../stores/sidecar';

const TABS = [
  { key: 'code', label: 'Code' },
  { key: 'tests', label: 'Tests' },
  { key: 'notes', label: 'Notes' },
  { key: 'diff', label: 'Diff' },
];

export default function SidecarPane() {
  const current = useSidecarStore(s => s.current);
  const close = useSidecarStore(s => s.close);
  const [tab, setTab] = useState<'code' | 'tests' | 'notes' | 'diff'>('code');
  const [comment, setComment] = useState('');

  useEffect(() => {
    if (current?.kind) setTab(current.kind);
  }, [current]);

  return (
    <section className="h-full flex flex-col">
      <header className="flex items-center justify-between p-2 border-b border-gray-700">
        <h2 className="font-semibold">{current?.title || 'Sidecar'}</h2>
        <button onClick={close} aria-label="Close" className="px-2">×</button>
      </header>
      <nav className="flex border-b border-gray-700">
        {TABS.map(t => (
          <button
            key={t.key}
            className={`px-3 py-1 text-sm ${tab === t.key ? 'bg-gray-800' : ''}`}
            onClick={() => setTab(t.key as any)}
          >
            {t.label}
          </button>
        ))}
      </nav>
      <div className="flex-1 overflow-auto p-2">
        {current?.snippet ? (
          <pre className="text-xs whitespace-pre-wrap">{current.snippet}</pre>
        ) : (
          <div className="text-gray-400">Open files and notes will appear here.</div>
        )}
      </div>
      <div className="p-2 border-t border-gray-700">
        <textarea
          className="w-full p-2 bg-gray-800"
          placeholder="Add a comment"
          value={comment}
          onChange={e => setComment(e.target.value)}
        />
        <button className="mt-2 px-3 py-1 bg-blue-600 rounded">Comment</button>
      </div>
    </section>
  );
}
