import { create } from 'zustand';
import { v4 as uuidv4 } from 'uuid';

interface SessionStore {
  id: string;
  user?: { id?: string; name?: string };
  flags: { ws?: boolean };
}

export const useSessionStore = create<SessionStore>(() => ({
  id: uuidv4(),
  user: undefined,
  flags: {},
}));
