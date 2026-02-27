import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  TerminalSquare,
  Settings2,
  Volume2,
  Globe,
  Plus,
  Edit3,
  Trash2,
  AlertTriangle
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiService } from '../services/apiService';

interface CommandInfo {
  name: string;
  action_type: string;
  details: Record<string, any>;
}

export default function CommandsPage() {
  const [activeTab, setActiveTab] = useState('all');

  const { data: commands, isLoading, isError, error } = useQuery<CommandInfo[]>({
    queryKey: ['commands'],
    queryFn: () => apiService.getCommands(),
  });

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-full p-20">
        <span className="loading loading-spinner loading-lg text-primary"></span>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="alert alert-error shadow-lg max-w-2xl mx-auto mt-10">
        <AlertTriangle />
        <span>Error loading commands: {(error as Error).message}</span>
      </div>
    );
  }

  const commandList = commands || [];

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
            Manage system commands and configure the Wakewords or API endpoints that trigger them.
          </p>
        </div>
        <button className="btn btn-primary glass">
          <Plus size={18} />
          New Command
        </button>
      </motion.div>

      <div className="divider divider-accent"></div>

      {/* Commands Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <AnimatePresence>
          {commandList.map((command, idx) => (
            <motion.div
              key={command.name}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: idx * 0.1 }}
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
                      <h2 className="card-title text-xl mb-1">{command.name}</h2>
                      <div className="flex gap-2 text-xs font-mono text-base-content/60">
                        <span className="px-2 py-1 rounded bg-base-300">{command.action_type}</span>
                        <span className="px-2 py-1 rounded bg-base-300 truncate max-w-[250px]">
                           {JSON.stringify(command.details).slice(0, 40)}
                           {JSON.stringify(command.details).length > 40 ? '...' : ''}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-1">
                    <div className="tooltip tooltip-bottom" data-tip="Edit Command">
                      <button
                        className="btn btn-ghost btn-sm btn-circle"
                        aria-label={`Edit ${command.name}`}
                      >
                        <Edit3 size={16} />
                      </button>
                    </div>
                    <div className="tooltip tooltip-bottom tooltip-error" data-tip="Delete Command">
                      <button
                        className="btn btn-ghost btn-sm btn-circle text-error"
                        aria-label={`Delete ${command.name}`}
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
                      <p className="font-medium text-sm">REST API / WebUI Trigger</p>
                      <p className="text-xs text-base-content/60 font-mono mt-0.5">
                        POST /api/v1/command
                      </p>
                    </div>
                    <div className="badge badge-success badge-sm badge-outline">Enabled</div>
                  </div>

                  {/* Wakewords 1-to-Many UI Placeholder */}
                  <div className="space-y-3 mt-4">
                    <div className="relative pl-6">
                      <div className="absolute left-[11px] top-0 bottom-[-16px] w-[2px] bg-base-content/10 last:bottom-auto last:h-8"></div>
                      <div className="absolute left-[11px] top-8 w-4 h-[2px] bg-base-content/10"></div>

                      <div className="flex items-start gap-3 p-4 rounded-xl border border-base-content/10 bg-base-100/50 hover:bg-base-200/50 transition-colors ml-2">
                        <Volume2 className="text-base-content/30" size={20} />
                        <div className="flex-1">
                          <div className="flex justify-between items-center mb-2">
                            <p className="font-semibold text-base-content/60 italic">
                              Wakeword mapping managed via global config
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        {commandList.length === 0 && (
          <div className="col-span-full text-center p-10 text-base-content/50 italic">
            No commands found. Create one to get started.
          </div>
        )}
      </div>
    </div>
  );
};
