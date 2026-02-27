import React, { useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  TerminalSquare,
  Settings2,
  Volume2,
  Globe,
  Plus,
  Edit3,
  Trash2,
  FileAudio
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { fetchCommands, CommandsResponse } from '../services/api';

// --- Domain Model ---
interface ParsedCommand {
  id: string;
  displayName: string;
  actionType: string;
  payload: string;
  apiEnabled: boolean;
  wakewords: ParsedWakeword[];
}

interface ParsedWakeword {
  id: string;
  displayName: string;
  isActive: boolean;
  threshold?: number;
  assets: string[];
}

export default function CommandsPage() {
  const { data, isLoading, isError, error } = useQuery<CommandsResponse>({
    queryKey: ['commands'],
    queryFn: fetchCommands,
    refetchInterval: 10000,
  });

  const parsedCommands: ParsedCommand[] = useMemo(() => {
    if (!data) return [];

    // Reverse map: model_name -> list of states that use it
    const modelToStates: Record<string, string[]> = {};
    Object.entries(data.state_models || {}).forEach(([state, models]) => {
      models.forEach(model => {
        if (!modelToStates[model]) modelToStates[model] = [];
        modelToStates[model].push(state);
      });
    });

    // Helper: find all wakewords that map to a state where this command is available
    // Note: This logic assumes a simple relationship where wakewords trigger states, and states enable commands.
    // In reality, commands are just actions. The "availability" is not strictly enforced by state,
    // but typically a state (like 'computer') listens for specific commands.
    // Since the config structure is loose, we will just list associated wakewords if we can infer them.

    return Object.entries(data.commands || {}).map(([key, cmd]: [string, any]) => {
      const actionType = cmd.action || "unknown";
      let payload = "";
      if (cmd.url) payload = cmd.url;
      else if (cmd.keys) payload = `keys: ${cmd.keys}`;
      else if (cmd.message) payload = `msg: ${cmd.message}`;
      else if (cmd.payload) payload = cmd.payload;

      // Infer associated wakewords/models
      // If a command key matches a model name (often true in this system), we can show it as a trigger.
      const associatedWakewords: ParsedWakeword[] = [];

      // Check if this command IS a model name in some state
      if (modelToStates[key]) {
         associatedWakewords.push({
            id: `ww_${key}`,
            displayName: key.replace(/_/g, " "),
            isActive: true, // Assuming active if present in state_models
            assets: modelToStates[key].map(state => `Active in: ${state}`)
         });
      }

      return {
        id: key,
        displayName: key.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase()),
        actionType,
        payload,
        apiEnabled: true, // Always true for backend commands
        wakewords: associatedWakewords
      };
    });
  }, [data]);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <span className="loading loading-spinner loading-lg text-primary"></span>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="alert alert-error shadow-lg">
        <span>Error loading commands: {(error as Error).message}</span>
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
          {parsedCommands.map((command, idx) => (
            <motion.div
              key={command.id}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: idx * 0.1 }}
              className="card glass-card overflow-hidden"
            >
              {command.apiEnabled && <div className="border-gradient"></div>}
              <div className="card-body p-0">
                {/* Command Header */}
                <div className="p-6 bg-base-200/50 border-b border-base-content/10 flex justify-between items-start">
                  <div className="flex gap-3">
                    <div className="p-3 rounded-xl bg-primary/20 text-primary">
                      <TerminalSquare size={24} />
                    </div>
                    <div>
                      <h2 className="card-title text-xl mb-1">{command.displayName}</h2>
                      <div className="flex gap-2 text-xs font-mono text-base-content/60">
                        <span className="px-2 py-1 rounded bg-base-300">{command.actionType}</span>
                        <span className="px-2 py-1 rounded bg-base-300 truncate max-w-[150px]" title={command.payload}>{command.payload}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-1">
                    <div className="tooltip tooltip-bottom" data-tip="Edit Command">
                      <button
                        className="btn btn-ghost btn-sm btn-circle"
                        aria-label={`Edit ${command.displayName}`}
                      >
                        <Edit3 size={16} />
                      </button>
                    </div>
                    <div className="tooltip tooltip-bottom tooltip-error" data-tip="Delete Command">
                      <button
                        className="btn btn-ghost btn-sm btn-circle text-error"
                        aria-label={`Delete ${command.displayName}`}
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
                  {command.apiEnabled && (
                    <div className="flex items-center gap-3 p-3 rounded-lg border border-success/30 bg-success/5">
                      <Globe className="text-success" size={20} />
                      <div className="flex-1">
                        <p className="font-medium text-sm">REST API / WebUI Trigger</p>
                        <p className="text-xs text-base-content/60 font-mono mt-0.5">POST /api/v1/commands/execute</p>
                      </div>
                      <div className="badge badge-success badge-sm badge-outline">Enabled</div>
                    </div>
                  )}

                  {/* Wakewords 1-to-Many UI */}
                  <div className="space-y-3 mt-4">
                    {command.wakewords.length > 0 ? command.wakewords.map((ww) => (
                      <div key={ww.id} className="relative pl-6">
                        {/* Tree line connector */}
                        <div className="absolute left-[11px] top-0 bottom-[-16px] w-[2px] bg-base-content/10 last:bottom-auto last:h-8"></div>
                        <div className="absolute left-[11px] top-8 w-4 h-[2px] bg-base-content/10"></div>

                        <div className="flex items-start gap-3 p-4 rounded-xl border border-base-content/10 bg-base-100/50 hover:bg-base-200/50 transition-colors ml-2">
                          <Volume2 className={ww.isActive ? "text-primary" : "text-base-content/30"} size={20} />
                          <div className="flex-1">
                            <div className="flex justify-between items-center mb-2">
                              <p className="font-semibold">{ww.displayName}</p>
                              <div className="badge badge-sm badge-ghost">Voice Model</div>
                            </div>

                            {/* ONNX Assets attached to this Wakeword */}
                            <div className="space-y-1.5">
                              {ww.assets.map(asset => (
                                <div key={asset} className="flex flex-items-center gap-2 text-xs text-base-content/70 bg-base-300/50 p-1.5 rounded-md font-mono">
                                  <FileAudio size={12} className="text-accent" />
                                  <span className="truncate">{asset}</span>
                                </div>
                              ))}
                            </div>

                          </div>
                        </div>
                      </div>
                    )) : (
                        <div className="text-sm text-base-content/40 italic pl-2">No voice triggers configured</div>
                    )}

                    {/* Add Wakeword Button */}
                    <div className="relative pl-6 mt-2">
                      <div className="absolute left-[11px] top-0 w-[2px] h-6 bg-base-content/10"></div>
                      <div className="absolute left-[11px] top-6 w-4 h-[2px] bg-base-content/10"></div>
                      <button className="btn btn-ghost btn-sm text-base-content/50 ml-2 mt-2 gap-2 hover:text-primary">
                        <Plus size={14} /> Add Wakeword Binding
                      </button>
                    </div>

                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
};
