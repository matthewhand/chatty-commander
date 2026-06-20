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
  ArrowUpDown
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

type SortKey = 'name' | 'type';

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
  const [sortKey, setSortKey] = useState<SortKey>('name');
  const [pendingDeleteCommand, setPendingDeleteCommand] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [pendingImport, setPendingImport] = useState<PendingImport | null>(null);
  const [isImporting, setIsImporting] = useState(false);
  const deleteDialogRef = useRef<HTMLDialogElement>(null);
  const importDialogRef = useRef<HTMLDialogElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const { data: commands, isLoading, isError, error, refetch } = useQuery<Record<string, CommandConfig>>({
    queryKey: ['commands'],
    queryFn: () => apiService.getCommands(),
  });

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    if (value) {
      setSearchParams({ q: value });
    } else {
      setSearchParams({});
    }
  };

  // Debounce the search query by 300ms so filtering is delayed while typing
  const [debouncedSearch, setDebouncedSearch] = useState(searchQuery);
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(searchQuery), 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Wire Ctrl/Cmd+K to focus the search input (the kbd hint previously did
  // nothing). We avoid a focus-stealing autoFocus on mount in favour of this.
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        searchInputRef.current?.focus();
        searchInputRef.current?.select();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

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
        // so a malformed file can't silently overwrite the live config.
        const invalid = Object.entries(parsed as Record<string, unknown>).filter(([, def]) => {
          if (typeof def !== 'object' || def === null || Array.isArray(def)) return true;
          const d = def as Record<string, unknown>;
          const hasActions = Array.isArray(d.actions) && d.actions.length > 0;
          const hasLegacyAction = typeof d.action === 'string' || typeof d.keypress === 'string' || typeof d.url === 'string';
          return !hasActions && !hasLegacyAction;
        });
        if (invalid.length > 0) {
          const names = invalid.map(([n]) => n).slice(0, 5).join(', ');
          addToast(`Import rejected: ${invalid.length} command(s) have no valid actions (${names}${invalid.length > 5 ? ', …' : ''}).`, 'error');
          return;
        }
        // Compute a diff against the current command set so the user can review
        // added/removed/changed counts before this replaces the whole config.
        const next = parsed as Record<string, CommandConfig>;
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
      if (sortKey === 'type') {
        const typeCmp = getCommandType(aCfg).label.localeCompare(getCommandType(bCfg).label);
        if (typeCmp !== 0) return typeCmp;
      }
      return aName.localeCompare(bName);
    });
    return filtered;
  }, [commandsList, debouncedSearch, sortKey]);

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
        <div className="flex gap-2">
          <button
            className="btn btn-ghost btn-sm"
            onClick={() => refetch()}
            onKeyDown={(e) => e.key === 'Enter' && refetch()}
            title="Refresh Commands"
            aria-label="Refresh Commands"
          >
            <RefreshCw size={18} className={isLoading ? "animate-spin" : ""} />
          </button>
          <button
            className="btn btn-outline btn-sm"
            onClick={handleExportJson}
            title="Export JSON"
            aria-label="Export commands as JSON"
            disabled={!commands || commandsList.length === 0}
          >
            <Download size={16} />
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
            <Upload size={16} />
            Import JSON
          </button>
          <Link to="/commands/authoring" className="btn btn-primary btn-sm glass">
            <Plus size={18} />
            New Command
          </Link>
        </div>
      </motion.div>

      <div className="divider divider-accent"></div>

      {/* Page-level note: all commands are triggerable via the REST API. This
          replaces the identical per-row "REST API Trigger" block. */}
      <div className="alert alert-info/60 bg-info/5 border border-info/30 text-sm">
        <Globe className="text-info shrink-0" size={18} />
        <span>
          Every command can be triggered via the REST API:{' '}
          <code className="font-mono">POST /api/v1/command</code>.
        </span>
      </div>

      {/* Controls: search + sort */}
      <div className="flex flex-col md:flex-row md:items-center gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-base-content/40" size={18} />
          <input
            ref={searchInputRef}
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
              onClick={() => setSearchParams({})}
              aria-label="Clear search"
            >
              ×
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
            onChange={(e) => setSortKey(e.target.value as SortKey)}
          >
            <option value="name">Name</option>
            <option value="type">Type</option>
          </select>
        </label>
        {searchQuery && (
          <span className="text-sm text-base-content/60">
            Showing {filteredCommands.length} of {commandsList.length} commands
          </span>
        )}
      </div>

      {/* Commands Table */}
      {!isEmpty && filteredCommands.length > 0 && (
        <div className="overflow-x-auto rounded-box border border-base-content/10">
          <table className="table table-zebra">
            <thead>
              <tr>
                <th>Name</th>
                <th>Type</th>
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
                      <td className="font-semibold align-top max-w-[16rem]">
                        <span className="truncate block" title={name}>{name}</span>
                      </td>
                      <td className="align-top">
                        <span className={`badge ${type.badgeClass} gap-1 whitespace-nowrap`}>
                          <TypeIcon size={14} />
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
      )}

      {isEmpty && (
        <div className="flex flex-col items-center justify-center p-12 bg-base-200/50 rounded-box border border-base-content/10">
          <TerminalSquare size={48} className="text-base-content/20 mb-4" />
          <h3 className="text-lg font-semibold text-base-content/70">No commands configured.</h3>
          <p className="text-base-content/50 mt-2 mb-6 max-w-md text-center">
            Get started by creating your first command to automate tasks and streamline your workflow.
          </p>
          <Link to="/commands/authoring" className="btn btn-primary">
            <Plus size={18} />
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
          <button className="btn btn-outline" onClick={() => setSearchParams({})}>
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
          <button onClick={handleDeleteCancel}>close</button>
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
          <button onClick={handleImportCancel}>close</button>
        </form>
      </dialog>
    </div>
  );
}
