import { create } from 'zustand';

interface CanvasStore {
  status: 'idle' | 'loading' | 'ready' | 'error';
  asciiOnly: boolean;
  logs: string[];
  setStatus: (s: CanvasStore['status']) => void;
  setAscii: (flag: boolean) => void;
  addLog: (line: string) => void;
  clearLogs: () => void;
}

export const useCanvasStore = create<CanvasStore>(set => ({
  status: 'idle',
  asciiOnly: false,
  logs: [],
  setStatus: status => set({ status }),
  setAscii: asciiOnly => set({ asciiOnly }),
  addLog: line => set(s => ({ logs: [...s.logs, line].slice(-2000) })),
  clearLogs: () => set({ logs: [] }),
}));
