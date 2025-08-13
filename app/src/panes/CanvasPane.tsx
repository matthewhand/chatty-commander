import React, { useEffect, useRef } from 'react';
import { on, post } from '../lib/bus';
import { useCanvasStore } from '../stores/canvas';

export default function CanvasPane() {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const { logs, addLog, setStatus, asciiOnly } = useCanvasStore();

  useEffect(() => {
    let readyOff: (() => void) | undefined;
    let logOff: (() => void) | undefined;

    async function load() {
      setStatus('loading');
      try {
        const res = await fetch('/api/canvas/build', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ asciiOnly })
        });
        const data = await res.json();
        if (iframeRef.current) {
          iframeRef.current.src = data.bundleUrl;
        }
      } catch (err) {
        setStatus('error');
      }

      readyOff = on('canvas:ready', () => {
        setStatus('ready');
        post(iframeRef.current?.contentWindow, 'canvas:init');
      });

      logOff = on<string>('canvas:log', line => {
        addLog(line);
      });
    }

    load();

    return () => {
      readyOff?.();
      logOff?.();
    };
  }, [asciiOnly, setStatus, addLog]);

  return (
    <section className="flex-1 flex flex-col">
      <iframe
        ref={iframeRef}
        title="canvas"
        sandbox="allow-scripts allow-downloads"
        className="flex-1 bg-white"
      />
      <div className="h-40 overflow-auto bg-black text-green-400 text-xs p-2" aria-label="Console">
        {logs.map((line, i) => (
          <div key={i}>{line}</div>
        ))}
      </div>
    </section>
  );
}
