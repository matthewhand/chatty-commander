import React from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchAgentStatus, Agent } from "../services/api";
import { Activity as AssessmentIcon } from "lucide-react";

const AgentStatusPage: React.FC = () => {
  const { data, isLoading, isError, error } = useQuery<Agent[]>({
    queryKey: ["agentStatus"],
    queryFn: fetchAgentStatus,
    refetchInterval: 30000,
    retry: 2,
  });

  const getStatusColor = (status: Agent["status"]) => {
    switch (status) {
      case "online": return "badge-success";
      case "offline": return "badge-ghost";
      case "error": return "badge-error";
      case "processing": return "badge-warning";
      default: return "badge-ghost";
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <span className="loading loading-spinner loading-lg text-primary"></span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-3 bg-error/10 rounded-xl text-error">
          <AssessmentIcon size={32} />
        </div>
        <div>
          <h2 className="text-3xl font-bold bg-gradient-to-r from-error to-warning bg-clip-text text-transparent">
            Agent Status
          </h2>
          <p className="text-base-content/60">Monitor agent health and logs</p>
        </div>
      </div>

      {isError && (
        <div className="alert alert-error shadow-lg">
          <svg xmlns="http://www.w3.org/2000/svg" className="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          <span>{(error as Error)?.message || "Failed to fetch agent status."}</span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {data?.map((agent) => (
          <div key={agent.id} className="card bg-base-100 shadow-xl border border-base-content/10">
            <div className="card-body">
              <div className="flex justify-between items-center mb-4">
                <h3 className="card-title text-xl font-bold">{agent.name}</h3>
                <div className={`badge ${getStatusColor(agent.status)} badge-lg font-bold uppercase`}>
                  {agent.status}
                </div>
              </div>

              {agent.error && (
                <div className="alert alert-error shadow-sm text-xs py-2 my-2">
                  <span>{agent.error}</span>
                </div>
              )}

              <div className="mockup-code bg-base-300 text-xs mt-4 before:hidden">
                <div className="px-4 py-2 space-y-2">
                  <div className="flex flex-col">
                    <span className="text-base-content/50 uppercase text-[10px] tracking-wider">Last Sent</span>
                    <span className="font-mono text-primary">{agent.lastMessageSent || "-"}</span>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-base-content/50 uppercase text-[10px] tracking-wider">Last Received</span>
                    <span className="font-mono text-secondary">{agent.lastMessageReceived || "-"}</span>
                  </div>
                  <div className="flex flex-col">
                    <span className="text-base-content/50 uppercase text-[10px] tracking-wider">Content</span>
                    <span className="font-mono text-base-content/70 break-words">{agent.lastMessageContent || "-"}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AgentStatusPage;
