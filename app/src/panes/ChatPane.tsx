import React, { useState, KeyboardEvent } from "react";
import { v4 as uuidv4 } from "uuid";
import { useChatStore, ChatMessage } from "../stores/chat";
import { useSidecarStore } from "../stores/sidecar";
import { sse } from "../lib/sse";

export default function ChatPane() {
  const messages = useChatStore((s) => s.messages);
  const push = useChatStore((s) => s.push);
  const update = useChatStore((s) => s.update);
  const setSidecar = useSidecarStore((s) => s.set);
  const [text, setText] = useState("");

  const send = async () => {
    const content = text.trim();
    if (!content) return;
    const userMsg: ChatMessage = {
      id: uuidv4(),
      role: "user",
      createdAt: new Date().toISOString(),
      content: [{ type: "text", text: content }],
    };
    push(userMsg);
    setText("");

    let assistantId: string | null = null;

    await sse(
      "/api/chat",
      { messages: [userMsg] },
      {
        chunk: ({ id, delta }) => {
          if (!assistantId) {
            assistantId = id;
            push({
              id,
              role: "assistant",
              createdAt: new Date().toISOString(),
              content: [{ type: "text", text: "" }],
            });
          }
          update(id, (m) => ({
            ...m,
            content: [
              { type: "text", text: (m.content?.[0]?.text ?? "") + delta },
            ],
          }));
        },
        tool_call: ({ id }) => {
          push({
            id,
            role: "tool",
            createdAt: new Date().toISOString(),
            content: [{ type: "text", text: "" }],
          });
        },
        tool_result: ({ id, delta }) => {
          update(id, (m) => ({
            ...m,
            content: [
              { type: "text", text: (m.content?.[0]?.text ?? "") + delta },
            ],
          }));
        },
        tool: data => {
          if ((data?.name === 'open_file' || data?.name === 'open_diff') && data.path) {
            const isDiff = data.name === 'open_diff' || data.diff;
            setSidecar({
              refId: data.path,
              title: data.path,
              kind: isDiff ? 'diff' : 'code',
              contentUrl: `/api/sidecar/file?path=${encodeURIComponent(data.path)}${
                isDiff ? '&diff=1' : ''
              }`,
            });
          }
        },
        'sidecar.open': data => {
          setSidecar(data);
        },
        done: () => {},
      },
    );
  };

  const handleKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <section className="h-full flex flex-col bg-gray-900" aria-label="Chat">
      <div className="flex-1 overflow-auto p-2">
        {messages.map((m) => (
          <div key={m.id} className="mb-2">
            <div className="text-xs text-gray-400">{m.role}</div>
            <div>{m.content[0]?.text}</div>
          </div>
        ))}
      </div>
      <div className="p-2 border-t border-gray-700 bg-gray-900">
        <textarea
          className="w-full p-2 bg-gray-800 text-gray-100 border border-gray-700"
          placeholder="Type a message"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKey}
        />
        <button
          className="mt-2 px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded"
          onClick={send}
        >
          Send
        </button>
      </div>
    </section>
  );
}
