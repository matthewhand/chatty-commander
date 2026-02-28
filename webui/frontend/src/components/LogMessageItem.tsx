import React from "react";
import {
  Terminal,
  Activity,
  AlertCircle,
  Cpu,
  CheckCircle2,
  Info
} from "lucide-react";

export interface LogMessage {
  id: string;
  type: "command" | "system" | "state" | "error" | "info" | "connection";
  content: string;
  timestamp: Date;
  metadata?: any;
}

interface LogMessageProps {
  message: LogMessage;
}

export const LogMessageItem: React.FC<LogMessageProps> = ({ message }) => {
  const getIcon = () => {
    switch (message.type) {
      case "command": return <Terminal size={14} className="text-accent" />;
      case "system": return <Activity size={14} className="text-info" />;
      case "state": return <Cpu size={14} className="text-secondary" />;
      case "error": return <AlertCircle size={14} className="text-error" />;
      case "connection": return <CheckCircle2 size={14} className="text-success" />;
      default: return <Info size={14} className="text-base-content/50" />;
    }
  };

  const getColors = () => {
    switch (message.type) {
      case "command": return "border-l-accent bg-accent/5";
      case "system": return "border-l-info bg-info/5";
      case "state": return "border-l-secondary bg-secondary/5";
      case "error": return "border-l-error bg-error/10";
      case "connection": return "border-l-success bg-success/5";
      default: return "border-l-base-content/20 bg-base-200/50";
    }
  };

  return (
    <div className={`flex gap-3 p-2 rounded-r border-l-2 text-xs mb-1 animate-in fade-in slide-in-from-bottom-1 duration-300 ${getColors()}`}>
      <div className="mt-0.5 flex-shrink-0 opacity-70">
        {getIcon()}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex justify-between items-baseline gap-2">
          <span className="font-mono text-[10px] opacity-40">
            {message.timestamp.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })}
          </span>
        </div>
        <p className="break-words font-mono leading-relaxed opacity-90">
          {message.content}
        </p>
      </div>
    </div>
  );
};
