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
  /**
   * Apply a transformation to a message by id.
   */
  update: (id: string, fn: (m: ChatMessage) => ChatMessage) => void;
  /**
   * Replace a message entirely by id.
   */
  replace: (id: string, msg: ChatMessage) => void;
  /**
   * Summarise the conversation so that the estimated token
   * count does not exceed the provided budget. The summariser
   * function is invoked with the messages that were removed
   * from the start of the conversation and should return a
   * new summary message.
   */
  summariseForBudget: (
    tokenBudget: number,
    summariser: (msgs: ChatMessage[]) => ChatMessage,
  ) => void;
}

export const useChatStore = create<ChatStore>(set => ({
  messages: [],
  push: m => set(s => ({ messages: [...s.messages, m] })),
  update: (id, fn) =>
    set(s => ({ messages: s.messages.map(m => (m.id === id ? fn(m) : m)) })),
  replace: (id, msg) =>
    set(s => ({ messages: s.messages.map(m => (m.id === id ? msg : m)) })),
  summariseForBudget: (tokenBudget, summariser) =>
    set(s => {
      const estimateTokens = (msgs: ChatMessage[]) =>
        msgs.reduce(
          (sum, m) => sum + (m.content?.[0]?.text?.length ?? 0),
          0,
        );

      let msgs = [...s.messages];
      if (estimateTokens(msgs) <= tokenBudget) return { messages: msgs };

      const removed: ChatMessage[] = [];
      while (msgs.length && estimateTokens(msgs) > tokenBudget) {
        removed.push(msgs.shift()!);
      }

      if (removed.length) {
        msgs.unshift(summariser(removed));
      }

      return { messages: msgs };
    }),
}));
