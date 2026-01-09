import React, { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Save as SaveIcon,
  Settings as SettingsIcon,
  Tune as TuneIcon,
} from "@mui/icons-material";

// Assuming a service for saving config
const saveConfig = async (config: any) => {
  // Placeholder API call
  console.log("Saving config:", config);
  return new Promise((resolve) => setTimeout(resolve, 1000));
};

const ConfigurationPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [config, setConfig] = useState({
    apiKey: "",
    enableVoice: true,
    theme: "dark",
  });

  const mutation = useMutation({
    mutationFn: saveConfig,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["config"] });
    },
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setConfig({ ...config, [e.target.name]: e.target.value });
  };

  const handleSwitch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setConfig({ ...config, [e.target.name]: e.target.checked });
  };

  const handleSubmit = () => {
    mutation.mutate(config);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-3 bg-primary/10 rounded-xl text-primary">
          <SettingsIcon sx={{ fontSize: 32 }} />
        </div>
        <div>
          <h2 className="text-3xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
            Configuration
          </h2>
          <p className="text-base-content/60">Manage your application settings</p>
        </div>
      </div>

      <div className="card bg-base-100 shadow-xl border border-base-content/10 overflow-visible">
        <div className="card-body p-0">

          {/* General Settings Section */}
          <div className="p-6 border-b border-base-content/10">
            <h3 className="text-lg font-bold flex items-center gap-2 mb-4 text-base-content">
              <TuneIcon className="w-5 h-5 text-primary" />
              General Settings
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="form-control w-full">
                <label className="label">
                  <span className="label-text font-medium">API Key</span>
                </label>
                <input
                  type="password"
                  name="apiKey"
                  placeholder="sk-..."
                  className="input input-bordered w-full focus:input-primary transition-all"
                  value={config.apiKey}
                  onChange={handleChange}
                />
                <label className="label">
                  <span className="label-text-alt text-base-content/50">External service key</span>
                </label>
              </div>

              <div className="form-control w-full">
                <label className="label">
                  <span className="label-text font-medium">Theme</span>
                </label>
                <select
                  name="theme"
                  className="select select-bordered w-full focus:select-primary"
                  value={config.theme}
                  onChange={handleChange}
                >
                  <option value="dark">Dark</option>
                  <option value="light">Light</option>
                </select>
                <label className="label">
                  <span className="label-text-alt text-base-content/50">Application appearance</span>
                </label>
              </div>
            </div>
          </div>

          {/* Feature Toggles */}
          <div className="p-6 bg-base-200/30">
            <div className="form-control">
              <label className="label cursor-pointer justify-start gap-4">
                <input
                  type="checkbox"
                  className="toggle toggle-primary"
                  checked={config.enableVoice}
                  onChange={handleSwitch}
                  name="enableVoice"
                />
                <div className="flex flex-col">
                  <span className="label-text font-medium text-base">Enable Voice Commands</span>
                  <span className="label-text-alt text-base-content/50">Allow microphone input for commands</span>
                </div>
              </label>
            </div>
          </div>

          {/* Action Footer */}
          <div className="p-4 bg-base-300/50 rounded-b-xl flex justify-end">
            <button
              className={`btn btn-primary gap-2 ${mutation.isPending ? 'loading' : ''}`}
              onClick={handleSubmit}
              disabled={mutation.isPending}
            >
              <SaveIcon />
              {mutation.isPending ? "Saving..." : "Save Changes"}
            </button>
          </div>

        </div>
      </div>
    </div>
  );
};

export default ConfigurationPage;
