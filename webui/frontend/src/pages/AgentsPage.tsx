import React, { useEffect, useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Bot,
  Plus,
  Trash2,
  RefreshCw,
  Search,
  Info,
  Zap,
  ArrowRightLeft,
  Cpu,
} from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  fetchAgentBlueprints,
  createAgentBlueprint,
  deleteAgentBlueprint,
  type AgentBlueprint,
  type CreateAgentPayload,
} from '../services/api';
import {
  Button,
  Card,
  Alert,
  Badge,
  Input,
  Textarea,
  EmptyState,
  Accordion,
  Avatar,
  Tooltip,
  Drawer,
  SkeletonCard,
  SkeletonText,
  Skeleton,
  PageHeader,
} from '../components/DaisyUI';
import { ConfirmModal } from '../components/DaisyUI/Modal';
import Modal from '../components/DaisyUI/Modal';
import { Timeline } from '../components/DaisyUI/Timeline';
import type { AccordionItem } from '../components/DaisyUI/Accordion';
import type { TimelineItem } from '../components/DaisyUI/Timeline';

function getInitials(name: string): string {
  return name
    .split(/[\s_-]+/)
    .map((w) => w[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
}

// Deterministic colour based on agent name
const STATUS_BADGE: Record<string, { variant: 'success' | 'error' | 'warning' | 'neutral'; label: string }> = {
  online: { variant: 'success', label: 'Online' },
  offline: { variant: 'neutral', label: 'Offline' },
  error: { variant: 'error', label: 'Error' },
};

function pseudoStatus(id: string): 'online' | 'offline' | 'error' {
  const hash = id.split('').reduce((a, c) => a + c.charCodeAt(0), 0);
  return (['online', 'offline', 'error'] as const)[hash % 3];
}

// Placeholder timeline items for agent activity
function placeholderTimeline(name: string): TimelineItem[] {
  return [
    { title: 'Created', description: `${name} blueprint registered`, time: 'Just now', status: 'success', side: 'start' as const },
    { title: 'Idle', description: 'Waiting for first handoff', time: '-', status: 'pending', side: 'end' as const },
  ];
}

const EMPTY_FORM: CreateAgentPayload = {
  name: '',
  description: '',
  persona_prompt: '',
  capabilities: [],
  team_role: null,
  handoff_triggers: [],
};

export default function AgentsPage() {
  useEffect(() => {
    document.title = 'Agents | ChattyCommander';
  }, []);

  const queryClient = useQueryClient();

  // --- data fetching ---
  const { data: agents, isLoading, isError, refetch } = useQuery<AgentBlueprint[]>({
    queryKey: ['agentBlueprints'],
    queryFn: fetchAgentBlueprints,
  });

  // --- mutations ---
  const createMutation = useMutation({
    mutationFn: createAgentBlueprint,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agentBlueprints'] });
      setCreateModalOpen(false);
      setForm({ ...EMPTY_FORM });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteAgentBlueprint,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agentBlueprints'] });
      setPendingDelete(null);
    },
  });

  // --- local state ---
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<AgentBlueprint | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<AgentBlueprint | null>(null);
  const [form, setForm] = useState<CreateAgentPayload>({ ...EMPTY_FORM });

  // Debounce search
  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(searchQuery), 300);
    return () => clearTimeout(t);
  }, [searchQuery]);

  const agentsList = useMemo(() => agents ?? [], [agents]);

  const filteredAgents = useMemo(() => {
    if (!debouncedSearch.trim()) return agentsList;
    const q = debouncedSearch.toLowerCase();
    return agentsList.filter(
      (a) =>
        a.name.toLowerCase().includes(q) ||
        a.description.toLowerCase().includes(q) ||
        (a.team_role && a.team_role.toLowerCase().includes(q)),
    );
  }, [agentsList, debouncedSearch]);

  const isEmpty = !isLoading && agentsList.length === 0;

  // --- handlers ---
  const handleCreate = () => {
    if (!form.name.trim() || !form.description.trim() || !form.persona_prompt.trim()) return;
    createMutation.mutate(form);
  };

  const openDrawer = (agent: AgentBlueprint) => {
    setSelectedAgent(agent);
    setDrawerOpen(true);
  };

  // --- render helpers ---
  const buildAccordionItems = (agent: AgentBlueprint): AccordionItem[] => [
    {
      id: `${agent.id}-details`,
      title: 'Persona & Instructions',
      icon: <Info size={16} />,
      content: (
        <p className="text-sm text-base-content/70 whitespace-pre-wrap">{agent.persona_prompt || 'No instructions set.'}</p>
      ),
    },
    {
      id: `${agent.id}-capabilities`,
      title: `Capabilities (${agent.capabilities.length})`,
      icon: <Zap size={16} />,
      content: (
        <div className="flex flex-wrap gap-2">
          {agent.capabilities.length > 0 ? (
            agent.capabilities.map((cap) => (
              <Badge key={cap} variant="info" size="small">
                {cap}
              </Badge>
            ))
          ) : (
            <span className="text-sm text-base-content/50">None defined</span>
          )}
        </div>
      ),
    },
    {
      id: `${agent.id}-handoffs`,
      title: `Handoff Triggers (${agent.handoff_triggers.length})`,
      icon: <ArrowRightLeft size={16} />,
      content: (
        <div className="flex flex-wrap gap-2">
          {agent.handoff_triggers.length > 0 ? (
            agent.handoff_triggers.map((t) => (
              <Badge key={t} variant="warning" size="small" badgeStyle="outline">
                {t}
              </Badge>
            ))
          ) : (
            <span className="text-sm text-base-content/50">No triggers</span>
          )}
        </div>
      ),
    },
    {
      id: `${agent.id}-activity`,
      title: 'Activity Timeline',
      icon: <Cpu size={16} />,
      content: <Timeline items={placeholderTimeline(agent.name)} vertical className="text-sm" />,
    },
  ];

  // --- loading ---
  if (isLoading) {
    return (
      <div className="space-y-6 animate-pulse" aria-busy="true" aria-label="Loading agents">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div className="space-y-2">
            <SkeletonText lines={1} className="h-10 w-64 rounded-lg" />
            <SkeletonText lines={1} className="h-5 w-96 rounded" />
          </div>
          <Skeleton width="8rem" height="3rem" className="rounded-lg" />
        </div>
        <div className="divider divider-accent"></div>
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <SkeletonCard key={i} showImage={false} showActions={true} className="h-64" />
          ))}
        </div>
      </div>
    );
  }

  // --- error ---
  if (isError) {
    return (
      <Alert status="error" className="shadow-lg">
        <span>Failed to load agents. Please check the backend connection.</span>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <PageHeader
          title="Agent Blueprints"
          subtitle="Manage AI agent personas, capabilities, and team handoffs."
          actions={
            <div className="flex gap-2">
              <Button variant="ghost" onClick={() => refetch()} title="Refresh Agents" aria-label="Refresh Agents">
                <RefreshCw size={18} className={isLoading ? 'animate-spin' : ''} />
              </Button>
              <Button variant="primary" onClick={() => setCreateModalOpen(true)}>
                <Plus size={18} />
                New Agent
              </Button>
            </div>
          }
        />
      </motion.div>

      <div className="divider divider-accent"></div>

      {/* Search */}
      <div className="flex items-center gap-2">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-base-content/40 z-10" size={18} />
          <Input
            type="text"
            placeholder="Search agents..."
            aria-label="Search agents"
            className="pl-10"
            value={searchQuery}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchQuery(e.target.value)}
            bordered
          />
        </div>
        {searchQuery && (
          <span className="text-sm text-base-content/60">
            Showing {filteredAgents.length} of {agentsList.length} agents
          </span>
        )}
      </div>

      {/* Agent Cards Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <AnimatePresence>
          {filteredAgents.map((agent, idx) => {
            const status = pseudoStatus(agent.id);
            const badge = STATUS_BADGE[status];
            return (
              <motion.div
                key={agent.id}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ delay: idx * 0.05 }}
              >
                <Card className="glass-card overflow-hidden">
                  <div className="border-gradient"></div>
                  <div className="card-body p-0">
                    {/* Agent header */}
                    <div className="p-6 bg-base-200/50 border-b border-base-content/10 flex justify-between items-start">
                      <div className="flex gap-3 items-center">
                        <Avatar placeholder shape="circle" size="md" innerClassName="bg-primary/20 text-primary">
                          {getInitials(agent.name)}
                        </Avatar>
                        <div>
                          <h2
                            className="card-title text-xl mb-1 cursor-pointer hover:text-primary transition-colors"
                            onClick={() => openDrawer(agent)}
                          >
                            {agent.name}
                          </h2>
                          <p className="text-sm text-base-content/60 line-clamp-1">{agent.description}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Tooltip content={`Status: ${badge.label}`} position="left">
                          <Badge variant={badge.variant} size="small" badgeStyle="outline">
                            {badge.label}
                          </Badge>
                        </Tooltip>
                        <Button
                          variant="ghost"
                          size="sm"
                          shape="circle"
                          className="text-error"
                          onClick={() => setPendingDelete(agent)}
                          aria-label={`Delete ${agent.name}`}
                        >
                          <Trash2 size={16} />
                        </Button>
                      </div>
                    </div>

                    {/* Accordion details */}
                    <div className="p-4">
                      <Accordion
                        items={buildAccordionItems(agent)}
                        allowMultiple
                        variant="bordered"
                        size="sm"
                      />
                    </div>

                    {/* Team role badge */}
                    {agent.team_role && (
                      <div className="px-6 pb-4">
                        <Badge variant="secondary" size="small" badgeStyle="outline">
                          Role: {agent.team_role}
                        </Badge>
                      </div>
                    )}
                  </div>
                </Card>
              </motion.div>
            );
          })}
        </AnimatePresence>

        {/* Empty state */}
        {isEmpty && (
          <div className="col-span-full">
            <EmptyState
              icon={Bot}
              title="No agent blueprints yet."
              description="Create your first AI agent blueprint to define personas, capabilities, and team handoffs."
              actionLabel={<><Plus size={18} /> Create Agent</>}
              onAction={() => setCreateModalOpen(true)}
            />
          </div>
        )}

        {/* No search results */}
        {searchQuery && filteredAgents.length === 0 && !isEmpty && (
          <div className="col-span-full">
            <EmptyState
              icon={Search}
              title="No agents match your search."
              description="Try adjusting your search terms or clearing the filter."
              actionLabel="Clear Search"
              onAction={() => setSearchQuery('')}
            />
          </div>
        )}
      </div>

      {/* Create Agent Modal */}
      <Modal
        isOpen={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        title="Create Agent Blueprint"
        size="lg"
        actions={[
          { label: 'Cancel', onClick: () => setCreateModalOpen(false), variant: 'ghost' },
          {
            label: 'Create',
            onClick: handleCreate,
            variant: 'primary',
            loading: createMutation.isPending,
            disabled: !form.name.trim() || !form.description.trim() || !form.persona_prompt.trim(),
          },
        ]}
      >
        <div className="space-y-4">
          {createMutation.isError && (
            <Alert status="error">
              <span>{(createMutation.error as Error)?.message ?? 'Creation failed'}</span>
            </Alert>
          )}
          <div>
            <label className="label font-semibold" htmlFor="agent-name">Name</label>
            <Input
              id="agent-name"
              type="text"
              placeholder="e.g. Research Assistant"
              value={form.name}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm((f) => ({ ...f, name: e.target.value }))}
              bordered
            />
          </div>
          <div>
            <label className="label font-semibold" htmlFor="agent-desc">Description</label>
            <Input
              id="agent-desc"
              type="text"
              placeholder="Short summary of this agent"
              value={form.description}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setForm((f) => ({ ...f, description: e.target.value }))}
              bordered
            />
          </div>
          <div>
            <label className="label font-semibold" htmlFor="agent-prompt">Persona Prompt</label>
            <Textarea
              id="agent-prompt"
              className="w-full h-28"
              bordered
              placeholder="Detailed system instructions for this agent..."
              value={form.persona_prompt}
              onChange={(e) => setForm((f) => ({ ...f, persona_prompt: e.target.value }))}
            />
          </div>
          <div>
            <label className="label font-semibold" htmlFor="agent-caps">Capabilities (comma separated)</label>
            <Input
              id="agent-caps"
              type="text"
              placeholder="e.g. search, summarize, code-review"
              value={(form.capabilities ?? []).join(', ')}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                setForm((f) => ({
                  ...f,
                  capabilities: e.target.value
                    .split(',')
                    .map((s) => s.trim())
                    .filter(Boolean),
                }))
              }
              bordered
            />
          </div>
          <div>
            <label className="label font-semibold" htmlFor="agent-role">Team Role (optional)</label>
            <Input
              id="agent-role"
              type="text"
              placeholder="e.g. researcher, coordinator"
              value={form.team_role ?? ''}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                setForm((f) => ({ ...f, team_role: e.target.value || null }))
              }
              bordered
            />
          </div>
          <div>
            <label className="label font-semibold" htmlFor="agent-handoffs">Handoff Triggers (comma separated)</label>
            <Input
              id="agent-handoffs"
              type="text"
              placeholder="e.g. needs-research, escalate"
              value={(form.handoff_triggers ?? []).join(', ')}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                setForm((f) => ({
                  ...f,
                  handoff_triggers: e.target.value
                    .split(',')
                    .map((s) => s.trim())
                    .filter(Boolean),
                }))
              }
              bordered
            />
          </div>
        </div>
      </Modal>

      {/* Delete Confirmation Modal */}
      <ConfirmModal
        isOpen={!!pendingDelete}
        onClose={() => setPendingDelete(null)}
        onConfirm={() => pendingDelete && deleteMutation.mutate(pendingDelete.id)}
        title="Delete Agent"
        message={`Are you sure you want to delete "${pendingDelete?.name ?? ''}"? This action cannot be undone.`}
        confirmText="Delete"
        cancelText="Cancel"
        confirmVariant="error"
        loading={deleteMutation.isPending}
      />

      {/* Agent Detail Drawer */}
      {selectedAgent && (
        <div className={`fixed inset-0 z-40 ${drawerOpen ? '' : 'pointer-events-none'}`}>
          {drawerOpen && (
            <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={() => setDrawerOpen(false)} />
          )}
          <div
            className={`absolute right-0 top-0 h-full w-full max-w-md bg-base-300 shadow-xl transition-transform duration-300 ${
              drawerOpen ? 'translate-x-0' : 'translate-x-full'
            }`}
          >
            <Drawer
              isOpen={drawerOpen}
              onClose={() => setDrawerOpen(false)}
              variant="sidebar"
              className="h-full"
            >
              <div className="p-6 space-y-6 overflow-y-auto h-full">
                <div className="flex items-center justify-between">
                  <h2 className="text-xl font-bold">{selectedAgent.name}</h2>
                  <Button variant="ghost" size="sm" onClick={() => setDrawerOpen(false)} aria-label="Close drawer">
                    X
                  </Button>
                </div>

                <div className="flex items-center gap-3">
                  <Avatar placeholder shape="circle" size="lg" innerClassName="bg-primary/20 text-primary">
                    {getInitials(selectedAgent.name)}
                  </Avatar>
                  <div>
                    <p className="font-semibold">{selectedAgent.name}</p>
                    <p className="text-sm text-base-content/60">{selectedAgent.description}</p>
                  </div>
                </div>

                <div>
                  <h3 className="font-semibold mb-2">Persona Prompt</h3>
                  <p className="text-sm text-base-content/70 whitespace-pre-wrap bg-base-200 p-3 rounded-lg">
                    {selectedAgent.persona_prompt}
                  </p>
                </div>

                <div>
                  <h3 className="font-semibold mb-2">Capabilities</h3>
                  <div className="flex flex-wrap gap-2">
                    {selectedAgent.capabilities.length > 0 ? (
                      selectedAgent.capabilities.map((cap) => (
                        <Badge key={cap} variant="info" size="small">{cap}</Badge>
                      ))
                    ) : (
                      <span className="text-sm text-base-content/50">None</span>
                    )}
                  </div>
                </div>

                <div>
                  <h3 className="font-semibold mb-2">Activity</h3>
                  <Timeline items={placeholderTimeline(selectedAgent.name)} vertical />
                </div>

                {selectedAgent.team_role && (
                  <div>
                    <h3 className="font-semibold mb-2">Team Role</h3>
                    <Badge variant="secondary" badgeStyle="outline">{selectedAgent.team_role}</Badge>
                  </div>
                )}
              </div>
            </Drawer>
          </div>
        </div>
      )}
    </div>
  );
}
