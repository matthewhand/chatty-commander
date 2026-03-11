import React, { useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSearchParams } from 'react-router-dom';
import {
  TerminalSquare,
  Settings2,
  Globe,
  Plus,
  Edit3,
  Trash2,
  FileAudio,
  RefreshCw,
  Search
} from 'lucide-react';
import { Link } from 'react-router-dom';
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
  const [searchParams, setSearchParams] = useSearchParams();
  const searchQuery = searchParams.get('q') || '';
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

  // Memoize the derived array to prevent expensive Object.entries() and array reallocation
  // on every render cycle, which improves performance on this page.
  const commandsList = useMemo(() => {
    return commands ? Object.entries(commands) : [];
  }, [commands]);

  // Memoize the empty check to avoid recalculating on each render
  const isEmpty = useMemo(() => !isLoading && commandsList.length === 0, [isLoading, commandsList.length]);

  // Memoize filtered commands for search functionality
  const filteredCommands = useMemo(() => {
    if (!searchQuery.trim()) return commandsList;
    const query = searchQuery.toLowerCase();
    return commandsList.filter(([name, config]) =>
      name.toLowerCase().includes(query) ||
      (config.action && config.action.toLowerCase().includes(query))
    );
  }, [commandsList, searchQuery]);
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
            className="input input-bordered w-full pl-10"
            value={searchQuery}
            onChange={handleSearchChange}
          />
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
                  <div className="flex gap-3">
                    <div className="p-3 rounded-xl bg-primary/20 text-primary">
                      <TerminalSquare size={24} />
                    </div>
                    <div>
                      <h2 className="card-title text-xl mb-1">{name}</h2>
                      <div className="flex gap-2 text-xs font-mono text-base-content/60">
                        <span className="px-2 py-1 rounded bg-base-300">{config.action}</span>
                        <span className="px-2 py-1 rounded bg-base-300 truncate max-w-[200px]" title={
                          config.keys || config.url || config.cmd || config.message || ""
                        }>
                          {config.keys || config.url || config.cmd || config.message || "-"}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-1">
                    <DynamicDropdown
                      ariaLabel={`Command options for ${name}`}
                      buttonContent={
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.75a.75.75 0 110-1.5.75.75 0 010 1.5zM12 12.75a.75.75 0 110-1.5.75.75 0 010 1.5zM12 18.75a.75.75 0 110-1.5.75.75 0 010 1.5z" />
                        </svg>
                      }
                      menuClassName="dropdown-content z-50 menu p-2 shadow bg-base-100 rounded-box w-52 border border-base-content/10"
                    >
                      <li>
                        <button aria-label={`Edit ${name}`}>
                          <Edit3 size={16} className="text-primary" />
                          Edit Command
                        </button>
                      </li>
                      <li>
                        <button className="text-error hover:bg-error/10 hover:text-error" aria-label={`Delete ${name}`}>
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
          <div className="col-span-full text-center p-12 opacity-50 italic">
            No commands configured.
          </div>
        )}
        {searchQuery && filteredCommands.length === 0 && !isEmpty && (
          <div className="col-span-full text-center p-12 opacity-50 italic">
            No commands match your search.
          </div>
        )}
      </div>
    </div>
  );
};
