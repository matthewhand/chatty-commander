import React, { useEffect, useState } from 'react';
import { useSidecarStore } from '../stores/sidecar';

type Tab = 'code' | 'tests' | 'notes' | 'diff';
const TABS: { value: Tab; label: string }[] = [
  { value: 'code', label: 'Code' },
  { value: 'tests', label: 'Tests' },
  { value: 'notes', label: 'Notes' },
  { value: 'diff', label: 'Diff' },
];

export default function SidecarPane() {
  const { open, current } = useSidecarStore();
  const [active, setActive] = useState<Tab>('code');
  const [content, setContent] = useState('');

  useEffect(() => {
    if (current) {
      setActive(current.kind);
      if (current.contentUrl) {
        fetch(current.contentUrl)
          .then(r => r.text())
          .then(setContent)
          .catch(() => setContent(''));
      } else {
        setContent(current.snippet || '');
      }
    } else {
      setContent('');
    }
  }, [current]);

  if (!open || !current) {
    return (
      <section className="h-full p-2">
        <h2 className="font-semibold mb-2">Sidecar</h2>
        <div>Open files and notes will appear here.</div>
      </section>
    );
  }

  return (
    <section className="h-full flex flex-col">
      <div className="flex border-b border-gray-700">
        {TABS.map(t => (
          <button
            key={t.value}
            className={`px-3 py-1 ${active === t.value ? 'bg-gray-800' : ''}`}
            onClick={() => setActive(t.value)}
          >
            {t.label}
          </button>
        ))}
      </div>
      <div className="flex-1 overflow-auto p-2">
        {content ? (
          <pre className="whitespace-pre-wrap">{content}</pre>
        ) : (
          <div>No content</div>
        )}
      </div>
    </section>
  );
}
