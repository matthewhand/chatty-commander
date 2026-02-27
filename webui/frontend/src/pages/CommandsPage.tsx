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
  FileAudio
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiService } from '../services/apiService';

// --- DOMAIN MODEL ---
interface Wakeword {
    id: string;
    displayName: string;
    isActive: boolean;
    threshold: number;
    assets: string[];
}

interface Command {
    id: string;
    displayName: string;
    actionType: string;
    payload: string;
    apiEnabled: boolean;
    wakewords: Wakeword[];
}

export default function CommandsPage() {
  const [activeTab, setActiveTab] = useState('all');

  const { data: commands, isLoading, isError, error } = useQuery({
    queryKey: ['commands'],
    queryFn: () => apiService.getCommands(),
  });

  if (isLoading) {
    return (
        <div className="flex justify-center items-center h-96">
            <span className="loading loading-spinner loading-lg text-primary"></span>
        </div>
    );
  }

  if (isError) {
      return (
          <div className="alert alert-error shadow-lg">
              <div>
                  <svg xmlns="http://www.w3.org/2000/svg" className="stroke-current flex-shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                  <span>Error loading commands: {(error as Error).message}</span>
              </div>
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
          {(commands as Command[])?.map((command, idx) => (
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
                        <span className="px-2 py-1 rounded bg-base-300 truncate max-w-[150px]">{command.payload}</span>
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
                    {command.wakewords.map((ww) => (
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
                    ))}

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
