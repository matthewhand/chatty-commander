import { create } from 'zustand';

interface SidecarItem {
  refId: string;
  title: string;
  kind: 'code' | 'tests' | 'diff' | 'notes';
  contentUrl?: string;
  snippet?: string;
}

interface SidecarStore {
  open: boolean;
  current?: SidecarItem;
  set: (item: SidecarItem) => void;
  close: () => void;
}

export const useSidecarStore = create<SidecarStore>(set => ({
  open: false,
  current: undefined,
  set: item => {
    set({ open: true, current: item });
    if (item.contentUrl && !item.snippet) {
      fetch(item.contentUrl)
        .then(res => res.text())
        .then(text => set({ open: true, current: { ...item, snippet: text } }))
        .catch(() => {});
    }
  },
  close: () => set({ open: false, current: undefined }),
}));
