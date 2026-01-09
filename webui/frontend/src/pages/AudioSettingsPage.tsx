import React, { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  Save as SaveIcon,
  Mic as MicIcon,
  Volume2 as VolumeUpIcon,
  Headphones as HeadphonesIcon,
} from "lucide-react";

// Placeholder services for audio devices
const getAudioDevices = async () => {
  // Simulate fetching devices
  console.log("Fetching audio devices...");
  return {
    input: ["Default Microphone", "External USB Mic", "Webcam Mic"],
    output: ["Default Speakers", "Headphones", "HDMI Output"],
  };
};
const saveAudioSettings = async (settings: any) => {
  // Placeholder save
  console.log("Saving audio settings:", settings);
  return new Promise((resolve) => setTimeout(resolve, 1000));
};

const AudioSettingsPage: React.FC = () => {
  const [inputDevice, setInputDevice] = useState("");
  const [outputDevice, setOutputDevice] = useState("");

  const { data: devices } = useQuery({
    queryKey: ["audioDevices"],
    queryFn: getAudioDevices,
  });

  const mutation = useMutation({
    mutationFn: saveAudioSettings,
  });

  const handleSave = () => {
    mutation.mutate({ inputDevice, outputDevice });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-3 bg-secondary/10 rounded-xl text-secondary">
          <HeadphonesIcon size={32} />
        </div>
        <div>
          <h2 className="text-3xl font-bold bg-gradient-to-r from-secondary to-primary bg-clip-text text-transparent">
            Audio Settings
          </h2>
          <p className="text-base-content/60">Configure inputs and outputs</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        {/* Input Device Card */}
        <div className="card bg-base-100 shadow-xl border border-base-content/10">
          <div className="card-body">
            <h3 className="card-title text-primary">
              <MicIcon size={20} /> Input Device
            </h3>
            <p className="text-sm opacity-70 mb-4">Select microphone source.</p>

            <div className="form-control w-full">
              <select
                className="select select-bordered w-full select-primary"
                value={inputDevice}
                onChange={(e) => setInputDevice(e.target.value)}
              >
                <option value="" disabled>Select device...</option>
                {devices?.input.map((dev) => (
                  <option key={dev} value={dev}>{dev}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Output Device Card */}
        <div className="card bg-base-100 shadow-xl border border-base-content/10">
          <div className="card-body">
            <h3 className="card-title text-secondary">
              <VolumeUpIcon size={20} /> Output Device
            </h3>
            <p className="text-sm opacity-70 mb-4">Select playback endpoint.</p>

            <div className="form-control w-full">
              <select
                className="select select-bordered w-full select-secondary"
                value={outputDevice}
                onChange={(e) => setOutputDevice(e.target.value)}
              >
                <option value="" disabled>Select device...</option>
                {devices?.output.map((dev) => (
                  <option key={dev} value={dev}>{dev}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

      </div>

      <div className="flex justify-end pt-4">
        <button
          className={`btn btn-accent gap-2 ${mutation.isPending ? 'loading' : ''}`}
          onClick={handleSave}
          disabled={mutation.isPending}
        >
          <SaveIcon size={20} />
          {mutation.isPending ? "Saving..." : "Apply Settings"}
        </button>
      </div>
    </div>
  );
};

export default AudioSettingsPage;
