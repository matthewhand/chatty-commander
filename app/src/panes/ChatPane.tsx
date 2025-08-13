import React, { useState, useRef, useEffect, KeyboardEvent } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { useChatStore, ChatMessage } from '../stores/chat';
import { sse } from '../lib/sse';

interface MessageItemProps {
  message: ChatMessage;
}

function MessageItem({ message }: MessageItemProps) {
  const roleStyles: Record<string, string> = {
    user: 'bg-blue-700 text-white',
    assistant: 'bg-gray-700 text-white',
    system: 'bg-yellow-800 text-yellow-100',
    tool: 'bg-green-700 text-white',
  };

  const renderBlocks = (text: string) => {
    const blocks: { type: 'text' | 'code'; value: string }[] = [];
    const regex = /```(?:\w+)?\n([\s\S]*?)```/g;
    let lastIndex = 0;
    let match: RegExpExecArray | null;
    while ((match = regex.exec(text))) {
      if (match.index > lastIndex) {
        blocks.push({ type: 'text', value: text.slice(lastIndex, match.index) });
      }
      blocks.push({ type: 'code', value: match[1] });
      lastIndex = regex.lastIndex;
    }
    if (lastIndex < text.length) {
      blocks.push({ type: 'text', value: text.slice(lastIndex) });
    }
    return blocks;
  };

  return (
    <div className={`mb-2 p-2 rounded ${roleStyles[message.role] ?? ''}`}>
      {renderBlocks(message.content[0]?.text ?? '').map((b, i) =>
        b.type === 'code' ? (
          <pre key={i} className="relative bg-black bg-opacity-40 p-2 rounded">
            <button
              onClick={() => navigator.clipboard.writeText(b.value)}
              className="absolute top-1 right-1 text-xs text-gray-300 hover:text-white"
            >
              copy
            </button>
            <code>{b.value}</code>
          </pre>
        ) : (
          <p key={i}>{b.value}</p>
        ),
      )}
    </div>
  );
}

function MessageList({ messages }: { messages: ChatMessage[] }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [range, setRange] = useState({ start: 0, end: 20 });
  const itemHeight = 64;

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const onScroll = () => {
      const scrollTop = el.scrollTop;
      const height = el.clientHeight;
      const start = Math.max(0, Math.floor(scrollTop / itemHeight) - 5);
      const end = Math.min(
        messages.length,
        start + Math.ceil(height / itemHeight) + 10,
      );
      setRange({ start, end });
    };
    el.addEventListener('scroll', onScroll);
    return () => el.removeEventListener('scroll', onScroll);
  }, [messages.length]);

  useEffect(() => {
    const el = containerRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages.length]);

  const slice = messages.slice(range.start, range.end);
  const topPadding = range.start * itemHeight;
  const bottomPadding = (messages.length - range.end) * itemHeight;

  return (
    <div ref={containerRef} className="flex-1 overflow-auto p-2">
      <div style={{ paddingTop: topPadding, paddingBottom: bottomPadding }}>
        {slice.map(m => (
          <MessageItem key={m.id} message={m} />
        ))}
      </div>
    </div>
  );
}

export default function ChatPane() {
  const messages = useChatStore(s => s.messages);
  const push = useChatStore(s => s.push);
  const update = useChatStore(s => s.update);
  const [text, setText] = useState('');
  const [useSidecar, setUseSidecar] = useState(true);
  const [useCanvas, setUseCanvas] = useState(true);

  const send = async () => {
    const content = text.trim();
    if (!content) return;
    const userMsg: ChatMessage = {
      id: uuidv4(),
      role: 'user',
      createdAt: new Date().toISOString(),
      content: [{ type: 'text', text: content }],
      contextRef: useSidecar
        ? { pane: 'sidecar' }
        : useCanvas
        ? { pane: 'canvas' }
        : undefined,
    };
    push(userMsg);
    setText('');

    const assistantId = uuidv4();
    push({
      id: assistantId,
      role: 'assistant',
      createdAt: new Date().toISOString(),
      content: [{ type: 'text', text: '' }],
    });

    await sse('/api/chat', { messages: [userMsg] }, {
      chunk: ({ delta }) => {
        update(assistantId, m => ({
          ...m,
          content: [
            {
              type: 'text',
              text: (m.content?.[0]?.text ?? '') + delta,
            },
          ],
        }));
      },
      done: () => {},
    });
  };

  const handleKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <section className="h-full flex flex-col" aria-label="Chat">
      <MessageList messages={messages} />
      <div className="px-2 py-1 text-xs text-yellow-400">
        Responses may be inaccurate. Do not share sensitive information.
      </div>
      <div className="p-2 border-t border-gray-700">
        <textarea
          className="w-full p-2 bg-gray-800"
          placeholder="Type a message"
          value={text}
          onChange={e => setText(e.target.value)}
          onKeyDown={handleKey}
        />
        <div className="flex items-center justify-between mt-2">
          <div className="text-xs text-gray-300 space-x-2">
            <label>
              <input
                type="checkbox"
                checked={useSidecar}
                onChange={e => setUseSidecar(e.target.checked)}
                className="mr-1"
              />
              Sidecar
            </label>
            <label>
              <input
                type="checkbox"
                checked={useCanvas}
                onChange={e => setUseCanvas(e.target.checked)}
                className="mr-1"
              />
              Canvas
            </label>
          </div>
          <button
            className="px-3 py-1 bg-blue-600 rounded"
            onClick={send}
          >
            Send
          </button>
        </div>
      </div>
    </section>
  );
}
