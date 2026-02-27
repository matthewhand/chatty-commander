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
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchCommands, deleteCommand, saveCommand, CommandDefinition } from '../services/api';

export default function CommandsPage() {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('all');

  // Real data fetch
  const { data: commands, isLoading, isError } = useQuery({
    queryKey: ['commands'],
    queryFn: fetchCommands,
  });

  const deleteMutation = useMutation({
    mutationFn: deleteCommand,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['commands'] });
    },
    onError: (err: any) => {
      alert(`Failed to delete command: ${err.message}`);
    }
  });

  const handleDelete = (name: string) => {
    if (confirm(`Are you sure you want to delete command "${name}"?`)) {
        deleteMutation.mutate(name);
    }
  };

  const handleCreate = () => {
      // Very basic create implementation for proof of concept
      const name = prompt("Enter command name (key):");
      if (!name) return;
      const action = prompt("Enter action type (keypress, shell, url):", "keypress");
      if (!action) return;

      const newCmd: CommandDefinition = { name, action };
      saveCommand(newCmd).then(() => {
          queryClient.invalidateQueries({ queryKey: ['commands'] });
      }).catch(err => alert(err.message));
  };

  if (isLoading) {
      return (
        <div className="flex justify-center items-center h-full">
          <span className="loading loading-spinner loading-lg text-primary"></span>
        </div>
      );
  }

  if (isError) {
      return (
          <div className="alert alert-error">
              <span>Failed to load commands.</span>
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
        <button className="btn btn-primary glass" onClick={handleCreate}>
          <Plus size={18} />
          New Command
        </button>
      </motion.div>

      <div className="divider divider-accent"></div>

      {/* Commands Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <AnimatePresence>
          {commands?.map((command, idx) => (
            <motion.div
              key={command.id}
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
                      <h2 className="card-title text-xl mb-1">{command.displayName}</h2>
                      <div className="flex gap-2 text-xs font-mono text-base-content/60">
                        <span className="px-2 py-1 rounded bg-base-300">{command.actionType}</span>
                        {command.description && <span className="px-2 py-1 rounded bg-base-300 truncate max-w-[150px]">{command.description}</span>}
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-1">
                    <div className="tooltip tooltip-bottom" data-tip="Edit Command">
                      <button
                        className="btn btn-ghost btn-sm btn-circle"
                        aria-label={`Edit ${command.displayName}`}
                        onClick={() => alert("Edit not implemented in this demo")}
                      >
                        <Edit3 size={16} />
                      </button>
                    </div>
                    <div className="tooltip tooltip-bottom tooltip-error" data-tip="Delete Command">
                      <button
                        className="btn btn-ghost btn-sm btn-circle text-error"
                        aria-label={`Delete ${command.displayName}`}
                        onClick={() => handleDelete(command.name)}
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
                      <p className="text-xs text-base-content/60 font-mono mt-0.5">POST /api/v1/commands/execute</p>
                    </div>
                    <div className="badge badge-success badge-sm badge-outline">Enabled</div>
                  </div>

                  {/* Wakewords (Placeholder for now as backend doesn't link them) */}
                  <div className="space-y-3 mt-4">
                     <p className="text-xs text-base-content/40 italic">Wakeword bindings not yet configured in backend.</p>
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
