import React from 'react';
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
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiService } from '../services/apiService';

// --- TYPES ---
interface WakewordConfig {
  id: string;
  displayName: string;
  isActive: boolean;
  threshold: number;
  assets: string[];
}

interface CommandConfig {
  id: string;
  displayName: string;
  actionType: string;
  payload: string;
  apiEnabled: boolean;
  wakewords: WakewordConfig[];
}

// Helper to transform backend config into UI model
const transformConfigToCommands = (config: any): CommandConfig[] => {
  if (!config || !config.commands) return [];

  const commands: CommandConfig[] = [];
  const stateModels = config.state_models || {};
  const wakewordStateMap = config.wakeword_state_map || {};

  Object.entries(config.commands).forEach(([key, cmd]: [string, any]) => {
    // Determine action type and payload
    let actionType = "unknown";
    let payload = "";

    if (cmd.action === "keypress") {
      actionType = "keypress";
      payload = cmd.keys || "";
    } else if (cmd.action === "url") {
      actionType = "url";
      payload = cmd.url || "";
    } else if (cmd.action === "shell") {
      actionType = "shell";
      payload = cmd.cmd || "";
    } else if (cmd.action === "custom_message") {
      actionType = "custom_message";
      payload = cmd.message || "";
    } else if (cmd.action === "voice_chat") {
      actionType = "voice_chat";
      payload = "(voice interaction)";
    }

    // Find associated wakewords/models
    const wakewords: WakewordConfig[] = [];

    // Check state_models for direct mapping (command key matches model name/wakeword)
    Object.entries(stateModels).forEach(([state, models]: [string, any]) => {
      if (Array.isArray(models) && models.includes(key)) {
         wakewords.push({
           id: `ww_${key}_${state}`,
           displayName: `${key} (${state})`,
           isActive: true,
           threshold: config.wake_word_threshold || 0.5,
           assets: [`${state}/${key}.onnx`] // Approximate path for display
         });
      }
    });

    commands.push({
      id: key,
      displayName: key, // Use key as display name for now
      actionType,
      payload,
      apiEnabled: true, // Assuming all configured commands are callable via API
      wakewords
    });
  });

  return commands;
};

export default function CommandsPage() {
  const queryClient = useQueryClient();

  // Fetch configuration
  const { data: config, isLoading, isError } = useQuery({
    queryKey: ['config'],
    queryFn: () => apiService.getConfig()
  });

  // Mutation for deleting a command
  const deleteMutation = useMutation({
    mutationFn: async (commandId: string) => {
      if (!config) return;
      // Use structuredClone for deep copy to avoid mutating React Query cache
      const newConfig = structuredClone(config);
      if (newConfig.commands && newConfig.commands[commandId]) {
        delete newConfig.commands[commandId];
        await apiService.updateConfig(newConfig);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['config'] });
    }
  });

  const handleDelete = (commandId: string) => {
    if (window.confirm(`Are you sure you want to delete command "${commandId}"?`)) {
      deleteMutation.mutate(commandId);
    }
  };

  const commands = React.useMemo(() => transformConfigToCommands(config), [config]);

  if (isLoading) {
    return <div className="p-8 text-center text-base-content/50">Loading commands...</div>;
  }

  if (isError) {
    return <div className="p-8 text-center text-error">Failed to load configuration.</div>;
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
          {commands.map((command, idx) => (
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
                        disabled
                      >
                        <Edit3 size={16} />
                      </button>
                    </div>
                    <div className="tooltip tooltip-bottom tooltip-error" data-tip="Delete Command">
                      <button
                        className="btn btn-ghost btn-sm btn-circle text-error"
                        aria-label={`Delete ${command.displayName}`}
                        onClick={() => handleDelete(command.id)}
                        disabled={deleteMutation.isPending}
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
                    {command.wakewords.length > 0 ? (
                      command.wakewords.map((ww) => (
                        <div key={ww.id} className="relative pl-6">
                          {/* Tree line connector */}
                          <div className="absolute left-[11px] top-0 bottom-[-16px] w-[2px] bg-base-content/10 last:bottom-auto last:h-8"></div>
                          <div className="absolute left-[11px] top-8 w-4 h-[2px] bg-base-content/10"></div>

                          <div className="flex items-start gap-3 p-4 rounded-xl border border-base-content/10 bg-base-100/50 hover:bg-base-200/50 transition-colors ml-2">
                            <Volume2 className={ww.isActive ? "text-primary" : "text-base-content/30"} size={20} />
                            <div className="flex-1">
                              <div className="flex justify-between items-center mb-2">
                                <p className="font-semibold">{ww.displayName}</p>
                                <input
                                  type="checkbox"
                                  className="toggle toggle-sm toggle-primary"
                                  defaultChecked={ww.isActive}
                                  aria-label={`Toggle ${ww.displayName} wakeword`}
                                  disabled
                                />
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
                      ))
                    ) : (
                      <div className="text-sm text-base-content/40 italic pl-6">No wakewords configured</div>
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
