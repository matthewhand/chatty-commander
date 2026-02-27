import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  TerminalSquare,
  Settings2,
  Globe,
  Plus,
  Edit3,
  Trash2,
  Code
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { fetchConfig, AppConfig, CommandAction } from '../services/api';

// Helper to format payload display
const getPayloadDisplay = (cmd: CommandAction) => {
  if (cmd.action === 'keypress') return `Keys: ${cmd.keys}`;
  if (cmd.action === 'url') return `URL: ${cmd.url}`;
  if (cmd.action === 'shell') return `Shell: ${cmd.cmd}`;
  if (cmd.action === 'custom_message') return `Msg: ${cmd.message}`;
  if (cmd.action === 'voice_chat') return 'Interactive Voice Chat';
  return 'Unknown Payload';
};

export default function CommandsPage() {
  const { data: config, isLoading, isError } = useQuery<AppConfig>({
    queryKey: ['config'],
    queryFn: fetchConfig,
  });

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-full">
        <span className="loading loading-spinner loading-lg text-primary"></span>
      </div>
    );
  }

  if (isError || !config) {
    return (
      <div className="alert alert-error shadow-lg">
        <span>Failed to load commands configuration.</span>
      </div>
    );
  }

  const commands = Object.entries(config.commands || {});

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
            Manage system commands and configure API endpoints that trigger them.
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
          {commands.length === 0 ? (
            <div className="col-span-full text-center p-10 text-base-content/50 italic">
              No commands configured.
            </div>
          ) : (
            commands.map(([cmdName, cmdData], idx) => (
              <motion.div
                key={cmdName}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: idx * 0.1 }}
                className="card glass-card overflow-hidden"
              >
                {/* Visual indicator for enabled API/WebUI access (implied enabled for all config commands) */}
                <div className="border-gradient"></div>

                <div className="card-body p-0">
                  {/* Command Header */}
                  <div className="p-6 bg-base-200/50 border-b border-base-content/10 flex justify-between items-start">
                    <div className="flex gap-3">
                      <div className="p-3 rounded-xl bg-primary/20 text-primary">
                        <TerminalSquare size={24} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h2 className="card-title text-xl mb-1 truncate" title={cmdName}>
                          {cmdName}
                        </h2>
                        <div className="flex flex-wrap gap-2 text-xs font-mono text-base-content/60">
                          <span className="px-2 py-1 rounded bg-base-300 border border-base-content/5">
                            {cmdData.action}
                          </span>
                          <span className="px-2 py-1 rounded bg-base-300 border border-base-content/5 truncate max-w-[200px]" title={getPayloadDisplay(cmdData)}>
                            {getPayloadDisplay(cmdData)}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex gap-1 shrink-0">
                      <div className="tooltip tooltip-bottom" data-tip="Edit Command">
                        <button
                          className="btn btn-ghost btn-sm btn-circle"
                          aria-label={`Edit ${cmdName}`}
                        >
                          <Edit3 size={16} />
                        </button>
                      </div>
                      <div className="tooltip tooltip-bottom tooltip-error" data-tip="Delete Command">
                        <button
                          className="btn btn-ghost btn-sm btn-circle text-error"
                          aria-label={`Delete ${cmdName}`}
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
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
                        <p className="font-medium text-sm">REST API / WebUI Trigger</p>
                        <p className="text-xs text-base-content/60 font-mono mt-0.5 break-all">
                          POST /api/v1/command
                        </p>
                      </div>
                      <div className="badge badge-success badge-sm badge-outline">Enabled</div>
                    </div>

                    {/* JSON Preview (Technical Detail) */}
                    <div className="collapse collapse-arrow border border-base-content/10 bg-base-100/50 rounded-lg">
                      <input type="checkbox" />
                      <div className="collapse-title text-sm font-medium flex items-center gap-2 text-base-content/70">
                        <Code size={14} /> View Configuration JSON
                      </div>
                      <div className="collapse-content">
                        <pre className="text-[10px] leading-tight font-mono bg-base-300 p-2 rounded overflow-x-auto">
                          {JSON.stringify(cmdData, null, 2)}
                        </pre>
                      </div>
                    </div>

                  </div>
                </div>
              </motion.div>
            ))
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};
