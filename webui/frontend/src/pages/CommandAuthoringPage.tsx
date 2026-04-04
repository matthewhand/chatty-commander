import React, { useState, useCallback, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
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
  Edit3,
  Save,
  RefreshCw,
  Code,
  Shield,
} from 'lucide-react';
import {
  Button,
  Card,
  Alert,
  Badge,
  Input,
  Select,
  Textarea,
  Tabs,
  ConfirmModal,
  LoadingSpinner,
  Steps,
  PageHeader,
  LoadingModal,
} from '../components/DaisyUI';

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

const ACTION_TYPE_VARIANTS: Record<string, 'primary' | 'secondary' | 'info' | 'ghost'> = {
  keypress: 'primary',
  url: 'secondary',
  shell: 'primary',
  custom_message: 'info',
};

const ActionTypeBadge: React.FC<{ type: string }> = ({ type }) => (
  <Badge variant={ACTION_TYPE_VARIANTS[type] || 'ghost'} size="small">
    {type}
  </Badge>
);

const ACTION_TYPE_OPTIONS = [
  { label: 'Keypress', value: 'keypress' },
  { label: 'URL', value: 'url' },
  { label: 'Shell Command', value: 'shell' },
  { label: 'Custom Message', value: 'custom_message' },
];

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
    >
      <Card className="bg-base-200/50 border border-base-content/10" compact>
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium text-base-content/60">Action {index + 1}</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={onRemove}
              aria-label="Remove action"
              shape="circle"
              className="text-error"
            >
              <Trash2 size={16} />
            </Button>
          </div>

          <div className="form-control">
            <label className="label cursor-pointer">
              <span className="label-text text-sm">Type</span>
            </label>
            <Select
              size="sm"
              options={ACTION_TYPE_OPTIONS}
              value={action.type}
              onChange={(e) => handleTypeChange(e.target.value as CommandAction['type'])}
            />
          </div>

          {action.type === 'keypress' && (
            <Input
              label="Keys"
              size="sm"
              placeholder="e.g., ctrl+alt+t"
              value={action.keys || ''}
              onChange={(e) => handleFieldChange('keys', e.target.value)}
            />
          )}

          {action.type === 'url' && (
            <Input
              label="URL"
              size="sm"
              placeholder="https://example.com"
              value={action.url || ''}
              onChange={(e) => handleFieldChange('url', e.target.value)}
            />
          )}

          {action.type === 'shell' && (
            <Input
              label="Command"
              size="sm"
              placeholder="e.g., npm start"
              value={action.cmd || action.command || ''}
              onChange={(e) => handleFieldChange('cmd', e.target.value)}
            />
          )}

          {action.type === 'custom_message' && (
            <Input
              label="Message"
              size="sm"
              placeholder="Enter message to display"
              value={action.message || ''}
              onChange={(e) => handleFieldChange('message', e.target.value)}
            />
          )}
        </div>
      </Card>
    </motion.div>
  );
};

// --- Steps Wizard Helper ---

function computeCurrentStep(mode: 'ai' | 'manual', description: string, generatedCommand: GeneratedCommand | null, manualCommand: GeneratedCommand): number {
  if (mode === 'ai') {
    if (generatedCommand && generatedCommand.actions.length > 0) return 4;
    if (description.trim()) return 2;
    return 1;
  }
  // manual mode
  if (manualCommand.actions.length > 0 && manualCommand.name && manualCommand.display_name) return 4;
  if (manualCommand.actions.length > 0) return 3;
  if (manualCommand.name || manualCommand.display_name || manualCommand.wakeword) return 2;
  return 1;
}

// --- Main Page Component ---

const MODE_TABS = [
  { key: 'ai', label: 'AI Mode', icon: <Sparkles size={16} /> },
  { key: 'manual', label: 'Manual Mode', icon: <Code size={16} /> },
];

export default function CommandAuthoringPage() {
  useEffect(() => {
    document.title = "Command Editor | ChattyCommander";
  }, []);

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
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  const currentStep = useMemo(
    () => computeCurrentStep(mode, description, generatedCommand, manualCommand),
    [mode, description, generatedCommand, manualCommand],
  );

  const validateField = useCallback((field: string, value: string) => {
    let errorMsg = '';
    switch (field) {
      case 'name':
        if (value && !/^[a-z][a-z0-9_]*$/.test(value)) {
          errorMsg = 'Must be snake_case (lowercase letters, digits, underscores; must start with a letter)';
        } else if (!value) {
          errorMsg = 'Command name is required';
        }
        break;
      case 'display_name':
        if (!value || value.length < 2) {
          errorMsg = 'Display name is required (min 2 characters)';
        }
        break;
      case 'wakeword':
        if (!value || value.length < 2) {
          errorMsg = 'Wakeword is required (min 2 characters)';
        }
        break;
    }
    setFormErrors((prev) => {
      const next = { ...prev };
      if (errorMsg) {
        next[field] = errorMsg;
      } else {
        delete next[field];
      }
      return next;
    });
  }, []);

  const hasFormErrors = useMemo(() => Object.keys(formErrors).length > 0, [formErrors]);

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
      setFormErrors({});
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

    // Validate each action has required fields based on type
    for (let i = 0; i < commandToSave.actions.length; i++) {
      const action = commandToSave.actions[i];
      switch (action.type) {
        case 'keypress':
          if (!action.keys?.trim()) {
            setError(`Action ${i + 1} (Keypress) requires a 'keys' value`);
            return;
          }
          break;
        case 'url':
          if (!action.url?.trim()) {
            setError(`Action ${i + 1} (URL) requires a 'url' value`);
            return;
          }
          break;
        case 'shell':
          if (!action.cmd?.trim() && !action.command?.trim()) {
            setError(`Action ${i + 1} (Shell) requires a 'command' value`);
            return;
          }
          break;
        case 'custom_message':
          if (!action.message?.trim()) {
            setError(`Action ${i + 1} (Message) requires a 'message' value`);
            return;
          }
          break;
        default:
          setError(`Action ${i + 1} has an invalid type`);
          return;
      }
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

  const currentCommand = useMemo(() => mode === 'ai' && generatedCommand ? generatedCommand : manualCommand, [mode, generatedCommand, manualCommand]);

  // Build ConfirmModal message content
  const confirmMessage = useMemo(() => {
    const lines = [
      `Name: ${currentCommand.name}`,
      `Display: ${currentCommand.display_name}`,
      `Wakeword: ${currentCommand.wakeword}`,
      `Actions (${currentCommand.actions.length}): ${currentCommand.actions.map((a) => a.type).join(', ')}`,
      '',
      'Commands can execute shell commands and open URLs. Please review carefully before saving.',
    ];
    return lines.join('\n');
  }, [currentCommand]);

  return (
    <div className="space-y-6">
      {/* Steps Wizard Indicator */}
      <Steps
        steps={[
          { label: 'Choose Mode' },
          { label: 'Define Command' },
          { label: 'Configure Actions' },
          { label: 'Review & Save' }
        ]}
        currentStep={currentStep - 1}
        className="w-full mb-6"
        aria-label="Authoring progress"
      />

      {/* Header Section */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="text-sm breadcrumbs mb-2 text-base-content/60" aria-label="breadcrumbs">
          <ul>
            <li><Link to="/commands">Commands</Link></li>
            <li>Command Authoring</li>
          </ul>
        </div>
        <PageHeader
          title="Command Authoring"
          subtitle="Create new voice commands using AI assistance or manual configuration."
          icon={<Wand2 size={32} className="text-primary" />}
          actions={
            <Tabs
              tabs={MODE_TABS}
              activeTab={mode}
              onChange={(key) => setMode(key as 'ai' | 'manual')}
              variant="boxed"
              className="bg-base-200"
            />
          }
        />
      </motion.div>

      <div className="divider divider-accent"></div>

      {/* Error Display */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
          >
            <Alert
              status="error"
              icon={<AlertCircle size={20} />}
              onClose={() => setError(null)}
            >
              <span>{error}</span>
            </Alert>
          </motion.div>
        )}
      </AnimatePresence>

      {/* AI Mode: Natural Language Input */}
      {mode === 'ai' && (
        <motion.div
          id="ai-mode-panel"
          role="tabpanel"
          aria-labelledby="tab-ai-mode"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Card className="glass-card">
            <h2 className="card-title flex items-center gap-2">
              <Sparkles className="text-primary" size={20} />
              Describe Your Command
            </h2>
            <p className="text-sm text-base-content/60 mb-4">
              Describe what you want your command to do in plain English. Our AI will generate the
              configuration for you.
            </p>

            <div className="form-control">
              <label htmlFor="ai-description" className="sr-only">AI command description</label>
              <Textarea
                id="ai-description"
                className="h-32 font-normal"
                placeholder="When I say 'start my day', open my email client, my code editor, and the project management website..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>

            <Card.Actions className="mt-4">
              <Button
                variant="primary"
                onClick={handleGenerate}
                disabled={!description.trim() || generateMutation.isPending}
                loading={generateMutation.isPending}
                loadingText="Generating..."
                icon={<Wand2 size={18} />}
              >
                Generate Command
              </Button>
            </Card.Actions>
          </Card>
        </motion.div>
      )}

      {/* Generated Command Preview */}
      {mode === 'ai' && generatedCommand && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
        >
          <Card className="glass-card border-primary/30">
            <div className="flex justify-between items-start">
              <h2 className="card-title flex items-center gap-2">
                <Check className="text-success" size={20} />
                Generated Command
              </h2>
              <div className="flex gap-2">
                <Button variant="ghost" size="sm" onClick={handleRegenerate} icon={<RefreshCw size={16} />}>
                  Regenerate
                </Button>
                <Button variant="secondary" size="sm" onClick={switchToManual} icon={<Edit3 size={16} />}>
                  Edit Manually
                </Button>
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

            <Card.Actions className="mt-4">
              <Button
                variant="primary"
                onClick={handleSave}
                disabled={saveMutation.isPending}
                loading={saveMutation.isPending}
                loadingText="Saving..."
                icon={<Save size={18} />}
              >
                Save Command
              </Button>
            </Card.Actions>
          </Card>
        </motion.div>
      )}

      {/* Manual Mode: Form */}
      {mode === 'manual' && (
        <motion.div
          id="manual-mode-panel"
          role="tabpanel"
          aria-labelledby="tab-manual-mode"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Card className="glass-card">
            <h2 className="card-title flex items-center gap-2">
              <Terminal className="text-primary" size={20} />
              Manual Command Editor
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
              <Input
                label="Command Name (snake_case)"
                placeholder="my_command"
                value={manualCommand.name}
                error={formErrors.name}
                onChange={(e) =>
                  setManualCommand((prev) => ({ ...prev, name: e.target.value }))
                }
                onBlur={(e) => validateField('name', e.target.value)}
              />

              <Input
                label="Display Name"
                placeholder="My Command"
                value={manualCommand.display_name}
                error={formErrors.display_name}
                onChange={(e) =>
                  setManualCommand((prev) => ({ ...prev, display_name: e.target.value }))
                }
                onBlur={(e) => validateField('display_name', e.target.value)}
              />

              <Input
                label="Wakeword"
                placeholder="Trigger phrase"
                value={manualCommand.wakeword}
                error={formErrors.wakeword}
                onChange={(e) =>
                  setManualCommand((prev) => ({ ...prev, wakeword: e.target.value }))
                }
                onBlur={(e) => validateField('wakeword', e.target.value)}
              />
            </div>

            <div className="divider"></div>

            <div className="flex justify-between items-center">
              <h3 className="font-semibold">Actions</h3>
              <Button variant="secondary" size="sm" onClick={addManualAction} icon={<Plus size={16} />}>
                Add Action
              </Button>
            </div>

            <AnimatePresence>
              {manualCommand.actions.length === 0 ? (
                <div className="text-center py-8 text-base-content/50">
                  <Terminal size={32} className="mx-auto mb-2 opacity-50" />
                  <p>No actions defined yet. Click &quot;Add Action&quot; to get started.</p>
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

            <Card.Actions className="mt-6">
              <Button
                variant="primary"
                onClick={handleSave}
                disabled={saveMutation.isPending || manualCommand.actions.length === 0 || hasFormErrors}
                loading={saveMutation.isPending}
                loadingText="Saving..."
                icon={<Save size={18} />}
              >
                Save Command
              </Button>
            </Card.Actions>
          </Card>
        </motion.div>
      )}

      {/* LLM Unavailable Helper */}
      {mode === 'ai' && error?.includes('LLM') && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <Alert
            status="warning"
            icon={<AlertCircle size={20} />}
          >
            <div className="flex-1">
              <p className="font-medium">AI generation is currently unavailable</p>
              <p className="text-sm">You can still create commands manually using the Manual Mode.</p>
            </div>
            <Button size="sm" variant="ghost" onClick={() => setMode('manual')}>
              Switch to Manual
            </Button>
          </Alert>
        </motion.div>
      )}

      {/* Confirmation Modal */}
      <ConfirmModal
        isOpen={showConfirmModal}
        onClose={() => setShowConfirmModal(false)}
        onConfirm={confirmSave}
        title="Confirm Command Creation"
        message={confirmMessage}
        confirmText="Confirm Save"
        cancelText="Cancel"
        confirmVariant="primary"
        loading={saveMutation.isPending}
      />

      {/* AI Generation Loading Modal */}
      <LoadingModal
        isOpen={generateMutation.isPending}
        onClose={() => {}}
        title="Generating Command"
        message="Please wait while the AI analyzes your description and generates the command configuration..."
      />
    </div>
  );
}
