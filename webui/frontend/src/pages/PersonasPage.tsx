import React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiService } from "../services/apiService";
import { Groups as GroupsIcon, Person as PersonIcon, Star as StarIcon } from "@mui/icons-material";

const PersonasPage: React.FC = () => {
  const queryClient = useQueryClient();

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["advisorPersonas"],
    queryFn: () => apiService.getAdvisorPersonas(),
  });

  const switchMutation = useMutation({
    mutationFn: ({
      contextKey,
      personaId,
    }: {
      contextKey: string;
      personaId: string;
    }) => apiService.switchAdvisorPersona(contextKey, personaId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["advisorContextStats"] });
    },
  });

  const { data: stats } = useQuery({
    queryKey: ["advisorContextStats"],
    queryFn: () => apiService.getAdvisorContextStats(),
  });

  const personas = data?.personas || [];

  // Hardcoded for demo
  const sampleContextKey = "discord:c1:u1";

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <span className="loading loading-spinner loading-lg text-primary"></span>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="alert alert-error shadow-lg">
        <svg xmlns="http://www.w3.org/2000/svg" className="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
        <span>{(error as Error)?.message || "Failed to load personas"}</span>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-3 bg-accent/10 rounded-xl text-accent">
          <GroupsIcon sx={{ fontSize: 32 }} />
        </div>
        <div>
          <h2 className="text-3xl font-bold bg-gradient-to-r from-accent to-secondary bg-clip-text text-transparent">
            Personas
          </h2>
          <p className="text-base-content/60">Manage AI Advisor personalities</p>
        </div>
      </div>

      {/* Stats Overview */}
      {stats && (
        <div className="stats shadow bg-base-100 border border-base-content/10 w-full md:w-auto">
          <div className="stat">
            <div className="stat-title">Active Contexts</div>
            <div className="stat-value text-primary">{stats.total_contexts}</div>
            <div className="stat-desc">Sessions using personas</div>
          </div>
        </div>
      )}

      {/* Personas Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {personas.map((p: any) => (
          <div key={p.id} className="card bg-base-100 shadow-xl border border-base-content/10 transition-all hover:border-primary/50 hover:shadow-2xl hover:-translate-y-1">
            <div className="card-body">
              <div className="flex justify-between items-start">
                <div className="flex items-center gap-2">
                  <div className="avatar placeholder">
                    <div className="bg-neutral text-neutral-content rounded-full w-10">
                      <span className="text-lg">{p.name.charAt(0)}</span>
                    </div>
                  </div>
                  <div>
                    <h3 className="card-title text-base">{p.name}</h3>
                    <span className="text-xs text-base-content/50">ID: {p.id}</span>
                  </div>
                </div>
                {p.is_default && (
                  <div className="badge badge-primary gap-1">
                    <StarIcon fontSize="small" /> Default
                  </div>
                )}
              </div>

              {p.system_prompt && (
                <div
                  className="tooltip tooltip-bottom w-full"
                  data-tip={p.system_prompt}
                >
                  <div className="mt-4 p-3 bg-base-200 rounded-lg text-sm text-base-content/70 italic text-left truncate">
                    "{p.system_prompt}"
                  </div>
                </div>
              )}

              <div className="card-actions justify-end mt-4">
                <button
                  className="btn btn-sm btn-outline btn-accent"
                  onClick={() => switchMutation.mutate({ contextKey: sampleContextKey, personaId: p.id })}
                  disabled={switchMutation.isPending}
                >
                  Apply to Sample
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PersonasPage;
