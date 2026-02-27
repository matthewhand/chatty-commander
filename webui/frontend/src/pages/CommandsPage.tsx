import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  TerminalSquare,
  Settings2,
  Globe,
  Plus,
  Play,
  Search,
  Keyboard,
  Link,
  Code
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
  const [searchQuery, setSearchQuery] = useState('');
  const [feedback, setFeedback] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  const { data: commands, isLoading, error } = useQuery<CommandDefinition[]>({
    queryKey: ['commands'],
    queryFn: () => apiService.getCommands(),
  });

  const handleExecute = async (commandName: string) => {
    setExecuting(commandName);
    setFeedback(null);
    try {
      const response = await apiService.executeCommand(commandName);
      if (response.success) {
        setFeedback({
          message: `Executed in ${response.execution_time.toFixed(1)}ms: ${response.message}`,
          type: 'success'
        });
      } else {
        setFeedback({ message: response.message, type: 'error' });
      }
    } catch (err: any) {
      setFeedback({ message: err.message || 'Execution failed', type: 'error' });
    } finally {
      setExecuting(null);
      // Auto-dismiss success messages after 3s
      setTimeout(() => setFeedback((prev) => prev?.type === 'success' ? null : prev), 3000);
    }
  };

  const filteredCommands = commands?.filter(cmd =>
    cmd.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getActionIcon = (type: string) => {
    switch(type) {
      case 'keypress': return <Keyboard size={14} />;
      case 'url': return <Link size={14} />;
      case 'shell': return <TerminalSquare size={14} />;
      default: return <Code size={14} />;
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
      {/* Feedback Toast */}
      <AnimatePresence>
        {feedback && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className={`alert ${feedback.type === 'success' ? 'alert-success' : 'alert-error'} fixed top-4 right-4 z-50 w-auto shadow-lg max-w-md`}
          >
            <span>{feedback.message}</span>
          </motion.div>
        )}
      </AnimatePresence>

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
        <div className="flex gap-2">
            <div className="relative">
                <input
                    type="text"
                    placeholder="Search commands..."
                    className="input input-bordered pl-10 w-full md:w-64"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                />
                <Search className="absolute left-3 top-3 text-base-content/40" size={18} />
            </div>
            <button className="btn btn-primary glass">
            <Plus size={18} />
            New Command
            </button>
        </div>
      </motion.div>

      <div className="divider divider-accent"></div>

      {/* Commands Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <AnimatePresence>
          {filteredCommands?.map((command, idx) => (
            <motion.div
              key={command.name}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
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
                        <span className="px-2 py-1 rounded bg-base-300 uppercase flex items-center gap-1">
                            {getActionIcon(command.action_type)}
                            {command.action_type}
                        </span>
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

                  {/* Better Details View */}
                  <div className="bg-base-300/50 rounded-lg p-3 text-sm border border-base-content/5">
                    {command.action_type === 'keypress' && (
                        <div className="flex items-center gap-2">
                            <Keyboard size={16} className="text-secondary" />
                            <span className="font-semibold text-base-content/70">Keys:</span>
                            <kbd className="kbd kbd-sm">{command.details.keys || command.details.keypress}</kbd>
                        </div>
                    )}
                    {command.action_type === 'url' && (
                        <div className="flex items-center gap-2 overflow-hidden">
                            <Link size={16} className="text-info" />
                            <span className="font-semibold text-base-content/70">URL:</span>
                            <span className="font-mono text-xs truncate">{command.details.url}</span>
                        </div>
                    )}
                     {command.action_type === 'shell' && (
                        <div className="flex items-center gap-2 overflow-hidden">
                            <TerminalSquare size={16} className="text-warning" />
                            <span className="font-semibold text-base-content/70">Cmd:</span>
                            <code className="font-mono text-xs bg-base-100 px-1 py-0.5 rounded truncate">{command.details.shell || command.details.cmd}</code>
                        </div>
                    )}
                     {command.action_type === 'custom_message' && (
                        <div className="flex items-center gap-2">
                            <Code size={16} className="text-accent" />
                            <span className="font-semibold text-base-content/70">Msg:</span>
                            <span className="italic">"{command.details.message}"</span>
                        </div>
                    )}
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
          {filteredCommands?.length === 0 && (
              <div className="col-span-full text-center py-12 text-base-content/50">
                  <p>No commands found matching "{searchQuery}"</p>
              </div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};
