import React, { useEffect, useMemo, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link, useSearchParams } from 'react-router-dom';
import {
  TerminalSquare,
  Keyboard,
  Globe,
  MessageSquare,
  Mic,
  Plus,
  Edit3,
  Trash2,
  PlayCircle,
  RefreshCw,
  Search,
  Download,
  Upload,
  ArrowUpDown,
  X
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiService } from '../services/apiService';
import { DynamicDropdown } from '../components/DynamicDropdown';
import { useToast } from '../components/ToastProvider';
import { useReducedMotionPref } from '../hooks/useReducedMotionPref';

// Backend response is a Record<string, CommandConfig>
interface CommandConfig {
  action?: string; // 'keypress' | 'url' | 'shell' | 'custom_message' | 'voice_chat'
  keys?: string;
  url?: string;
  cmd?: string;
  message?: string;
}

// Cap the framer-motion entrance stagger so large lists don't animate with an
// unbounded delay (the last rows would otherwise wait seconds before appearing).
const MAX_STAGGER_INDEX = 12;
const STAGGER_STEP = 0.03;

// The "every command is REST-triggerable" note is useful once, then just noise.
// Persist its dismissal so it stays hidden across reloads (mirrors the
// dashboard onboarding callout's localStorage pattern).
const REST_API_NOTE_DISMISSED_KEY = "chatty.commandsRestApiNoteDismissed";

function readRestApiNoteDismissed(): boolean {
  try {
    return window.localStorage.getItem(REST_API_NOTE_DISMISSED_KEY) === "1";
  } catch {
    // localStorage may be unavailable (private mode / SSR); default to showing.
    return false;
  }
}

function persistRestApiNoteDismissed(): void {
  try {
    window.localStorage.setItem(REST_API_NOTE_DISMISSED_KEY, "1");
  } catch {
    // Best-effort; if we can't persist, the note simply reappears next load.
  }
}

type CommandTypeKey = 'keypress' | 'url' | 'shell' | 'voice_chat' | 'custom_message' | 'unknown';

interface CommandTypeMeta {
  key: CommandTypeKey;
  label: string;
  badgeClass: string;
  Icon: typeof TerminalSquare;
}

const TYPE_META: Record<CommandTypeKey, CommandTypeMeta> = {
  keypress: { key: 'keypress', label: 'Keypress', badgeClass: 'badge-primary', Icon: Keyboard },
  url: { key: 'url', label: 'URL', badgeClass: 'badge-info', Icon: Globe },
  shell: { key: 'shell', label: 'Shell', badgeClass: 'badge-warning', Icon: TerminalSquare },
  voice_chat: { key: 'voice_chat', label: 'Voice', badgeClass: 'badge-secondary', Icon: Mic },
  custom_message: { key: 'custom_message', label: 'Message', badgeClass: 'badge-accent', Icon: MessageSquare },
  unknown: { key: 'unknown', label: 'Other', badgeClass: 'badge-ghost', Icon: TerminalSquare },
};

// Derive the command's type from its config. The explicit `action` field wins;
// otherwise we infer it from whichever payload field is populated.
function getCommandType(config: CommandConfig): CommandTypeMeta {
  const action = config.action;
  if (action === 'keypress') return TYPE_META.keypress;
  if (action === 'url') return TYPE_META.url;
  if (action === 'shell') return TYPE_META.shell;
  if (action === 'voice_chat') return TYPE_META.voice_chat;
  if (action === 'custom_message') return TYPE_META.custom_message;
  // Infer from payload when action is missing/unrecognized.
  if (config.keys) return TYPE_META.keypress;
  if (config.url) return TYPE_META.url;
  if (config.cmd) return TYPE_META.shell;
  if (config.message) return TYPE_META.custom_message;
  return TYPE_META.unknown;
}

// Human-readable summary of what a command actually does.
function describeAction(config: CommandConfig): { label: string; detail: string } {
  if (config.url) return { label: 'Opens URL', detail: config.url };
  if (config.keys) return { label: 'Presses keys', detail: config.keys };
  if (config.cmd) return { label: 'Runs command', detail: config.cmd };
  if (config.message) return { label: 'Sends message', detail: config.message };
  if (config.action) return { label: 'Action', detail: config.action };
  return { label: 'No action', detail: 'Not configured' };
}

// Normalize imported command definitions so the app's own (flat) export round-
// trips losslessly while still accepting the nested `actions[]` shape.
//
// The flat export shape is the canonical CommandConfig ({action, keys, url, cmd,
// message}). A flat entry is passed through as-is. A nested entry (one carrying
// an `actions[]` array) is left structurally intact for backward compatibility —
// we only ensure flat entries stay flat so export → import is a no-op diff.
function normalizeImported(
  parsed: Record<string, Record<string, unknown>>,
): Record<string, CommandConfig> {
  const out: Record<string, CommandConfig> = {};
  for (const [name, def] of Object.entries(parsed)) {
    const d = def as Record<string, unknown>;
    const hasActions = Array.isArray(d.actions) && d.actions.length > 0;
    if (hasActions) {
      // Preserve the nested shape verbatim (backward compatibility).
      out[name] = def as CommandConfig;
      continue;
    }
    // Flat / legacy shape: keep only the recognized CommandConfig fields so the
    // result matches exactly what the exporter emits.
    const flat: CommandConfig = {};
    if (typeof d.action === 'string') flat.action = d.action;
    if (typeof d.keys === 'string') flat.keys = d.keys;
    // Legacy `keypress` alias maps onto the canonical `keys` field.
    else if (typeof d.keypress === 'string') flat.keys = d.keypress;
    if (typeof d.url === 'string') flat.url = d.url;
    if (typeof d.cmd === 'string') flat.cmd = d.cmd;
    if (typeof d.message === 'string') flat.message = d.message;
    out[name] = flat;
  }
  return out;
}

type SortKey = 'name' | 'type';
type SortDir = 'asc' | 'desc';

interface PendingImport {
  parsed: Record<string, CommandConfig>;
  added: string[];
  removed: string[];
  changed: string[];
}

export default function CommandsPage() {
  useEffect(() => {
    document.title = "Commands | ChattyCommander";
  }, []);

  const reduceMotion = useReducedMotionPref();
  const { addToast } = useToast();
  const [searchParams, setSearchParams] = useSearchParams();
  const searchQuery = searchParams.get('q') || '';
  // Sort key + direction are persisted in the URL alongside ?q= so they survive
  // back/forward navigation and refresh. ?sort=name|type, ?dir=asc|desc.
  const sortParam = searchParams.get('sort');
  const sortKey: SortKey = sortParam === 'type' ? 'type' : 'name';
  const sortDir: SortDir = searchParams.get('dir') === 'desc' ? 'desc' : 'asc';
  const [pendingDeleteCommand, setPendingDeleteCommand] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [pendingImport, setPendingImport] = useState<PendingImport | null>(null);
  const [isImporting, setIsImporting] = useState(false);
  // Bulk selection is keyed on command name so it survives sort/re-render.
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [isBulkDeleting, setIsBulkDeleting] = useState(false);
  const [restApiNoteDismissed, setRestApiNoteDismissed] = useState(readRestApiNoteDismissed);
  const deleteDialogRef = useRef<HTMLDialogElement>(null);
  const importDialogRef = useRef<HTMLDialogElement>(null);
  const bulkDeleteDialogRef = useRef<HTMLDialogElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const { data: commands, isLoading, isFetching, isError, error, refetch } = useQuery<Record<string, CommandConfig>>({
    queryKey: ['commands'],
    queryFn: () => apiService.getCommands(),
  });

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    // Preserve any active sort params while editing the search query.
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      if (value) {
        next.set('q', value);
      } else {
        next.delete('q');
      }
      return next;
    });
  };

  // Persist the sort key/direction in the URL (alongside ?q=). Selecting the
  // current key toggles direction; selecting a new key resets it to ascending.
  const applySort = (key: SortKey) => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      const nextDir: SortDir = key === sortKey && sortDir === 'asc' ? 'desc' : 'asc';
      next.set('sort', key);
      // 'name' + 'asc' is the default; omit params to keep the URL clean.
      if (key === 'name') {
        next.delete('sort');
      }
      if (nextDir === 'asc') {
        next.delete('dir');
      } else {
        next.set('dir', nextDir);
      }
      return next;
    });
  };

  // Clear the search query while preserving any active sort params (mirrors how
  // the sort handler preserves ?q=). Building from `prev` avoids wiping ?sort/?dir.
  const clearSearch = () => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.delete('q');
      return next;
    });
  };

  // Mirror for the <select> control: always sets the key, resetting direction.
  const handleSortSelect = (key: SortKey) => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set('sort', key);
      if (key === 'name') {
        next.delete('sort');
      }
      next.delete('dir');
      return next;
    });
  };

  // aria-sort value for a given column header.
  const ariaSortFor = (key: SortKey): 'ascending' | 'descending' | 'none' =>
    sortKey === key ? (sortDir === 'asc' ? 'ascending' : 'descending') : 'none';

  // Debounce the search query by 300ms so filtering is delayed while typing
  const [debouncedSearch, setDebouncedSearch] = useState(searchQuery);
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(searchQuery), 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Note: Ctrl/Cmd+K focus is owned by MainLayout's global handler (which targets
  // the search input via its stable `id="command-search"` / ref below). We do NOT
  // register a duplicate handler here — both would fire on /commands.

  const handleDeleteClick = (commandName: string) => {
    setPendingDeleteCommand(commandName);
    deleteDialogRef.current?.showModal();
  };

  const handleDeleteConfirm = async () => {
    if (!pendingDeleteCommand || isDeleting) return;
    setIsDeleting(true);
    try {
      await apiService.deleteCommand(pendingDeleteCommand);
      // Only refresh and close once the deletion actually succeeded, so the UI
      // never reports a deletion that didn't happen on the backend.
      refetch();
      // Drop the just-deleted command from any active selection so the bulk bar
      // doesn't linger (and a later bulk-delete can't 404 on a gone command).
      const deletedName = pendingDeleteCommand;
      setSelected((prev) => {
        if (!prev.has(deletedName)) return prev;
        const next = new Set(prev);
        next.delete(deletedName);
        return next;
      });
      deleteDialogRef.current?.close();
      setPendingDeleteCommand(null);
    } catch (err) {
      // Surface the failure via a toast (consistent with the rest of the app)
      // and keep the dialog open so the user can retry or cancel.
      addToast(`Failed to delete command: ${err instanceof Error ? err.message : String(err)}`, 'error');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleDeleteCancel = () => {
    deleteDialogRef.current?.close();
    setPendingDeleteCommand(null);
  };

  // Memoize the derived array to prevent expensive Object.entries() and array reallocation
  // on every render cycle, which improves performance on this page.
  const commandsList = useMemo(() => {
    return commands ? Object.entries(commands) : [];
  }, [commands]);

  // Memoize the empty check to avoid recalculating on each render
  const isEmpty = useMemo(() => !isLoading && commandsList.length === 0, [isLoading, commandsList.length]);

  const handleExportJson = () => {
    const blob = new Blob([JSON.stringify(commands, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'commands.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleImportJson = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const parsed = JSON.parse(event.target?.result as string);
        if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
          addToast('Invalid JSON: expected an object mapping command names to definitions.', 'error');
          return;
        }
        // Validate each command entry has a recognizable shape before importing,
        // so a malformed file can't silently overwrite the live config. We accept
        // the nested `actions[]`/legacy shape AND the flat `/api/v1/commands`
        // export shape (action/keys/url/cmd/message) so the app's own export can
        // be re-imported.
        const invalid = Object.entries(parsed as Record<string, unknown>).filter(([, def]) => {
          if (typeof def !== 'object' || def === null || Array.isArray(def)) return true;
          const d = def as Record<string, unknown>;
          const hasActions = Array.isArray(d.actions) && d.actions.length > 0;
          const hasLegacyAction = typeof d.action === 'string' || typeof d.keypress === 'string' || typeof d.url === 'string';
          // Flat export shape: any populated payload field is enough.
          const hasFlatPayload =
            typeof d.keys === 'string' ||
            typeof d.url === 'string' ||
            typeof d.cmd === 'string' ||
            typeof d.message === 'string';
          return !hasActions && !hasLegacyAction && !hasFlatPayload;
        });
        if (invalid.length > 0) {
          const names = invalid.map(([n]) => n).slice(0, 5).join(', ');
          addToast(`Import rejected: ${invalid.length} command(s) have no valid actions (${names}${invalid.length > 5 ? ', …' : ''}).`, 'error');
          return;
        }
        // Normalize each entry to the canonical flat shape so a flat ↔ flat
        // round-trip is lossless and a nested `actions[]` import still applies.
        // (The nested shape is passed through unchanged for backward compat.)
        const next = normalizeImported(parsed as Record<string, Record<string, unknown>>);
        const current = commands ?? {};
        const currentNames = Object.keys(current);
        const nextNames = Object.keys(next);
        const added = nextNames.filter((n) => !(n in current));
        const removed = currentNames.filter((n) => !(n in next));
        const changed = nextNames.filter(
          (n) => n in current && JSON.stringify(current[n]) !== JSON.stringify(next[n]),
        );
        setPendingImport({ parsed: next, added, removed, changed });
        importDialogRef.current?.showModal();
      } catch (err) {
        addToast(`Import failed: ${err instanceof Error ? err.message : String(err)}`, 'error');
      }
    };
    reader.readAsText(file);
    // Reset so the same file can be re-imported if needed
    e.target.value = '';
  };

  const handleImportConfirm = async () => {
    if (!pendingImport || isImporting) return;
    setIsImporting(true);
    try {
      await apiService.updateConfig({ commands: pendingImport.parsed });
      refetch();
      importDialogRef.current?.close();
      setPendingImport(null);
      addToast('Commands imported successfully.', 'success');
    } catch (err) {
      addToast(`Import failed: ${err instanceof Error ? err.message : String(err)}`, 'error');
    } finally {
      setIsImporting(false);
    }
  };

  const handleImportCancel = () => {
    importDialogRef.current?.close();
    setPendingImport(null);
  };

  // Clear the selection whenever the (debounced) search filter changes, so the
  // selection never includes commands that are no longer visible/relevant.
  useEffect(() => {
    setSelected(new Set());
  }, [debouncedSearch]);

  // Memoize filtered + sorted commands. Search now covers the visible detail
  // (url/keys/cmd/message) in addition to name + action.
  const filteredCommands = useMemo(() => {
    const query = debouncedSearch.trim().toLowerCase();
    const filtered = query
      ? commandsList.filter(([name, config]) => {
          const haystack = [
            name,
            config.action,
            config.url,
            config.keys,
            config.cmd,
            config.message,
          ]
            .filter(Boolean)
            .join(' ')
            .toLowerCase();
          return haystack.includes(query);
        })
      : commandsList.slice();
    filtered.sort(([aName, aCfg], [bName, bCfg]) => {
      let cmp = 0;
      if (sortKey === 'type') {
        cmp = getCommandType(aCfg).label.localeCompare(getCommandType(bCfg).label);
      }
      if (cmp === 0) {
        cmp = aName.localeCompare(bName);
      }
      return sortDir === 'desc' ? -cmp : cmp;
    });
    return filtered;
  }, [commandsList, debouncedSearch, sortKey, sortDir]);

  // Names currently visible (post-filter) — the universe "select all" operates on.
  const filteredNames = useMemo(
    () => filteredCommands.map(([name]) => name),
    [filteredCommands],
  );
  // How many of the visible commands are selected drives the header checkbox
  // (checked = all, indeterminate = some, unchecked = none).
  const selectedVisibleCount = useMemo(
    () => filteredNames.filter((name) => selected.has(name)).length,
    [filteredNames, selected],
  );
  const allVisibleSelected =
    filteredNames.length > 0 && selectedVisibleCount === filteredNames.length;
  const someVisibleSelected =
    selectedVisibleCount > 0 && selectedVisibleCount < filteredNames.length;

  // Reflect the indeterminate state on the header checkboxes (it can only be set
  // imperatively on the DOM node, not via a prop/attribute).
  const selectAllTableRef = useRef<HTMLInputElement>(null);
  const selectAllCardRef = useRef<HTMLInputElement>(null);
  useEffect(() => {
    if (selectAllTableRef.current) selectAllTableRef.current.indeterminate = someVisibleSelected;
    if (selectAllCardRef.current) selectAllCardRef.current.indeterminate = someVisibleSelected;
  }, [someVisibleSelected]);

  const toggleSelected = (name: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(name)) {
        next.delete(name);
      } else {
        next.add(name);
      }
      return next;
    });
  };

  // Select-all toggles only the currently-visible (filtered) commands.
  const toggleSelectAll = () => {
    setSelected((prev) => {
      if (filteredNames.every((name) => prev.has(name))) {
        // All visible are selected -> clear them (keep any non-visible, though
        // selection is cleared on search change so there generally are none).
        const next = new Set(prev);
        filteredNames.forEach((name) => next.delete(name));
        return next;
      }
      const next = new Set(prev);
      filteredNames.forEach((name) => next.add(name));
      return next;
    });
  };

  const handleBulkDeleteClick = () => {
    if (selected.size === 0) return;
    bulkDeleteDialogRef.current?.showModal();
  };

  const handleBulkDeleteCancel = () => {
    bulkDeleteDialogRef.current?.close();
  };

  const handleBulkDeleteConfirm = async () => {
    if (selected.size === 0 || isBulkDeleting) return;
    setIsBulkDeleting(true);
    try {
      // Delete each selected command via the existing per-command mechanism. We
      // use allSettled so a mid-list failure doesn't abort the rest — every
      // command is attempted and reported on honestly.
      const names = Array.from(selected);
      const results = await Promise.allSettled(
        names.map((name) => apiService.deleteCommand(name)),
      );
      const succeeded = names.filter((_, i) => results[i].status === 'fulfilled');
      const failedCount = names.length - succeeded.length;

      // Always refetch so the list reflects whatever actually got deleted, even
      // on partial failure.
      refetch();
      // Clear only the commands that were actually deleted from the selection,
      // leaving the failed ones selected so the user can retry them.
      const succeededSet = new Set(succeeded);
      setSelected((prev) => {
        const next = new Set(prev);
        succeededSet.forEach((name) => next.delete(name));
        return next;
      });

      if (failedCount === 0) {
        bulkDeleteDialogRef.current?.close();
        addToast(
          `Deleted ${succeeded.length} command${succeeded.length === 1 ? '' : 's'}.`,
          'success',
        );
      } else if (succeeded.length === 0) {
        addToast(`Failed to delete ${failedCount} command${failedCount === 1 ? '' : 's'}.`, 'error');
      } else {
        addToast(`Deleted ${succeeded.length}, ${failedCount} failed.`, 'error');
      }
    } finally {
      setIsBulkDeleting(false);
    }
  };

  // Export only the selected commands, reusing the same JSON export shape.
  const handleExportSelected = () => {
    if (selected.size === 0 || !commands) return;
    const subset: Record<string, CommandConfig> = {};
    for (const name of selected) {
      if (name in commands) subset[name] = commands[name];
    }
    const blob = new Blob([JSON.stringify(subset, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'commands.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    setSelected(new Set());
  };

  if (isLoading) {
    return (
      <div className="space-y-6 animate-pulse" aria-busy="true" aria-label="Loading commands">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <div className="h-10 w-64 skeleton mb-2 rounded-lg"></div>
            <div className="h-5 w-96 skeleton rounded"></div>
          </div>
          <div className="h-12 w-32 skeleton rounded-lg"></div>
        </div>

        <div className="divider divider-accent"></div>

        <div className="h-64 skeleton rounded-box"></div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="alert alert-error shadow-lg">
        <span>Failed to load commands: {(error as Error)?.message ?? 'Please check the backend connection.'}</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <motion.div
        initial={reduceMotion ? false : { opacity: 0, y: -20 }}
        animate={reduceMotion ? undefined : { opacity: 1, y: 0 }}
        className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4"
      >
        <div>
          <h1 className="text-3xl font-bold text-gradient-primary">Commands & Triggers</h1>
          <p className="text-base-content/60 mt-1">
            Manage system commands and configuration.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            className="btn btn-ghost btn-sm"
            onClick={() => refetch()}
            onKeyDown={(e) => e.key === 'Enter' && refetch()}
            title="Refresh Commands"
            aria-label="Refresh Commands"
            disabled={isFetching}
          >
            <RefreshCw size={20} className={isFetching ? "animate-spin" : ""} />
          </button>
          <button
            className="btn btn-outline btn-sm"
            onClick={handleExportJson}
            title="Export JSON"
            aria-label="Export commands as JSON"
            disabled={!commands || commandsList.length === 0}
          >
            <Download size={20} />
            Export JSON
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".json"
            className="hidden"
            onChange={handleImportJson}
          />
          <button
            className="btn btn-outline btn-sm"
            onClick={() => fileInputRef.current?.click()}
            title="Import JSON"
            aria-label="Import commands from JSON"
          >
            <Upload size={20} />
            Import JSON
          </button>
          <Link to="/commands/authoring" className="btn btn-primary btn-sm glass">
            <Plus size={20} />
            New Command
          </Link>
        </div>
      </motion.div>

      <div className="divider divider-accent"></div>

      {/* Page-level note: all commands are triggerable via the REST API. This
          replaces the identical per-row "REST API Trigger" block. Dismissible +
          persisted, since it's a learn-once hint, not standing UI. */}
      {!restApiNoteDismissed && (
        <div
          className="alert alert-info/60 bg-info/5 border border-info/30 text-sm"
          data-testid="rest-api-note"
        >
          <Globe className="text-info shrink-0" size={20} />
          <span className="flex-1">
            Every command can be triggered via the REST API:{' '}
            <code className="font-mono">POST /api/v1/command</code>.
          </span>
          <button
            type="button"
            className="btn btn-ghost btn-xs btn-square"
            onClick={() => {
              setRestApiNoteDismissed(true);
              persistRestApiNoteDismissed();
            }}
            aria-label="Dismiss REST API note"
          >
            <X size={16} />
          </button>
        </div>
      )}

      {/* Controls: search + sort */}
      <div className="flex flex-col md:flex-row md:items-center gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-base-content/40" size={16} />
          <input
            ref={searchInputRef}
            id="command-search"
            type="text"
            placeholder="Search commands..."
            aria-label="Search commands"
            className="input input-bordered input-sm w-full pl-10 pr-20"
            value={searchQuery}
            onChange={handleSearchChange}
          />
          <kbd className="kbd kbd-sm absolute right-10 top-1/2 -translate-y-1/2 text-base-content/40">
            Ctrl+K
          </kbd>
          {searchQuery && (
            <button
              className="absolute right-3 top-1/2 -translate-y-1/2 btn btn-ghost btn-xs btn-circle"
              onClick={clearSearch}
              aria-label="Clear search"
            >
              <X size={16} />
            </button>
          )}
        </div>
        <label className="flex items-center gap-2 text-sm">
          <ArrowUpDown size={16} className="text-base-content/50" />
          <span className="text-base-content/60">Sort</span>
          <select
            className="select select-bordered select-sm"
            aria-label="Sort commands"
            value={sortKey}
            onChange={(e) => handleSortSelect(e.target.value as SortKey)}
          >
            <option value="name">Name</option>
            <option value="type">Type</option>
          </select>
        </label>
        {searchQuery && (
          <span className="text-sm text-base-content/60" aria-live="polite">
            Showing {filteredCommands.length} of {commandsList.length} commands
          </span>
        )}
      </div>

      {/* Bulk action bar — appears once at least one command is selected. */}
      {selected.size > 0 && (
        <div
          role="region"
          aria-label="Bulk actions"
          className="sticky top-0 z-20 flex flex-col sm:flex-row sm:items-center gap-3 rounded-box border border-primary/30 bg-primary/5 p-3 backdrop-blur"
        >
          <span className="text-sm font-medium" aria-live="polite">
            {selected.size} selected
          </span>
          <div className="flex gap-2 sm:ml-auto">
            <button
              className="btn btn-outline btn-sm"
              onClick={handleExportSelected}
              aria-label="Export selected commands as JSON"
            >
              <Download size={16} />
              Export selected
            </button>
            <button
              className="btn btn-error btn-sm"
              onClick={handleBulkDeleteClick}
              aria-label="Delete selected commands"
            >
              <Trash2 size={16} />
              Delete selected
            </button>
          </div>
        </div>
      )}

      {/* Commands list */}
      {!isEmpty && filteredCommands.length > 0 && (
        <>
          {/* Mobile: stacked cards (the table's Actions column scrolls off-screen
              at ~375px, so below md we render an equivalent card per command). */}
          <div className="md:hidden space-y-3">
            <label className="flex items-center gap-2 text-sm px-1">
              <input
                ref={selectAllCardRef}
                type="checkbox"
                className="checkbox checkbox-sm"
                aria-label="Select all commands"
                checked={allVisibleSelected}
                onChange={toggleSelectAll}
              />
              <span className="text-base-content/60">Select all</span>
            </label>
            <ul className="space-y-3" aria-label="Commands">
              <AnimatePresence>
              {filteredCommands.map(([name, config], idx) => {
                const type = getCommandType(config);
                const { label, detail } = describeAction(config);
                const TypeIcon = type.Icon;
                return (
                  <motion.li
                    key={name}
                    data-reduced-motion={reduceMotion ? 'true' : 'false'}
                    initial={reduceMotion ? false : { opacity: 0, y: 8 }}
                    animate={reduceMotion ? undefined : { opacity: 1, y: 0 }}
                    transition={
                      reduceMotion
                        ? undefined
                        : { delay: Math.min(idx, MAX_STAGGER_INDEX) * STAGGER_STEP }
                    }
                    className="rounded-box border border-base-content/10 bg-base-100 p-4"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <span className="flex items-start gap-2 min-w-0">
                        <input
                          type="checkbox"
                          className="checkbox checkbox-sm mt-1 shrink-0"
                          aria-label={`Select ${name}`}
                          checked={selected.has(name)}
                          onChange={() => toggleSelected(name)}
                        />
                        <span className="font-semibold break-all" title={name}>{name}</span>
                      </span>
                      <span className={`badge ${type.badgeClass} gap-1 whitespace-nowrap shrink-0`}>
                        <TypeIcon size={16} />
                        {type.label}
                      </span>
                    </div>
                    <div className="mt-2">
                      <div className="text-xs uppercase tracking-wider text-base-content/50">{label}</div>
                      <div className="text-sm font-mono break-all">{detail}</div>
                    </div>
                    <div className="mt-3 flex items-center gap-2">
                      <Link
                        to={`/commands/authoring?edit=${encodeURIComponent(name)}`}
                        className="btn btn-ghost btn-sm flex-1 min-h-[40px] text-primary"
                        aria-label={`Edit ${name}`}
                        title="Edit"
                      >
                        <Edit3 size={16} />
                        Edit
                      </Link>
                      <button
                        className="btn btn-ghost btn-sm flex-1 min-h-[40px] text-error"
                        aria-label={`Delete ${name}`}
                        title="Delete"
                        onClick={() => handleDeleteClick(name)}
                      >
                        <Trash2 size={16} />
                        Delete
                      </button>
                      <Link
                        to={`/voice-test?command=${encodeURIComponent(name)}`}
                        className="btn btn-ghost btn-sm flex-1 min-h-[40px] text-success"
                        aria-label={`Test ${name}`}
                        title="Test this command"
                      >
                        <PlayCircle size={16} />
                        Test
                      </Link>
                    </div>
                  </motion.li>
                );
              })}
              </AnimatePresence>
            </ul>
          </div>

          {/* Desktop (md+): full table */}
          <div className="hidden md:block overflow-x-auto rounded-box border border-base-content/10">
            <table className="table table-zebra">
              <caption className="sr-only">
                Configured commands, sortable by name or type. {filteredCommands.length} of {commandsList.length} shown.
              </caption>
              <thead>
                <tr>
                  <th className="w-0">
                    <input
                      ref={selectAllTableRef}
                      type="checkbox"
                      className="checkbox checkbox-sm"
                      aria-label="Select all commands"
                      checked={allVisibleSelected}
                      onChange={toggleSelectAll}
                    />
                  </th>
                  <th aria-sort={ariaSortFor('name')}>
                    <button
                      type="button"
                      className="inline-flex items-center gap-1 hover:text-primary"
                      onClick={() => applySort('name')}
                    >
                      Name
                      <ArrowUpDown size={16} className="opacity-50" aria-hidden="true" />
                    </button>
                  </th>
                  <th aria-sort={ariaSortFor('type')}>
                    <button
                      type="button"
                      className="inline-flex items-center gap-1 hover:text-primary"
                      onClick={() => applySort('type')}
                    >
                      Type
                      <ArrowUpDown size={16} className="opacity-50" aria-hidden="true" />
                    </button>
                  </th>
                  <th>Action</th>
                  <th className="text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                <AnimatePresence>
                  {filteredCommands.map(([name, config], idx) => {
                    const type = getCommandType(config);
                    const { label, detail } = describeAction(config);
                    const TypeIcon = type.Icon;
                    return (
                      <motion.tr
                        key={name}
                        data-reduced-motion={reduceMotion ? 'true' : 'false'}
                        initial={reduceMotion ? false : { opacity: 0, y: 8 }}
                        animate={reduceMotion ? undefined : { opacity: 1, y: 0 }}
                        transition={
                          reduceMotion
                            ? undefined
                            : { delay: Math.min(idx, MAX_STAGGER_INDEX) * STAGGER_STEP }
                        }
                        className="hover"
                      >
                        <td className="align-top">
                          <input
                            type="checkbox"
                            className="checkbox checkbox-sm"
                            aria-label={`Select ${name}`}
                            checked={selected.has(name)}
                            onChange={() => toggleSelected(name)}
                          />
                        </td>
                        <td className="font-semibold align-top max-w-[16rem]">
                          <span className="truncate block" title={name}>{name}</span>
                        </td>
                        <td className="align-top">
                          <span className={`badge ${type.badgeClass} gap-1 whitespace-nowrap`}>
                            <TypeIcon size={16} />
                            {type.label}
                          </span>
                        </td>
                        <td className="align-top">
                          <div className="text-xs uppercase tracking-wider text-base-content/50">{label}</div>
                          <div className="text-sm font-mono break-all max-w-md">{detail}</div>
                        </td>
                        <td className="align-top">
                          <div className="flex items-center justify-end gap-1">
                            <Link
                              to={`/commands/authoring?edit=${encodeURIComponent(name)}`}
                              className="btn btn-ghost btn-xs btn-circle text-primary"
                              aria-label={`Edit ${name}`}
                              title="Edit"
                            >
                              <Edit3 size={16} />
                            </Link>
                            <button
                              className="btn btn-ghost btn-xs btn-circle text-error"
                              aria-label={`Delete ${name}`}
                              title="Delete"
                              onClick={() => handleDeleteClick(name)}
                            >
                              <Trash2 size={16} />
                            </button>
                            <DynamicDropdown
                              buttonContent={
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.75a.75.75 0 110-1.5.75.75 0 010 1.5zM12 12.75a.75.75 0 110-1.5.75.75 0 010 1.5zM12 18.75a.75.75 0 110-1.5.75.75 0 010 1.5z" />
                                </svg>
                              }
                              menuClassName="dropdown-content z-50 menu p-2 shadow bg-base-100 rounded-box w-52 border border-base-content/10"
                              ariaLabel={`More options for ${name}`}
                            >
                              <li>
                                <Link to={`/voice-test?command=${encodeURIComponent(name)}`} aria-label={`Test ${name}`}>
                                  <PlayCircle size={16} className="text-success" />
                                  Test this command
                                </Link>
                              </li>
                            </DynamicDropdown>
                          </div>
                        </td>
                      </motion.tr>
                    );
                  })}
                </AnimatePresence>
              </tbody>
            </table>
          </div>
        </>
      )}

      {isEmpty && (
        <div className="flex flex-col items-center justify-center p-12 bg-base-200/50 rounded-box border border-base-content/10">
          <TerminalSquare size={48} className="text-base-content/20 mb-4" />
          <h3 className="text-lg font-semibold text-base-content/70">No commands configured.</h3>
          <p className="text-base-content/50 mt-2 mb-6 max-w-md text-center">
            Get started by creating your first command to automate tasks and streamline your workflow.
          </p>
          <Link to="/commands/authoring" className="btn btn-primary">
            <Plus size={20} />
            Create Command
          </Link>
        </div>
      )}
      {searchQuery && filteredCommands.length === 0 && !isEmpty && (
        <div className="flex flex-col items-center justify-center p-12 bg-base-200/50 rounded-box border border-base-content/10">
          <Search size={48} className="text-base-content/20 mb-4" />
          <h3 className="text-lg font-semibold text-base-content/70">No commands match your search.</h3>
          <p className="text-base-content/50 mt-2 mb-6 max-w-md text-center">
            Try adjusting your search terms or clearing the search filter to see all commands.
          </p>
          <button className="btn btn-outline" onClick={clearSearch}>
            Clear Search
          </button>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      <dialog ref={deleteDialogRef} className="modal">
        <div className="modal-box">
          <h3 className="font-bold text-lg">Confirm Deletion</h3>
          <p className="py-4">Are you sure you want to delete <strong>{pendingDeleteCommand}</strong>?</p>
          <div className="modal-action">
            <button className="btn" onClick={handleDeleteCancel} disabled={isDeleting}>Cancel</button>
            <button className="btn btn-error" onClick={handleDeleteConfirm} disabled={isDeleting}>
              {isDeleting ? <span className="loading loading-spinner loading-sm" aria-hidden="true"></span> : null}
              Delete
            </button>
          </div>
        </div>
        <form method="dialog" className="modal-backdrop">
          <button aria-label="Close dialog" onClick={handleDeleteCancel}>close</button>
        </form>
      </dialog>

      {/* Bulk Delete Confirmation Modal */}
      <dialog ref={bulkDeleteDialogRef} className="modal">
        <div className="modal-box">
          <h3 className="font-bold text-lg">Confirm Deletion</h3>
          <p className="py-4">
            Are you sure you want to delete <strong>{selected.size}</strong>{' '}
            selected command{selected.size === 1 ? '' : 's'}? This cannot be undone.
          </p>
          <div className="modal-action">
            <button className="btn" onClick={handleBulkDeleteCancel} disabled={isBulkDeleting}>Cancel</button>
            <button className="btn btn-error" onClick={handleBulkDeleteConfirm} disabled={isBulkDeleting}>
              {isBulkDeleting ? <span className="loading loading-spinner loading-sm" aria-hidden="true"></span> : null}
              Delete {selected.size}
            </button>
          </div>
        </div>
        <form method="dialog" className="modal-backdrop">
          <button aria-label="Close dialog" onClick={handleBulkDeleteCancel}>close</button>
        </form>
      </dialog>

      {/* Import Confirmation Modal — shows the diff before replacing the set */}
      <dialog ref={importDialogRef} className="modal">
        <div className="modal-box">
          <h3 className="font-bold text-lg">Confirm Import</h3>
          <p className="py-2 text-sm text-base-content/70">
            Importing replaces your entire command set. Review the changes below.
          </p>
          {pendingImport && (
            <div className="flex flex-wrap gap-2 py-2">
              <span className="badge badge-success gap-1">+{pendingImport.added.length} added</span>
              <span className="badge badge-error gap-1">-{pendingImport.removed.length} removed</span>
              <span className="badge badge-warning gap-1">~{pendingImport.changed.length} changed</span>
            </div>
          )}
          <div className="modal-action">
            <button className="btn" onClick={handleImportCancel} disabled={isImporting}>Cancel</button>
            <button className="btn btn-primary" onClick={handleImportConfirm} disabled={isImporting}>
              {isImporting ? <span className="loading loading-spinner loading-sm" aria-hidden="true"></span> : null}
              Apply Import
            </button>
          </div>
        </div>
        <form method="dialog" className="modal-backdrop">
          <button aria-label="Close dialog" onClick={handleImportCancel}>close</button>
        </form>
      </dialog>
    </div>
  );
}
