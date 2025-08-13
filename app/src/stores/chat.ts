import { create } from 'zustand';

export type Role = 'user' | 'assistant' | 'system' | 'tool';

export interface ChatMessage {
  id: string;
  role: Role;
  createdAt: string;
  content: any[];
  contextRef?: { pane: 'sidecar' | 'canvas'; refId?: string };
  meta?: Record<string, any>;
}

interface ChatStore {
  messages: ChatMessage[];
  push: (m: ChatMessage) => void;
  update: (id: string, fn: (m: ChatMessage) => ChatMessage) => void;
}

export const useChatStore = create<ChatStore>(set => ({
  messages: [],
  push: m => set(s => ({ messages: [...s.messages, m] })),
  update: (id, fn) =>
    set(s => ({ messages: s.messages.map(m => (m.id === id ? fn(m) : m)) })),
}));
