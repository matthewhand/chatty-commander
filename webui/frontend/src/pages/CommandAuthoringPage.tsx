import React, { useState, useCallback, useEffect, useMemo, useRef } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useReducedMotionPref } from '../hooks/useReducedMotionPref';
import { useUnsavedChanges } from '../hooks/useUnsavedChanges';
import { useToast } from '../components/ToastProvider';
import Collapse from '../components/Collapse';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Wand2,
  Sparkles,
  Terminal,
  AlertCircle,
  AlertTriangle,
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
  Lightbulb,
} from 'lucide-react';

// Starter prompts for AI mode. They give a first-time user concrete ideas (and
// fill what was otherwise an empty pre-generation screen); clicking one drops it
// into the description box to tweak and generate.
const AI_PROMPT_EXAMPLES: { title: string; prompt: string }[] = [
  {
    title: 'Start my workday',
    prompt:
      "When I say 'start my day', open my email, my code editor, and the project board.",
  },
  {
    title: 'Take a screenshot',
    prompt: "When I say 'take a screenshot', press the Print Screen key.",
  },
  {
    title: 'Mute the microphone',
    prompt: "When I say 'mute', toggle my microphone with ctrl+shift+m.",
  },
  {
    title: 'Open a dashboard',
    prompt:
      "When I say 'open dashboard', open https://grafana.local in my browser.",
  },
];

// --- TypeScript Interfaces ---

interface CommandAction {
  type: 'keypress' | 'url' | 'shell' | 'custom_message';
  keys?: string;
  url?: string;
  cmd?: string;
  command?: string; // Alternative for shell
  message?: string;
}

// --- Danger heuristics ---

/**
 * Heuristic scan of a shell command string for patterns that are commonly
 * destructive or that pull-and-execute remote code. Returns a human-readable
 * warning, or null when nothing suspicious is found. This is advisory only —
 * it never blocks saving, it just surfaces risk to the author.
 */
export function detectShellDanger(cmd: string): string | null {
  const c = cmd.trim();
  if (!c) return null;
  const lower = c.toLowerCase();
  if (/\brm\s+(-[a-z]*\s+)*-[a-z]*f|\brm\s+-[a-z]*r[a-z]*f|\brm\s+-rf|\brm\s+-fr/.test(lower)) {
    return 'Looks like a recursive/forced delete (rm -rf). This can permanently destroy files.';
  }
  if (/\b(curl|wget)\b[^|]*\|\s*(sudo\s+)?(sh|bash|zsh)\b/.test(lower)) {
    return 'Pipes a downloaded script straight into a shell (curl | sh). This runs untrusted remote code.';
  }
  if (/(^|\s)sudo\s/.test(lower)) {
    return 'Runs with elevated privileges (sudo). Make sure you trust this command.';
  }
  if (/\b(mkfs|dd\s+if=)/.test(lower) || /:\(\)\s*\{.*\}\s*;/.test(c)) {
    return 'Contains a potentially destructive disk/fork operation.';
  }
  if (/>\s*\/dev\/sd|>\s*\/dev\/disk/.test(lower)) {
    return 'Writes directly to a raw disk device. This can corrupt the system.';
  }
  return null;
}

/**
 * Heuristic scan of a URL action. Flags schemes other than https unless the
 * host is localhost/127.0.0.1 (a common, intentional local-dev target).
 * Returns a warning string or null.
 */
export function detectUrlDanger(url: string): string | null {
  const u = url.trim();
  if (!u) return null;
  let parsed: URL | null = null;
  try {
    parsed = new URL(u);
  } catch {
    // Not parseable as an absolute URL — flag so the author adds a scheme.
    return 'URL has no scheme. Use https:// (or http://localhost for local development).';
  }
  const host = parsed.hostname.toLowerCase();
  const isLocal = host === 'localhost' || host === '127.0.0.1' || host === '::1' || host === '[::1]';
  if (parsed.protocol === 'https:') return null;
  if (parsed.protocol === 'http:' && isLocal) return null;
  if (parsed.protocol === 'http:') {
    return 'Uses insecure http:// for a non-local host. Prefer https://.';
  }
  return `Unusual URL scheme "${parsed.protocol.replace(':', '')}". Expected https (or http on localhost).`;
}

/** A flagged action for prominent display in the confirm modal. */
interface DangerFlag {
  index: number;
  type: string;
  detail: string;
  warning: string;
}

function actionDetail(action: CommandAction): string {
  return action.keys || action.url || action.cmd || action.command || action.message || '';
}

/** Collect danger flags across all actions of a command. */
export function collectDangerFlags(actions: CommandAction[]): DangerFlag[] {
  const flags: DangerFlag[] = [];
  actions.forEach((action, index) => {
    let warning: string | null = null;
    if (action.type === 'shell') {
      warning = detectShellDanger(action.cmd || action.command || '');
    } else if (action.type === 'url') {
      warning = detectUrlDanger(action.url || '');
    }
    if (warning) {
      flags.push({ index, type: action.type, detail: actionDetail(action), warning });
    }
  });
  return flags;
}

/**
 * Validate a single action and return an error message, or null if valid.
 * Shared by both AI and manual flows so validation is symmetric.
 */
export function validateAction(action: CommandAction): string | null {
  switch (action.type) {
    case 'keypress':
      return action.keys?.trim() ? null : "Keypress requires a 'keys' value (e.g. ctrl+alt+t)";
    case 'url':
      return action.url?.trim() ? null : "URL requires a 'url' value";
    case 'shell':
      return action.cmd?.trim() || action.command?.trim()
        ? null
        : "Shell action requires a 'command' value";
    case 'custom_message':
      return action.message?.trim() ? null : "Message requires a 'message' value";
    default:
      return 'Action has an invalid type';
  }
}

const fetchExistingCommandNames = async (): Promise<string[]> => {
  const res = await fetch('/api/v1/config');
  if (!res.ok) return [];
  const config = await res.json().catch(() => ({}));
  return config?.commands ? Object.keys(config.commands) : [];
};

interface GeneratedCommand {
  name: string;
  display_name: string;
  wakeword: string;
  actions: CommandAction[];
}

/**
 * Normalize a command into the exact shape that {@link saveCommand} persists
 * (e.g. `command` → `cmd`, a singular `action` already flattened to `actions`).
 * Used both when writing config and when computing the manual-editor dirty
 * baseline, so an edit-then-revert round-trips to an identical serialization
 * and reads as clean rather than phantom-dirty.
 */
function normalizeCommandForSave(command: GeneratedCommand): {
  name: string;
  display_name: string;
  wakeword: string;
  actions: Record<string, string>[];
} {
  return {
    name: command.name,
    display_name: command.display_name,
    wakeword: command.wakeword,
    actions: command.actions.map((action) => {
      const normalized: Record<string, string> = { type: action.type };
      if (action.keys) normalized.keys = action.keys;
      if (action.url) normalized.url = action.url;
      if (action.cmd) normalized.cmd = action.cmd;
      else if (action.command) normalized.cmd = action.command;
      if (action.message) normalized.message = action.message;
      return normalized;
    }),
  };
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

const saveCommand = async (
  command: GeneratedCommand,
  editName?: string | null,
): Promise<void> => {
  // First fetch the current config
  const configRes = await fetch('/api/v1/config');
  if (!configRes.ok) {
    throw new Error('Failed to fetch current configuration');
  }
  const config = await configRes.json();

  const existing = { ...(config.commands || {}) };
  // When editing and the name changed, remove the old key so we don't orphan
  // the previous definition under its former name.
  if (editName && editName !== command.name && editName in existing) {
    delete existing[editName];
  }

  // Add the new command to the commands object
  const normalized = normalizeCommandForSave(command);
  const updatedCommands = {
    ...existing,
    [command.name]: {
      name: normalized.display_name,
      actions: normalized.actions,
      ...(normalized.wakeword ? { wakeword: normalized.wakeword } : {}),
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

const ACTION_HELP: Record<CommandAction['type'], string> = {
  keypress: 'A key chord sent to the active window. Combine modifiers with "+", e.g. ctrl+alt+t.',
  url: 'A URL to open in the default browser. Must include a scheme — https:// (or http://localhost for local development).',
  shell: 'A shell command run on the host. Unlike keypress, this executes directly — avoid destructive commands.',
  custom_message: 'A message spoken/displayed back to you. No system action is taken.',
};

const ActionField: React.FC<{
  action: CommandAction;
  onChange: (action: CommandAction) => void;
  onRemove: () => void;
  index: number;
}> = ({ action, onChange, onRemove, index }) => {
  const reduceMotion = useReducedMotionPref();
  const handleTypeChange = (type: CommandAction['type']) => {
    onChange({ type } as CommandAction);
  };

  const handleFieldChange = (field: string, value: string) => {
    onChange({ ...action, [field]: value });
  };

  const validationError = validateAction(action);
  // Stable id for the validation error so the relevant input(s) can point at it
  // via aria-describedby and screen readers associate the two.
  const errorId = `action-error-${index}`;
  const dangerWarning =
    action.type === 'shell'
      ? detectShellDanger(action.cmd || action.command || '')
      : action.type === 'url'
        ? detectUrlDanger(action.url || '')
        : null;

  return (
    <motion.div
      initial={reduceMotion ? false : { opacity: 0, x: -20 }}
      animate={reduceMotion ? undefined : { opacity: 1, x: 0 }}
      exit={reduceMotion ? undefined : { opacity: 0, x: 20 }}
      className={`card bg-base-200/50 border p-4 space-y-3 ${
        validationError
          ? 'border-error/50'
          : dangerWarning
            ? 'border-warning/50'
            : 'border-base-content/10'
      }`}
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
        <label className="label" htmlFor={`action-type-${index}`}>
          <span className="label-text text-sm">Type</span>
        </label>
        <select
          id={`action-type-${index}`}
          className="select select-sm select-bordered w-full"
          value={action.type}
          onChange={(e) => handleTypeChange(e.target.value as CommandAction['type'])}
        >
          <option value="keypress">Keypress</option>
          <option value="url">URL</option>
          <option value="shell">Shell Command</option>
          <option value="custom_message">Custom Message</option>
        </select>
        <span className="text-xs text-base-content/50 mt-1">{ACTION_HELP[action.type]}</span>
      </div>

      {action.type === 'keypress' && (
        <div className="form-control">
          <label className="label" htmlFor={`action-keys-${index}`}>
            <span className="label-text text-sm">Keys</span>
          </label>
          <input
            id={`action-keys-${index}`}
            type="text"
            className="input input-sm input-bordered"
            placeholder="e.g., ctrl+alt+t"
            value={action.keys || ''}
            aria-invalid={validationError ? true : undefined}
            aria-describedby={validationError ? errorId : undefined}
            onChange={(e) => handleFieldChange('keys', e.target.value)}
          />
        </div>
      )}

      {action.type === 'url' && (
        <div className="form-control">
          <label className="label" htmlFor={`action-url-${index}`}>
            <span className="label-text text-sm">URL</span>
          </label>
          <input
            id={`action-url-${index}`}
            type="text"
            className="input input-sm input-bordered"
            placeholder="https://example.com"
            value={action.url || ''}
            aria-invalid={validationError ? true : undefined}
            aria-describedby={validationError ? errorId : undefined}
            onChange={(e) => handleFieldChange('url', e.target.value)}
          />
        </div>
      )}

      {action.type === 'shell' && (
        <div className="form-control">
          <label className="label" htmlFor={`action-cmd-${index}`}>
            <span className="label-text text-sm">Command</span>
          </label>
          <input
            id={`action-cmd-${index}`}
            type="text"
            className="input input-sm input-bordered"
            placeholder="e.g., npm start"
            value={action.cmd || action.command || ''}
            aria-invalid={validationError ? true : undefined}
            aria-describedby={validationError ? errorId : undefined}
            onChange={(e) => handleFieldChange('cmd', e.target.value)}
          />
        </div>
      )}

      {action.type === 'custom_message' && (
        <div className="form-control">
          <label className="label" htmlFor={`action-message-${index}`}>
            <span className="label-text text-sm">Message</span>
          </label>
          <input
            id={`action-message-${index}`}
            type="text"
            className="input input-sm input-bordered"
            placeholder="Enter message to display"
            value={action.message || ''}
            aria-invalid={validationError ? true : undefined}
            aria-describedby={validationError ? errorId : undefined}
            onChange={(e) => handleFieldChange('message', e.target.value)}
          />
        </div>
      )}

      {validationError && (
        <p id={errorId} role="alert" className="text-error text-xs flex items-center gap-1">
          <AlertCircle size={16} />
          {validationError}
        </p>
      )}

      {dangerWarning && (
        <p className="text-warning text-xs flex items-center gap-1">
          <AlertTriangle size={16} />
          {dangerWarning}
        </p>
      )}
    </motion.div>
  );
};

// --- Main Page Component ---

export default function CommandAuthoringPage() {
  const reduceMotion = useReducedMotionPref();
  const navigate = useNavigate();
  const { addToast } = useToast();
  const [searchParams] = useSearchParams();
  const editName = searchParams.get('edit');
  const isEditing = Boolean(editName);

  useEffect(() => {
    document.title = (isEditing ? "Edit Command" : "Command Editor") + " | ChattyCommander";
  }, [isEditing]);

  const queryClient = useQueryClient();
  const [mode, setMode] = useState<'ai' | 'manual'>('ai');
  // Refs to the mode tabs so keyboard navigation can move focus to the newly
  // selected tab (focus follows selection, per the WAI-ARIA APG tabs pattern).
  const aiTabRef = useRef<HTMLButtonElement | null>(null);
  const manualTabRef = useRef<HTMLButtonElement | null>(null);
  const [description, setDescription] = useState('');
  const [generatedCommand, setGeneratedCommand] = useState<GeneratedCommand | null>(null);
  const [manualCommand, setManualCommand] = useState<GeneratedCommand>({
    name: '',
    display_name: '',
    wakeword: '',
    actions: [],
  });
  // The pristine baseline of the manual editor: the empty form for a new
  // command, or the loaded definition when editing (?edit=). Stored as the
  // SAME normalized serialization saveCommand produces, so an edit-then-revert
  // round-trips to an identical string and reads as clean (not phantom-dirty).
  // Used to derive a "has unsaved edits" signal without a separate dirty flag.
  const manualBaselineRef = useRef<string>(
    JSON.stringify(
      normalizeCommandForSave({ name: '', display_name: '', wakeword: '', actions: [] }),
    ),
  );
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formErrors, setFormErrors] = useState<Record<string, string>>({});
  // Existing command keys, fetched once, used to detect silent clobber.
  const [existingNames, setExistingNames] = useState<string[]>([]);
  // Element that had focus when the modal opened, so we can restore it on close.
  const modalTriggerRef = useRef<HTMLElement | null>(null);
  const modalRef = useRef<HTMLDivElement | null>(null);
  const cancelButtonRef = useRef<HTMLButtonElement | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchExistingCommandNames().then((names) => {
      if (!cancelled) setExistingNames(names);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  // When arriving with ?edit=<name>, load that command from config and
  // preload the manual editor so the existing definition can be modified.
  useEffect(() => {
    if (!editName) return;
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch('/api/v1/config');
        if (!res.ok) throw new Error('Failed to load configuration');
        const config = await res.json();
        const cmd = config?.commands?.[editName];
        if (!cmd) {
          if (!cancelled) setError(`Command "${editName}" was not found.`);
          return;
        }
        const actions: CommandAction[] = Array.isArray(cmd.actions)
          ? cmd.actions
          : cmd.action
            ? [cmd.action]
            : [];
        if (!cancelled) {
          const loaded: GeneratedCommand = {
            name: editName,
            display_name: cmd.name || editName,
            wakeword: cmd.wakeword || '',
            actions,
          };
          // The loaded definition is the pristine baseline, so preloading an
          // existing command for editing doesn't count as an unsaved edit.
          // Normalize through the same mapper saveCommand uses so an
          // edit-then-revert serializes back to this exact baseline.
          manualBaselineRef.current = JSON.stringify(normalizeCommandForSave(loaded));
          setManualCommand(loaded);
          setMode('manual');
        }
      } catch (e: unknown) {
        if (!cancelled) setError(e instanceof Error ? e.message : 'Failed to load command for editing');
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [editName]);

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

  // Whether the author has unsaved work in progress. True when the manual editor
  // diverges from its pristine baseline (new-command empty form, or the loaded
  // definition when editing), or when the AI flow has actual savable work — a
  // generated-but-unsaved command. A half-typed AI description with no generated
  // result is NOT dirty: it has nothing to save and shouldn't trip the
  // session-expiry deferral. Used to defer a mid-edit session expiry so real
  // edits aren't silently discarded.
  const isDirty = useMemo(() => {
    const manualDirty =
      JSON.stringify(normalizeCommandForSave(manualCommand)) !== manualBaselineRef.current;
    const aiDirty = generatedCommand !== null;
    return manualDirty || aiDirty;
  }, [manualCommand, generatedCommand]);
  useUnsavedChanges(isDirty);

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
    mutationFn: (command: GeneratedCommand) => saveCommand(command, editName),
    onSuccess: (_data, command) => {
      queryClient.invalidateQueries({ queryKey: ['commands'] });
      setShowConfirmModal(false);
      setFormErrors({});
      setError(null);
      addToast(
        isEditing
          ? `Command "${command.name}" updated.`
          : `Command "${command.name}" created.`,
        'success',
      );
      // Successful save is a destination, not a dead end: go back to the list.
      navigate('/commands');
    },
    onError: (err: Error) => {
      setError(err.message);
      setShowConfirmModal(false);
      addToast(err.message, 'error');
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

  const handleSave = useCallback(async (e?: React.MouseEvent<HTMLButtonElement>) => {
    // Remember the trigger so focus can be restored when the modal closes.
    modalTriggerRef.current = (e?.currentTarget as HTMLElement) ?? null;
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

    // Validate each action has required fields based on type (shared with the
    // inline per-action errors so AI and manual flows agree).
    for (let i = 0; i < commandToSave.actions.length; i++) {
      const actionError = validateAction(commandToSave.actions[i]);
      if (actionError) {
        setError(`Action ${i + 1}: ${actionError}`);
        return;
      }
    }

    // Prevent silently clobbering an existing command. When editing, colliding
    // with the command currently being edited is fine; any other collision is
    // a rename onto an existing key and must be confirmed/blocked. Re-fetch the
    // current command names here rather than trusting the mount snapshot, so a
    // command created in another tab/session after this page loaded is still
    // seen and not silently overwritten. Fall back to the mount snapshot if the
    // refresh fails, so a transient fetch error never weakens the guard.
    let names = existingNames;
    try {
      const fresh = await fetchExistingCommandNames();
      names = fresh;
      setExistingNames(fresh);
    } catch {
      // Keep the last-known names; the guard still applies.
    }
    const collidesWith = names.includes(commandToSave.name);
    const isSelf = isEditing && commandToSave.name === editName;
    if (collidesWith && !isSelf) {
      setError(
        `A command named "${commandToSave.name}" already exists. Choose a different name to avoid overwriting it.`,
      );
      return;
    }

    setShowConfirmModal(true);
    setError(null);
  }, [mode, generatedCommand, manualCommand, existingNames, isEditing, editName]);

  const closeModal = useCallback(() => {
    setShowConfirmModal(false);
    // Restore focus to whatever opened the dialog.
    modalTriggerRef.current?.focus?.();
  }, []);

  const confirmSave = useCallback(() => {
    const commandToSave = mode === 'ai' && generatedCommand ? generatedCommand : manualCommand;
    saveMutation.mutate(commandToSave);
  }, [mode, generatedCommand, manualCommand, saveMutation]);

  const handleCancel = useCallback(() => {
    navigate('/commands');
  }, [navigate]);

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

  // Keyboard navigation for the mode tablist (WAI-ARIA APG tabs pattern).
  // Arrow keys (and Home/End) move between tabs; selection follows focus, so
  // activating a tab also moves the visible focus to it via its ref.
  const handleTabKeyDown = useCallback(
    (event: React.KeyboardEvent<HTMLButtonElement>) => {
      const order: Array<'ai' | 'manual'> = ['ai', 'manual'];
      const refs: Record<'ai' | 'manual', React.RefObject<HTMLButtonElement>> = {
        ai: aiTabRef,
        manual: manualTabRef,
      };
      const currentIndex = order.indexOf(mode);
      let nextMode: 'ai' | 'manual' | null = null;
      switch (event.key) {
        case 'ArrowRight':
        case 'ArrowDown':
          nextMode = order[(currentIndex + 1) % order.length];
          break;
        case 'ArrowLeft':
        case 'ArrowUp':
          nextMode = order[(currentIndex - 1 + order.length) % order.length];
          break;
        case 'Home':
          nextMode = order[0];
          break;
        case 'End':
          nextMode = order[order.length - 1];
          break;
        default:
          return;
      }
      event.preventDefault();
      if (nextMode && nextMode !== mode) {
        setMode(nextMode);
      }
      // Focus follows selection — move focus to the (now) active tab.
      refs[nextMode].current?.focus();
    },
    [mode],
  );

  const currentCommand = useMemo(() => mode === 'ai' && generatedCommand ? generatedCommand : manualCommand, [mode, generatedCommand, manualCommand]);

  const dangerFlags = useMemo(() => collectDangerFlags(currentCommand.actions), [currentCommand]);

  // Modal accessibility: focus the Cancel button on open, trap Tab within the
  // dialog, close on Escape. Focus restoration is handled by closeModal.
  useEffect(() => {
    if (!showConfirmModal) return;
    cancelButtonRef.current?.focus();

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        closeModal();
        return;
      }
      if (event.key !== 'Tab') return;
      const dialog = modalRef.current;
      if (!dialog) return;
      const focusable = dialog.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])',
      );
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      const active = document.activeElement as HTMLElement | null;
      if (event.shiftKey && active === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && active === last) {
        event.preventDefault();
        first.focus();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [showConfirmModal, closeModal]);

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <motion.div
        initial={reduceMotion ? false : { opacity: 0, y: -20 }}
        animate={reduceMotion ? undefined : { opacity: 1, y: 0 }}
        className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4"
      >
        <div>
          <div className="text-sm breadcrumbs mb-2 text-base-content/60" aria-label="breadcrumbs">
            <ul>
              <li><Link to="/commands">Commands</Link></li>
              <li>{isEditing ? 'Edit Command' : 'Command Authoring'}</li>
            </ul>
          </div>
          <h1 className="text-3xl font-bold text-gradient-primary flex items-center gap-3">
            <Wand2 size={24} />
            {isEditing ? `Edit: ${editName}` : 'Command Authoring'}
          </h1>
          <p className="text-base-content/60 mt-1">
            {isEditing
              ? 'Update the actions, display name, and wake word for this command, then save your changes.'
              : 'Create new voice commands using AI assistance or manual configuration.'}
          </p>
        </div>

        {/* Mode Toggle */}
        <div className="tabs tabs-boxed bg-base-200" role="tablist" aria-label="Command Creation Mode">
          <button
            id="tab-ai-mode"
            ref={aiTabRef}
            role="tab"
            aria-selected={mode === 'ai'}
            aria-controls="ai-mode-panel"
            tabIndex={mode === 'ai' ? 0 : -1}
            className={`tab ${mode === 'ai' ? 'tab-active' : ''}`}
            onClick={() => setMode('ai')}
            onKeyDown={handleTabKeyDown}
          >
            <Sparkles size={16} className="mr-2" />
            AI Mode
          </button>
          <button
            id="tab-manual-mode"
            ref={manualTabRef}
            role="tab"
            aria-selected={mode === 'manual'}
            aria-controls="manual-mode-panel"
            tabIndex={mode === 'manual' ? 0 : -1}
            className={`tab ${mode === 'manual' ? 'tab-active' : ''}`}
            onClick={() => setMode('manual')}
            onKeyDown={handleTabKeyDown}
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
            initial={reduceMotion ? false : { opacity: 0, height: 0 }}
            animate={reduceMotion ? undefined : { opacity: 1, height: 'auto' }}
            exit={reduceMotion ? undefined : { opacity: 0, height: 0 }}
            className="alert alert-error"
          >
            <AlertCircle size={20} />
            <span>{error}</span>
            <button onClick={() => setError(null)} className="btn btn-ghost btn-sm btn-circle" aria-label="Dismiss error">
              <X size={16} />
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* AI Mode: Natural Language Input */}
      {mode === 'ai' && (
        <motion.div
          id="ai-mode-panel"
          role="tabpanel"
          aria-labelledby="tab-ai-mode"
          initial={reduceMotion ? false : { opacity: 0, y: 20 }}
          animate={reduceMotion ? undefined : { opacity: 1, y: 0 }}
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
                aria-label="Command Description"
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
                    <Loader2 size={16} className="animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Wand2 size={16} />
                    Generate Command
                  </>
                )}
              </button>
            </div>
          </div>
        </motion.div>
      )}

      {/* AI Mode: starter examples — shown before a command is generated so the
          page leads a first-time user with concrete ideas instead of empty space. */}
      {mode === 'ai' && !generatedCommand && (
        <div className="card glass-card" data-testid="ai-prompt-examples">
          <div className="card-body">
            <h2 className="card-title text-base flex items-center gap-2">
              <Lightbulb className="text-primary" size={18} />
              Need ideas? Start from an example
            </h2>
            <p className="text-sm text-base-content/60">
              Click one to drop it into the box above, then tweak it and generate.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-2">
              {AI_PROMPT_EXAMPLES.map((ex) => (
                <button
                  key={ex.title}
                  type="button"
                  className="text-left p-4 rounded-xl bg-base-200/40 border border-base-content/10 hover:border-primary/40 hover:bg-base-200/70 transition-colors"
                  onClick={() => setDescription(ex.prompt)}
                >
                  <p className="font-medium text-sm flex items-center gap-2">
                    <Sparkles size={14} className="text-primary/70 shrink-0" />
                    {ex.title}
                  </p>
                  <p className="text-xs text-base-content/60 mt-1">{ex.prompt}</p>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Generated Command Preview */}
      {mode === 'ai' && generatedCommand && (
        <motion.div
          initial={reduceMotion ? false : { opacity: 0, scale: 0.95 }}
          animate={reduceMotion ? undefined : { opacity: 1, scale: 1 }}
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

            <Collapse
              title="Command details"
              defaultOpen
              badge={
                <span className="badge badge-sm" data-testid="generated-command-summary">
                  {generatedCommand.name} · {generatedCommand.actions.length}{" "}
                  {generatedCommand.actions.length === 1 ? "action" : "actions"}
                </span>
              }
              className="mt-4"
              data-testid="generated-command-details"
            >
              <div className="space-y-4">
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
            </Collapse>

            <div className="card-actions justify-end mt-4 gap-2">
              <button className="btn btn-ghost" onClick={handleCancel}>
                Cancel
              </button>
              <button
                className="btn btn-primary"
                onClick={handleSave}
                disabled={saveMutation.isPending}
              >
                {saveMutation.isPending ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save size={16} />
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
          id="manual-mode-panel"
          role="tabpanel"
          aria-labelledby="tab-manual-mode"
          initial={reduceMotion ? false : { opacity: 0, y: 20 }}
          animate={reduceMotion ? undefined : { opacity: 1, y: 0 }}
          className="card glass-card"
        >
          <div className="card-body">
            <h2 className="card-title flex items-center gap-2">
              <Terminal className="text-primary" size={20} />
              Manual Command Editor
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
              <div className="form-control">
                <label className="label" htmlFor="cmd-name">
                  <span className="label-text">Command Name (snake_case)</span>
                </label>
                <input
                  id="cmd-name"
                  type="text"
                  className={`input input-bordered${formErrors.name ? ' input-error' : ''}`}
                  placeholder="my_command"
                  value={manualCommand.name}
                  aria-describedby="cmd-name-help"
                  onChange={(e) =>
                    setManualCommand((prev) => ({ ...prev, name: e.target.value }))
                  }
                  onBlur={(e) => validateField('name', e.target.value)}
                />
                <span id="cmd-name-help" className="text-xs text-base-content/50 mt-1">
                  Unique internal id used in config and the API. Not spoken.
                </span>
                {formErrors.name && (
                  <span className="text-error text-xs mt-1">{formErrors.name}</span>
                )}
              </div>

              <div className="form-control">
                <label className="label" htmlFor="cmd-display-name">
                  <span className="label-text">Display Name</span>
                </label>
                <input
                  id="cmd-display-name"
                  type="text"
                  className={`input input-bordered${formErrors.display_name ? ' input-error' : ''}`}
                  placeholder="My Command"
                  value={manualCommand.display_name}
                  onChange={(e) =>
                    setManualCommand((prev) => ({ ...prev, display_name: e.target.value }))
                  }
                  onBlur={(e) => validateField('display_name', e.target.value)}
                />
                {formErrors.display_name && (
                  <span className="text-error text-xs mt-1">{formErrors.display_name}</span>
                )}
              </div>

              <div className="form-control">
                <label className="label" htmlFor="cmd-wakeword">
                  <span className="label-text">Wakeword</span>
                </label>
                <input
                  id="cmd-wakeword"
                  type="text"
                  className={`input input-bordered${formErrors.wakeword ? ' input-error' : ''}`}
                  placeholder="Trigger phrase"
                  value={manualCommand.wakeword}
                  aria-describedby="cmd-wakeword-help"
                  onChange={(e) =>
                    setManualCommand((prev) => ({ ...prev, wakeword: e.target.value }))
                  }
                  onBlur={(e) => validateField('wakeword', e.target.value)}
                />
                <span id="cmd-wakeword-help" className="text-xs text-base-content/50 mt-1">
                  The spoken phrase that triggers this command.
                </span>
                {formErrors.wakeword && (
                  <span className="text-error text-xs mt-1">{formErrors.wakeword}</span>
                )}
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
                  <Terminal size={24} className="mx-auto mb-2 opacity-50" />
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

            <div className="card-actions justify-end mt-6 gap-2">
              <button className="btn btn-ghost" onClick={handleCancel}>
                Cancel
              </button>
              <button
                className="btn btn-primary"
                onClick={handleSave}
                disabled={saveMutation.isPending || manualCommand.actions.length === 0 || hasFormErrors}
              >
                {saveMutation.isPending ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save size={16} />
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
          initial={reduceMotion ? false : { opacity: 0 }}
          animate={reduceMotion ? undefined : { opacity: 1 }}
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
              initial={reduceMotion ? false : { opacity: 0 }}
              animate={reduceMotion ? undefined : { opacity: 1 }}
              exit={reduceMotion ? undefined : { opacity: 0 }}
              className="fixed inset-0 bg-black/50 z-40"
              onClick={closeModal}
            />
            <motion.div
              initial={reduceMotion ? false : { opacity: 0, scale: 0.9 }}
              animate={reduceMotion ? undefined : { opacity: 1, scale: 1 }}
              exit={reduceMotion ? undefined : { opacity: 0, scale: 0.9 }}
              className="fixed inset-0 flex items-center justify-center z-50 p-4"
              role="dialog"
              aria-modal="true"
              aria-labelledby="confirm-modal-title"
              ref={modalRef}
            >
              <div className="card glass-card max-w-lg w-full bg-base-100 shadow-2xl">
                <div className="card-body">
                  <div className="flex items-center gap-3 text-warning mb-4">
                    <Shield size={24} />
                    <h3 id="confirm-modal-title" className="text-xl font-bold">
                      {isEditing ? 'Confirm Command Changes' : 'Confirm Command Creation'}
                    </h3>
                  </div>

                  <div className="alert alert-warning mb-4">
                    <AlertCircle size={16} />
                    <span className="text-sm">
                      Commands can execute shell commands and open URLs. Please review carefully
                      before saving.
                    </span>
                  </div>

                  {dangerFlags.length > 0 && (
                    <div className="alert alert-error mb-4 flex-col items-start">
                      <div className="flex items-center gap-2 font-semibold">
                        <AlertTriangle size={16} />
                        Potentially risky actions flagged
                      </div>
                      <ul className="list-disc list-inside text-sm mt-1 space-y-1">
                        {dangerFlags.map((flag) => (
                          <li key={flag.index}>
                            <span className="font-mono">
                              Action {flag.index + 1} ({flag.type}): {flag.detail}
                            </span>
                            <span className="block opacity-90">{flag.warning}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

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
                      onClick={closeModal}
                      ref={cancelButtonRef}
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
