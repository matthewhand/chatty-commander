import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  TerminalSquare,
  Settings2,
  Globe,
  Plus,
  Edit3,
  Trash2,
  RefreshCw
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiService } from '../services/apiService';

// Backend response is a Record<string, CommandConfig>
interface CommandConfig {
  action: string; // 'keypress' | 'url' | 'shell' | 'custom_message' | 'voice_chat'
  keys?: string;
  url?: string;
  cmd?: string;
  message?: string;
}

export default function CommandsPage() {
  const { data: commands, isLoading, isError, error, refetch } = useQuery<Record<string, CommandConfig>>({
    queryKey: ['commands'],
    queryFn: () => apiService.getCommands(),
  });

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
           <button className="btn btn-ghost" onClick={() => refetch()} title="Refresh Commands">
             <RefreshCw size={18} className={isLoading ? "animate-spin" : ""} />
           </button>
           <button className="btn btn-primary glass">
            <Plus size={18} />
            New Command
          </button>
        </div>
      </motion.div>

      <div className="divider divider-accent"></div>

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
          {commands && Object.entries(commands).map(([name, config], idx) => (
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
                    <div className="tooltip tooltip-bottom" data-tip="Edit Command">
                      <button
                        className="btn btn-ghost btn-sm btn-circle"
                        aria-label={`Edit ${name}`}
                      >
                        <Edit3 size={16} />
                      </button>
                    </div>
                    <div className="tooltip tooltip-bottom tooltip-error" data-tip="Delete Command">
                      <button
                        className="btn btn-ghost btn-sm btn-circle text-error"
                        aria-label={`Delete ${name}`}
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                </div>

                {/* Triggers Section */}
                <div className="p-6 space-y-4">
                  <h3 className="text-sm font-semibold uppercase tracking-wider text-base-content/50 flex flex-items-center gap-2">
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
        {!isLoading && commands && Object.keys(commands).length === 0 && (
            <div className="col-span-full text-center p-12 opacity-50 italic">
                No commands configured.
            </div>
        )}
      </div>
    </div>
  );
};
