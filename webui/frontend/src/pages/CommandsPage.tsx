import React, { useEffect, useMemo, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link, useSearchParams } from 'react-router-dom';
import {
  TerminalSquare,
  Settings2,
  Globe,
  Plus,
  Edit3,
  Trash2,
  FileAudio,
  RefreshCw,
  Search,
  Download,
  Upload
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiService } from '../services/apiService';
import { DynamicDropdown } from '../components/DynamicDropdown';

// Backend response is a Record<string, CommandConfig>
interface CommandConfig {
  action: string; // 'keypress' | 'url' | 'shell' | 'custom_message' | 'voice_chat'
  keys?: string;
  url?: string;
  cmd?: string;
  message?: string;
}

export default function CommandsPage() {
  useEffect(() => {
    document.title = "Commands | ChattyCommander";
  }, []);

  const [searchParams, setSearchParams] = useSearchParams();
  const searchQuery = searchParams.get('q') || '';
  const [pendingDeleteCommand, setPendingDeleteCommand] = useState<string | null>(null);
  const deleteDialogRef = useRef<HTMLDialogElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
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

  const handleDeleteClick = (commandName: string) => {
    setPendingDeleteCommand(commandName);
    deleteDialogRef.current?.showModal();
  };

  const handleDeleteConfirm = async () => {
    if (pendingDeleteCommand) {
      await apiService.deleteCommand(pendingDeleteCommand);
      refetch();
    }
    deleteDialogRef.current?.close();
    setPendingDeleteCommand(null);
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
    reader.onload = async (event) => {
      try {
        const parsed = JSON.parse(event.target?.result as string);
        if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
          alert('Invalid JSON: expected an object.');
          return;
        }
        await apiService.updateConfig({ commands: parsed });
        refetch();
      } catch (err) {
        alert(`Import failed: ${err instanceof Error ? err.message : String(err)}`);
      }
    };
    reader.readAsText(file);
    // Reset so the same file can be re-imported if needed
    e.target.value = '';
  };

  // Memoize filtered commands for search functionality (uses debounced value)
  const filteredCommands = useMemo(() => {
    if (!debouncedSearch.trim()) return commandsList;
    const query = debouncedSearch.toLowerCase();
    return commandsList.filter(([name, config]) =>
      name.toLowerCase().includes(query) ||
      (config.action && config.action.toLowerCase().includes(query))
    );
  }, [commandsList, debouncedSearch]);
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

        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="card glass-card overflow-hidden h-64 skeleton rounded-box"></div>
          ))}
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="alert alert-error shadow-lg">
        <span>Failed to load commands. Please check the backend connection.</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
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
            className="btn btn-ghost"
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
          <Link to="/commands/authoring" className="btn btn-primary glass">
            <Plus size={18} />
            New Command
          </Link>
        </div>
      </motion.div>

      <div className="divider divider-accent"></div>

      {/* Search Filter */}
      <div className="flex items-center gap-2">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-base-content/40" size={18} />
          <input
            type="text"
            placeholder="Search commands..."
            aria-label="Search commands"
            className="input input-bordered w-full pl-10 pr-20"
            value={searchQuery}
            onChange={handleSearchChange}
            autoFocus
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
        {searchQuery && (
          <span className="text-sm text-base-content/60">
            Showing {filteredCommands.length} of {commandsList.length} commands
          </span>
        )}
      </div>

      {/* Loading / Error States */}
      {isLoading && (
        <div className="flex justify-center p-12">
          <span className="loading loading-spinner loading-lg text-primary"></span>
        </div>
      )}

      {isError && (
        <div className="alert alert-error shadow-lg">
          <span>Failed to load commands: {(error as Error).message}</span>
        </div>
      )}

      {/* Commands Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <AnimatePresence>
          {filteredCommands.map(([name, config], idx) => (
            <motion.div
              key={name}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: idx * 0.05 }}
              className="card glass-card overflow-hidden"
            >
              <div className="border-gradient"></div>
              <div className="card-body p-0">
                {/* Command Header */}
                <div className="p-6 bg-base-200/50 border-b border-base-content/10 flex justify-between items-start">
                  <div className="flex gap-1">
                    <DynamicDropdown
                      buttonContent={
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.75a.75.75 0 110-1.5.75.75 0 010 1.5zM12 12.75a.75.75 0 110-1.5.75.75 0 010 1.5zM12 18.75a.75.75 0 110-1.5.75.75 0 010 1.5z" />
                        </svg>
                      }
                      menuClassName="dropdown-content z-50 menu p-2 shadow bg-base-100 rounded-box w-52 border border-base-content/10"
                      ariaLabel={`Options for ${name}`}
                    >
                      <li>
                        <button aria-label={`Edit ${name}`}>
                          <Edit3 size={16} className="text-primary" />
                          Edit Command
                        </button>
                      </li>
                      <li>
                        <button className="text-error hover:bg-error/10 hover:text-error" aria-label={`Delete ${name}`} onClick={() => handleDeleteClick(name)}>
                          <Trash2 size={16} />
                          Delete Command
                        </button>
                      </li>
                    </DynamicDropdown>
                  </div>
                </div>

                {/* Triggers Section */}
                <div className="p-6 space-y-4">
                  <h3 className="text-sm font-semibold uppercase tracking-wider text-base-content/50 flex items-center gap-2">
                    <Settings2 size={14} /> Activation Triggers
                  </h3>

                  {/* REST API Badge */}
                  <div className="flex items-center gap-3 p-3 rounded-lg border border-success/30 bg-success/5">
                    <Globe className="text-success" size={20} />
                    <div className="flex-1">
                      <p className="font-medium text-sm">REST API Trigger</p>
                      <p className="text-xs text-base-content/60 font-mono mt-0.5">POST /api/v1/command</p>
                    </div>
                    <div className="badge badge-success badge-sm badge-outline">Enabled</div>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        {isEmpty && (
          <div className="col-span-full flex flex-col items-center justify-center p-12 bg-base-200/50 rounded-box border border-base-content/10">
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
          <div className="col-span-full flex flex-col items-center justify-center p-12 bg-base-200/50 rounded-box border border-base-content/10">
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
      </div>

      {/* Delete Confirmation Modal */}
      <dialog ref={deleteDialogRef} className="modal">
        <div className="modal-box">
          <h3 className="font-bold text-lg">Confirm Deletion</h3>
          <p className="py-4">Are you sure you want to delete <strong>{pendingDeleteCommand}</strong>?</p>
          <div className="modal-action">
            <button className="btn" onClick={handleDeleteCancel}>Cancel</button>
            <button className="btn btn-error" onClick={handleDeleteConfirm}>Delete</button>
          </div>
        </div>
        <form method="dialog" className="modal-backdrop">
          <button onClick={handleDeleteCancel} aria-label="Close delete confirmation dialog">close</button>
        </form>
      </dialog>
    </div>
  );
};
