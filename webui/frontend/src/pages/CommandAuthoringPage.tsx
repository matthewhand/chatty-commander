import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Wand2,
  Sparkles,
  Terminal,
  AlertCircle,
  Check,
  X,
  Plus,
  Trash2,
  Loader2,
  Edit3,
  Save,
  RefreshCw,
  Code,
  Shield,
} from 'lucide-react';

// --- TypeScript Interfaces ---

interface CommandAction {
  type: 'keypress' | 'url' | 'shell' | 'custom_message';
  keys?: string;
  url?: string;
  cmd?: string;
  command?: string; // Alternative for shell
  message?: string;
}

interface GeneratedCommand {
  name: string;
  display_name: string;
  wakeword: string;
  actions: CommandAction[];
}

// --- API Functions ---

const generateCommandFromDescription = async (description: string): Promise<GeneratedCommand> => {
  const res = await fetch('/api/v1/commands/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ description }),
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }

  return res.json();
};

const saveCommand = async (command: GeneratedCommand): Promise<void> => {
  // First fetch the current config
  const configRes = await fetch('/api/v1/config');
  if (!configRes.ok) {
    throw new Error('Failed to fetch current configuration');
  }
  const config = await configRes.json();

  // Add the new command to the commands object
  const updatedCommands = {
    ...config.commands,
    [command.name]: {
      name: command.display_name,
      actions: command.actions.map(action => {
        // Normalize action structure
        const normalized: Record<string, string> = { type: action.type };
        if (action.keys) normalized.keys = action.keys;
        if (action.url) normalized.url = action.url;
        if (action.cmd) normalized.cmd = action.cmd;
        else if (action.command) normalized.cmd = action.command;
        if (action.message) normalized.message = action.message;
        return normalized;
      }),
      ...(command.wakeword ? { wakeword: command.wakeword } : {}),
    },
  };

  // Save the updated config
  const saveRes = await fetch('/api/v1/config', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ...config,
      commands: updatedCommands,
    }),
  });

  if (!saveRes.ok) {
    const error = await saveRes.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${saveRes.status}`);
  }
};

// --- Components ---

const ActionTypeBadge: React.FC<{ type: string }> = ({ type }) => {
  const colors: Record<string, string> = {
    keypress: 'badge-primary',
    url: 'badge-secondary',
    shell: 'badge-accent',
    custom_message: 'badge-info',
  };

  return (
    <span className={`badge ${colors[type] || 'badge-ghost'} badge-sm`}>
      {type}
    </span>
  );
};

const ActionField: React.FC<{
  action: CommandAction;
  onChange: (action: CommandAction) => void;
  onRemove: () => void;
  index: number;
}> = ({ action, onChange, onRemove, index }) => {
  const handleTypeChange = (type: CommandAction['type']) => {
    onChange({ type } as CommandAction);
  };

  const handleFieldChange = (field: string, value: string) => {
    onChange({ ...action, [field]: value });
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      className="card bg-base-200/50 border border-base-content/10 p-4 space-y-3"
    >
      <div className="flex justify-between items-center">
        <span className="text-sm font-medium text-base-content/60">Action {index + 1}</span>
        <button
          onClick={onRemove}
          className="btn btn-ghost btn-sm btn-circle text-error"
          aria-label="Remove action"
        >
          <Trash2 size={16} />
        </button>
      </div>

      <div className="form-control">
        <label className="label">
          <span className="label-text text-sm">Type</span>
        </label>
        <select
          className="select select-sm select-bordered w-full"
          value={action.type}
          onChange={(e) => handleTypeChange(e.target.value as CommandAction['type'])}
        >
          <option value="keypress">Keypress</option>
          <option value="url">URL</option>
          <option value="shell">Shell Command</option>
          <option value="custom_message">Custom Message</option>
        </select>
      </div>

      {action.type === 'keypress' && (
        <div className="form-control">
          <label className="label">
            <span className="label-text text-sm">Keys</span>
          </label>
          <input
            type="text"
            className="input input-sm input-bordered"
            placeholder="e.g., ctrl+alt+t"
            value={action.keys || ''}
            onChange={(e) => handleFieldChange('keys', e.target.value)}
          />
        </div>
      )}

      {action.type === 'url' && (
        <div className="form-control">
          <label className="label">
            <span className="label-text text-sm">URL</span>
          </label>
          <input
            type="text"
            className="input input-sm input-bordered"
            placeholder="https://example.com"
            value={action.url || ''}
            onChange={(e) => handleFieldChange('url', e.target.value)}
          />
        </div>
      )}

      {action.type === 'shell' && (
        <div className="form-control">
          <label className="label">
            <span className="label-text text-sm">Command</span>
          </label>
          <input
            type="text"
            className="input input-sm input-bordered"
            placeholder="e.g., npm start"
            value={action.cmd || action.command || ''}
            onChange={(e) => handleFieldChange('cmd', e.target.value)}
          />
        </div>
      )}

      {action.type === 'custom_message' && (
        <div className="form-control">
          <label className="label">
            <span className="label-text text-sm">Message</span>
          </label>
          <input
            type="text"
            className="input input-sm input-bordered"
            placeholder="Enter message to display"
            value={action.message || ''}
            onChange={(e) => handleFieldChange('message', e.target.value)}
          />
        </div>
      )}
    </motion.div>
  );
};

// --- Main Page Component ---

export default function CommandAuthoringPage() {
  const queryClient = useQueryClient();
  const [mode, setMode] = useState<'ai' | 'manual'>('ai');
  const [description, setDescription] = useState('');
  const [generatedCommand, setGeneratedCommand] = useState<GeneratedCommand | null>(null);
  const [manualCommand, setManualCommand] = useState<GeneratedCommand>({
    name: '',
    display_name: '',
    wakeword: '',
    actions: [],
  });
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Generate command mutation
  const generateMutation = useMutation({
    mutationFn: generateCommandFromDescription,
    onSuccess: (data) => {
      setGeneratedCommand(data);
      setError(null);
    },
    onError: (err: Error) => {
      setError(err.message);
      setGeneratedCommand(null);
    },
  });

  // Save command mutation
  const saveMutation = useMutation({
    mutationFn: saveCommand,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['commands'] });
      setShowConfirmModal(false);
      // Reset form
      setDescription('');
      setGeneratedCommand(null);
      setManualCommand({ name: '', display_name: '', wakeword: '', actions: [] });
      setError(null);
    },
    onError: (err: Error) => {
      setError(err.message);
      setShowConfirmModal(false);
    },
  });

  const handleGenerate = useCallback(() => {
    if (!description.trim()) return;
    generateMutation.mutate(description);
  }, [description, generateMutation]);

  const handleRegenerate = useCallback(() => {
    if (!description.trim()) return;
    generateMutation.mutate(description);
  }, [description, generateMutation]);

  const handleSave = useCallback(() => {
    const commandToSave = mode === 'ai' && generatedCommand ? generatedCommand : manualCommand;

    // Validation
    if (!commandToSave.name.trim()) {
      setError('Command name is required');
      return;
    }
    if (!commandToSave.display_name.trim()) {
      setError('Display name is required');
      return;
    }
    if (commandToSave.actions.length === 0) {
      setError('At least one action is required');
      return;
    }

    setShowConfirmModal(true);
    setError(null);
  }, [mode, generatedCommand, manualCommand]);

  const confirmSave = useCallback(() => {
    const commandToSave = mode === 'ai' && generatedCommand ? generatedCommand : manualCommand;
    saveMutation.mutate(commandToSave);
  }, [mode, generatedCommand, manualCommand, saveMutation]);

  const addManualAction = useCallback(() => {
    setManualCommand((prev) => ({
      ...prev,
      actions: [...prev.actions, { type: 'keypress' }],
    }));
  }, []);

  const updateManualAction = useCallback((index: number, action: CommandAction) => {
    setManualCommand((prev) => ({
      ...prev,
      actions: prev.actions.map((a, i) => (i === index ? action : a)),
    }));
  }, []);

  const removeManualAction = useCallback((index: number) => {
    setManualCommand((prev) => ({
      ...prev,
      actions: prev.actions.filter((_, i) => i !== index),
    }));
  }, []);

  const switchToManual = useCallback(() => {
    if (generatedCommand) {
      setManualCommand(generatedCommand);
    }
    setMode('manual');
  }, [generatedCommand]);

  const currentCommand = mode === 'ai' && generatedCommand ? generatedCommand : manualCommand;

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4"
      >
        <div>
          <h1 className="text-3xl font-bold text-gradient-primary flex items-center gap-3">
            <Wand2 size={32} />
            Command Authoring
          </h1>
          <p className="text-base-content/60 mt-1">
            Create new voice commands using AI assistance or manual configuration.
          </p>
        </div>

        {/* Mode Toggle */}
        <div className="tabs tabs-boxed bg-base-200">
          <button
            className={`tab ${mode === 'ai' ? 'tab-active' : ''}`}
            onClick={() => setMode('ai')}
          >
            <Sparkles size={16} className="mr-2" />
            AI Mode
          </button>
          <button
            className={`tab ${mode === 'manual' ? 'tab-active' : ''}`}
            onClick={() => setMode('manual')}
          >
            <Code size={16} className="mr-2" />
            Manual Mode
          </button>
        </div>
      </motion.div>

      <div className="divider divider-accent"></div>

      {/* Error Display */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="alert alert-error"
          >
            <AlertCircle size={20} />
            <span>{error}</span>
            <button onClick={() => setError(null)} className="btn btn-ghost btn-sm btn-circle">
              <X size={16} />
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* AI Mode: Natural Language Input */}
      {mode === 'ai' && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card glass-card"
        >
          <div className="card-body">
            <h2 className="card-title flex items-center gap-2">
              <Sparkles className="text-primary" size={20} />
              Describe Your Command
            </h2>
            <p className="text-sm text-base-content/60 mb-4">
              Describe what you want your command to do in plain English. Our AI will generate the
              configuration for you.
            </p>

            <div className="form-control">
              <textarea
                className="textarea textarea-bordered h-32 font-normal"
                placeholder="When I say 'start my day', open my email client, my code editor, and the project management website..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>

            <div className="card-actions justify-end mt-4">
              <button
                className="btn btn-primary"
                onClick={handleGenerate}
                disabled={!description.trim() || generateMutation.isPending}
              >
                {generateMutation.isPending ? (
                  <>
                    <Loader2 size={18} className="animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Wand2 size={18} />
                    Generate Command
                  </>
                )}
              </button>
            </div>
          </div>
        </motion.div>
      )}

      {/* Generated Command Preview */}
      {mode === 'ai' && generatedCommand && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="card glass-card border-primary/30"
        >
          <div className="card-body">
            <div className="flex justify-between items-start">
              <h2 className="card-title flex items-center gap-2">
                <Check className="text-success" size={20} />
                Generated Command
              </h2>
              <div className="flex gap-2">
                <button className="btn btn-ghost btn-sm" onClick={handleRegenerate}>
                  <RefreshCw size={16} className="mr-1" />
                  Regenerate
                </button>
                <button className="btn btn-secondary btn-sm" onClick={switchToManual}>
                  <Edit3 size={16} className="mr-1" />
                  Edit Manually
                </button>
              </div>
            </div>

            <div className="mt-4 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-base-200/50 p-4 rounded-xl">
                  <p className="text-xs text-base-content/50 uppercase tracking-wider">Name</p>
                  <p className="font-mono text-sm">{generatedCommand.name}</p>
                </div>
                <div className="bg-base-200/50 p-4 rounded-xl">
                  <p className="text-xs text-base-content/50 uppercase tracking-wider">Display Name</p>
                  <p className="font-medium">{generatedCommand.display_name}</p>
                </div>
                <div className="bg-base-200/50 p-4 rounded-xl">
                  <p className="text-xs text-base-content/50 uppercase tracking-wider">Wakeword</p>
                  <p className="font-medium">{generatedCommand.wakeword}</p>
                </div>
              </div>

              <div>
                <p className="text-xs text-base-content/50 uppercase tracking-wider mb-2">Actions</p>
                <div className="space-y-2">
                  {generatedCommand.actions.map((action, idx) => (
                    <div
                      key={idx}
                      className="flex items-center gap-3 p-3 rounded-lg bg-base-200/30 border border-base-content/10"
                    >
                      <ActionTypeBadge type={action.type} />
                      <span className="text-sm font-mono text-base-content/70">
                        {action.keys || action.url || action.cmd || action.command || action.message || 'No details'}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="card-actions justify-end mt-4">
              <button
                className="btn btn-primary"
                onClick={handleSave}
                disabled={saveMutation.isPending}
              >
                {saveMutation.isPending ? (
                  <>
                    <Loader2 size={18} className="animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save size={18} />
                    Save Command
                  </>
                )}
              </button>
            </div>
          </div>
        </motion.div>
      )}

      {/* Manual Mode: Form */}
      {mode === 'manual' && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card glass-card"
        >
          <div className="card-body">
            <h2 className="card-title flex items-center gap-2">
              <Terminal className="text-primary" size={20} />
              Manual Command Editor
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
              <div className="form-control">
                <label className="label">
                  <span className="label-text">Command Name (snake_case)</span>
                </label>
                <input
                  type="text"
                  className="input input-bordered"
                  placeholder="my_command"
                  value={manualCommand.name}
                  onChange={(e) =>
                    setManualCommand((prev) => ({ ...prev, name: e.target.value }))
                  }
                />
              </div>

              <div className="form-control">
                <label className="label">
                  <span className="label-text">Display Name</span>
                </label>
                <input
                  type="text"
                  className="input input-bordered"
                  placeholder="My Command"
                  value={manualCommand.display_name}
                  onChange={(e) =>
                    setManualCommand((prev) => ({ ...prev, display_name: e.target.value }))
                  }
                />
              </div>

              <div className="form-control">
                <label className="label">
                  <span className="label-text">Wakeword</span>
                </label>
                <input
                  type="text"
                  className="input input-bordered"
                  placeholder="Trigger phrase"
                  value={manualCommand.wakeword}
                  onChange={(e) =>
                    setManualCommand((prev) => ({ ...prev, wakeword: e.target.value }))
                  }
                />
              </div>
            </div>

            <div className="divider"></div>

            <div className="flex justify-between items-center">
              <h3 className="font-semibold">Actions</h3>
              <button className="btn btn-secondary btn-sm" onClick={addManualAction}>
                <Plus size={16} className="mr-1" />
                Add Action
              </button>
            </div>

            <AnimatePresence>
              {manualCommand.actions.length === 0 ? (
                <div className="text-center py-8 text-base-content/50">
                  <Terminal size={32} className="mx-auto mb-2 opacity-50" />
                  <p>No actions defined yet. Click "Add Action" to get started.</p>
                </div>
              ) : (
                <div className="space-y-3 mt-4">
                  {manualCommand.actions.map((action, idx) => (
                    <ActionField
                      key={idx}
                      index={idx}
                      action={action}
                      onChange={(updated) => updateManualAction(idx, updated)}
                      onRemove={() => removeManualAction(idx)}
                    />
                  ))}
                </div>
              )}
            </AnimatePresence>

            <div className="card-actions justify-end mt-6">
              <button
                className="btn btn-primary"
                onClick={handleSave}
                disabled={saveMutation.isPending || manualCommand.actions.length === 0}
              >
                {saveMutation.isPending ? (
                  <>
                    <Loader2 size={18} className="animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save size={18} />
                    Save Command
                  </>
                )}
              </button>
            </div>
          </div>
        </motion.div>
      )}

      {/* LLM Unavailable Helper */}
      {mode === 'ai' && error?.includes('LLM') && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="alert alert-warning"
        >
          <AlertCircle size={20} />
          <div className="flex-1">
            <p className="font-medium">AI generation is currently unavailable</p>
            <p className="text-sm">You can still create commands manually using the Manual Mode.</p>
          </div>
          <button className="btn btn-sm" onClick={() => setMode('manual')}>
            Switch to Manual
          </button>
        </motion.div>
      )}

      {/* Confirmation Modal */}
      <AnimatePresence>
        {showConfirmModal && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 z-40"
              onClick={() => setShowConfirmModal(false)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="fixed inset-0 flex items-center justify-center z-50 p-4"
            >
              <div className="card glass-card max-w-lg w-full bg-base-100 shadow-2xl">
                <div className="card-body">
                  <div className="flex items-center gap-3 text-warning mb-4">
                    <Shield size={28} />
                    <h3 className="text-xl font-bold">Confirm Command Creation</h3>
                  </div>

                  <div className="alert alert-warning mb-4">
                    <AlertCircle size={18} />
                    <span className="text-sm">
                      Commands can execute shell commands and open URLs. Please review carefully
                      before saving.
                    </span>
                  </div>

                  <div className="bg-base-200/50 rounded-xl p-4 space-y-2 mb-4">
                    <div className="flex justify-between">
                      <span className="text-sm text-base-content/60">Name:</span>
                      <span className="font-mono text-sm">{currentCommand.name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-base-content/60">Display:</span>
                      <span className="text-sm">{currentCommand.display_name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-base-content/60">Wakeword:</span>
                      <span className="text-sm">{currentCommand.wakeword}</span>
                    </div>
                    <div className="pt-2 border-t border-base-content/10">
                      <span className="text-sm text-base-content/60">Actions ({currentCommand.actions.length}):</span>
                      <div className="mt-2 space-y-1">
                        {currentCommand.actions.map((action, idx) => (
                          <div key={idx} className="flex items-center gap-2 text-sm">
                            <ActionTypeBadge type={action.type} />
                            <span className="text-base-content/70 truncate">
                              {action.keys || action.url || action.cmd || action.command || action.message || '—'}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="card-actions justify-end gap-2">
                    <button
                      className="btn btn-ghost"
                      onClick={() => setShowConfirmModal(false)}
                    >
                      Cancel
                    </button>
                    <button
                      className="btn btn-primary"
                      onClick={confirmSave}
                      disabled={saveMutation.isPending}
                    >
                      {saveMutation.isPending ? (
                        <>
                          <Loader2 size={16} className="animate-spin mr-1" />
                          Saving...
                        </>
                      ) : (
                        <>
                          <Check size={16} className="mr-1" />
                          Confirm Save
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
