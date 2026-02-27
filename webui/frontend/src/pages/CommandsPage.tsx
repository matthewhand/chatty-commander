import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  TerminalSquare,
  Settings2,
  Globe,
  Plus,
  Play
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiService } from '../services/apiService';

interface CommandDefinition {
  name: string;
  action_type: string;
  details: any;
}

export default function CommandsPage() {
  const [executing, setExecuting] = useState<string | null>(null);

  const { data: commands, isLoading, error } = useQuery<CommandDefinition[]>({
    queryKey: ['commands'],
    queryFn: () => apiService.getCommands(),
  });

  const handleExecute = async (commandName: string) => {
    setExecuting(commandName);
    try {
      await apiService.executeCommand(commandName);
    } catch (err) {
      console.error(err);
      alert(`Failed to execute ${commandName}`);
    } finally {
      setExecuting(null);
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-full">
        <span className="loading loading-spinner loading-lg text-primary"></span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert alert-error shadow-lg">
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
        <button className="btn btn-primary glass">
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
              key={command.name}
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
                      <h2 className="card-title text-xl mb-1">{command.name}</h2>
                      <div className="flex gap-2 text-xs font-mono text-base-content/60">
                        <span className="px-2 py-1 rounded bg-base-300 uppercase">{command.action_type}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-1">
                     <button
                        className={`btn btn-sm ${executing === command.name ? 'loading' : 'btn-outline btn-success'}`}
                        onClick={() => handleExecute(command.name)}
                        disabled={executing === command.name}
                     >
                       {!executing && <Play size={16} />}
                       Execute
                     </button>
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
                      <p className="text-xs text-base-content/60 font-mono mt-0.5">POST /api/v1/command</p>
                    </div>
                    <div className="badge badge-success badge-sm badge-outline">Enabled</div>
                  </div>

                  {/* Details View */}
                  <div className="mockup-code bg-base-300 text-xs p-0 before:hidden">
                    <pre className="p-4 overflow-x-auto">
                        <code>{JSON.stringify(command.details, null, 2)}</code>
                    </pre>
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
