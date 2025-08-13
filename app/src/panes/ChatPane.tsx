import React, { useState, KeyboardEvent, useEffect, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { useChatStore, ChatMessage } from '../stores/chat';
import { sse } from '../lib/sse';

export default function ChatPane() {
  const messages = useChatStore(s => s.messages);
  const push = useChatStore(s => s.push);
  const update = useChatStore(s => s.update);
  const [text, setText] = useState('');

  const send = useCallback(async () => {
    const content = text.trim();
    if (!content) return;
    const userMsg: ChatMessage = {
      id: uuidv4(),
      role: 'user',
      createdAt: new Date().toISOString(),
      content: [{ type: 'text', text: content }],
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
          content: [{ type: 'text', text: (m.content?.[0]?.text ?? '') + delta }],
        }));
      },
      done: () => {},
    });
  }, [text, push, update, setText]);

  useEffect(() => {
    const handler = () => {
      void send();
    };
    window.addEventListener('chat:send', handler);
    return () => window.removeEventListener('chat:send', handler);
  }, [send]);

  const handleKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <section className="h-full flex flex-col" aria-label="Chat">
      <div className="flex-1 overflow-auto p-2">
        {messages.map(m => (
          <div key={m.id} className="mb-2">
            <div className="text-xs text-gray-400">{m.role}</div>
            <div>{m.content[0]?.text}</div>
          </div>
        ))}
      </div>
      <div className="p-2 border-t border-gray-700">
        <textarea
          id="chat-input"
          className="w-full p-2 bg-gray-800"
          placeholder="Type a message"
          value={text}
          onChange={e => setText(e.target.value)}
          onKeyDown={handleKey}
        />
        <button
          className="mt-2 px-3 py-1 bg-blue-600 rounded"
          onClick={send}
        >
          Send
        </button>
      </div>
    </section>
  );
}
