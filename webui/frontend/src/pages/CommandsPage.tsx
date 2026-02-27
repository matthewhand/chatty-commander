import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  TerminalSquare,
  Settings2,
  Plus,
  Edit3,
  Trash2,
  Save,
  X,
  Keyboard,
  Globe,
  MessageSquare,
  Terminal,
} from "lucide-react";
import { apiService } from "../services/apiService";

interface CommandAction {
  action: "keypress" | "url" | "shell" | "custom_message" | "voice_chat";
  keys?: string;
  url?: string;
  cmd?: string;
  message?: string;
  [key: string]: any;
}

interface Command {
  id: string;
  action: CommandAction;
}

export default function CommandsPage() {
  const [commands, setCommands] = useState<Command[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [config, setConfig] = useState<any>(null);

  // Edit/Create State
  const [editingId, setEditingId] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [editForm, setEditForm] = useState<{
    id: string;
    actionType: string;
    payload: string;
  }>({ id: "", actionType: "keypress", payload: "" });

  const fetchConfig = async () => {
    try {
      setLoading(true);
      const data = await apiService.getConfig();
      setConfig(data);
      if (data && data.commands) {
        const cmdList = Object.entries(data.commands).map(([key, val]: [string, any]) => ({
          id: key,
          action: val,
        }));
        setCommands(cmdList);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load commands");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConfig();
  }, []);

  const handleSave = async () => {
    if (!config) return;

    try {
      const newCommands = { ...config.commands };
      const { id, actionType, payload } = editForm;

      // Construct action object based on type
      let actionObj: any = { action: actionType };
      if (actionType === "keypress") actionObj.keys = payload;
      else if (actionType === "url") actionObj.url = payload;
      else if (actionType === "shell") actionObj.cmd = payload; // Note: 'cmd' matches backend executor
      else if (actionType === "custom_message") actionObj.message = payload;

      // If renaming (creating new key, deleting old), handle that
      if (editingId && editingId !== id) {
        delete newCommands[editingId];
      }

      newCommands[id] = actionObj;

      // Optimistic update
      const updatedConfig = { ...config, commands: newCommands };
      setConfig(updatedConfig);

      const cmdList = Object.entries(newCommands).map(([key, val]: [string, any]) => ({
        id: key,
        action: val,
      }));
      setCommands(cmdList);

      // Persist
      await apiService.updateConfig({ commands: newCommands });

      // Reset state
      setEditingId(null);
      setIsCreating(false);
    } catch (err: any) {
      setError(err.message || "Failed to save command");
      fetchConfig(); // Revert on error
    }
  };

  const handleDelete = async (id: string) => {
    if (!config) return;
    if (!window.confirm(`Are you sure you want to delete command "${id}"?`)) return;

    try {
      const newCommands = { ...config.commands };
      delete newCommands[id];

      // Optimistic update
      const updatedConfig = { ...config, commands: newCommands };
      setConfig(updatedConfig);
      const cmdList = Object.entries(newCommands).map(([key, val]: [string, any]) => ({
        id: key,
        action: val,
      }));
      setCommands(cmdList);

      await apiService.updateConfig({ commands: newCommands });
    } catch (err: any) {
      setError(err.message || "Failed to delete command");
      fetchConfig();
    }
  };

  const startEdit = (cmd: Command) => {
    let payload = "";
    if (cmd.action.action === "keypress") payload = cmd.action.keys || "";
    else if (cmd.action.action === "url") payload = cmd.action.url || "";
    else if (cmd.action.action === "shell") payload = cmd.action.cmd || cmd.action.shell || "";
    else if (cmd.action.action === "custom_message") payload = cmd.action.message || "";

    setEditForm({
      id: cmd.id,
      actionType: cmd.action.action || "keypress",
      payload,
    });
    setEditingId(cmd.id);
    setIsCreating(false);
  };

  const startCreate = () => {
    setEditForm({ id: "", actionType: "keypress", payload: "" });
    setIsCreating(true);
    setEditingId(null);
  };

  const cancelEdit = () => {
    setEditingId(null);
    setIsCreating(false);
  };

  const getIconForAction = (type: string) => {
    switch (type) {
      case "keypress": return <Keyboard size={16} />;
      case "url": return <Globe size={16} />;
      case "shell": return <Terminal size={16} />;
      case "custom_message": return <MessageSquare size={16} />;
      default: return <TerminalSquare size={16} />;
    }
  };

  if (loading) return <div className="flex justify-center p-10"><span className="loading loading-spinner loading-lg"></span></div>;

  return (
    <div className="space-y-6 pb-20">
      {/* Header Section */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4"
      >
        <div>
          <h1 className="text-3xl font-bold text-gradient-primary">Commands</h1>
          <p className="text-base-content/60 mt-1">
            Manage voice commands and their actions.
          </p>
        </div>
        {!isCreating && !editingId && (
          <button className="btn btn-primary" onClick={startCreate}>
            <Plus size={18} />
            New Command
          </button>
        )}
      </motion.div>

      {error && (
        <div className="alert alert-error shadow-lg">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="btn btn-xs btn-ghost"><X size={14}/></button>
        </div>
      )}

      <div className="divider divider-accent"></div>

      {/* Editor Form */}
      <AnimatePresence>
        {(isCreating || editingId) && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="card bg-base-200 border border-primary/20 mb-8 overflow-hidden"
          >
            <div className="card-body">
              <h3 className="card-title text-primary">
                {isCreating ? "Create New Command" : "Edit Command"}
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
                <div className="form-control">
                  <label className="label">
                    <span className="label-text font-bold">Command Name (ID)</span>
                  </label>
                  <input
                    type="text"
                    placeholder="e.g., lights_on"
                    className="input input-bordered w-full"
                    value={editForm.id}
                    onChange={(e) => setEditForm({ ...editForm, id: e.target.value })}
                    disabled={!!editingId} // Prevent ID change on edit for simplicity, or allow if you want rename logic
                  />
                  <label className="label">
                    <span className="label-text-alt opacity-60">Unique identifier for this command.</span>
                  </label>
                </div>

                <div className="form-control">
                  <label className="label">
                    <span className="label-text font-bold">Action Type</span>
                  </label>
                  <select
                    className="select select-bordered w-full"
                    value={editForm.actionType}
                    onChange={(e) => setEditForm({ ...editForm, actionType: e.target.value })}
                  >
                    <option value="keypress">Keypress Simulation</option>
                    <option value="url">HTTP Request (Webhook)</option>
                    <option value="shell">Shell Command</option>
                    <option value="custom_message">Custom Message / Echo</option>
                  </select>
                </div>

                <div className="form-control md:col-span-2">
                  <label className="label">
                    <span className="label-text font-bold">
                      {editForm.actionType === "keypress" ? "Keys to Press" :
                       editForm.actionType === "url" ? "Target URL" :
                       editForm.actionType === "shell" ? "Command to Execute" :
                       "Message Text"}
                    </span>
                  </label>
                  <input
                    type="text"
                    placeholder={
                      editForm.actionType === "keypress" ? "e.g., ctrl+alt+t" :
                      editForm.actionType === "url" ? "http://..." :
                      editForm.actionType === "shell" ? "notify-send 'Hello'" :
                      "Hello World"
                    }
                    className="input input-bordered w-full font-mono text-sm"
                    value={editForm.payload}
                    onChange={(e) => setEditForm({ ...editForm, payload: e.target.value })}
                  />
                </div>
              </div>
              <div className="card-actions justify-end mt-4">
                <button className="btn btn-ghost" onClick={cancelEdit}>Cancel</button>
                <button className="btn btn-primary" onClick={handleSave} disabled={!editForm.id || !editForm.payload}>
                  <Save size={18} />
                  Save Command
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Commands Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <AnimatePresence>
          {commands.map((cmd, idx) => (
            <motion.div
              key={cmd.id}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: idx * 0.05 }}
              className={`card glass-card overflow-hidden ${editingId === cmd.id ? 'ring-2 ring-primary' : ''}`}
            >
              <div className="card-body p-0">
                {/* Command Header */}
                <div className="p-6 bg-base-200/50 border-b border-base-content/10 flex justify-between items-start">
                  <div className="flex gap-3 items-center">
                    <div className="p-3 rounded-xl bg-primary/20 text-primary">
                      {getIconForAction(cmd.action.action)}
                    </div>
                    <div>
                      <h2 className="card-title text-xl mb-1 font-mono">{cmd.id}</h2>
                      <div className="badge badge-sm badge-outline uppercase text-[10px] tracking-wider font-bold opacity-70">
                        {cmd.action.action}
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-1">
                    <div className="tooltip tooltip-bottom" data-tip="Edit">
                      <button
                        className="btn btn-ghost btn-sm btn-circle"
                        onClick={() => startEdit(cmd)}
                        disabled={!!editingId || isCreating}
                      >
                        <Edit3 size={16} />
                      </button>
                    </div>
                    <div className="tooltip tooltip-bottom tooltip-error" data-tip="Delete">
                      <button
                        className="btn btn-ghost btn-sm btn-circle text-error"
                        onClick={() => handleDelete(cmd.id)}
                        disabled={!!editingId || isCreating}
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                </div>

                {/* Details Section */}
                <div className="p-6 space-y-4">
                  <div>
                    <h3 className="text-xs font-bold uppercase tracking-wider text-base-content/40 mb-2 flex items-center gap-2">
                      <Settings2 size={12} /> Configuration
                    </h3>
                    <div className="bg-base-100 rounded-lg p-3 border border-base-content/10 font-mono text-xs break-all">
                       {cmd.action.keys || cmd.action.url || cmd.action.cmd || cmd.action.message || cmd.action.shell || <span className="italic opacity-50">No payload</span>}
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {commands.length === 0 && !loading && (
            <div className="col-span-full text-center py-20 opacity-50">
                <TerminalSquare size={48} className="mx-auto mb-4" />
                <p>No commands configured.</p>
            </div>
        )}
      </div>
    </div>
  );
}
