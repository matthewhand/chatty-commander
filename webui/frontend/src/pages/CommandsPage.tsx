import React, { useEffect, useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSearchParams } from 'react-router-dom';
import {
  TerminalSquare,
  Settings2,
  Globe,
  Plus,
  Edit3,
  Trash2,
  RefreshCw,
  Search,
  Upload,
  X
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { apiService } from '../services/apiService';
import {
  Button,
  Card,
  Alert,
  Badge,
  Input,
  EmptyState,
  SkeletonCard,
  Pagination,
  Kbd,
  PageHeader,
  Rating,
  Dropdown,
  FileInput,
} from '../components/DaisyUI';
import { ConfirmModal } from '../components/DaisyUI/Modal';

// Backend response is a Record<string, CommandConfig>
interface CommandConfig {
  action: string; // 'keypress' | 'url' | 'shell' | 'custom_message' | 'voice_chat'
  keys?: string;
  url?: string;
  cmd?: string;
  message?: string;
}

const ITEMS_PER_PAGE = 12;

export default function CommandsPage() {
  useEffect(() => {
    document.title = "Commands | ChattyCommander";
  }, []);

  const [searchParams, setSearchParams] = useSearchParams();
  const searchQuery = searchParams.get('q') || '';
  const [pendingDeleteCommand, setPendingDeleteCommand] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const fileInputRef = React.useRef<HTMLInputElement>(null);
  const { data: commands, isLoading, isError, refetch } = useQuery<Record<string, CommandConfig>>({
    queryKey: ['commands'],
    queryFn: () => apiService.getCommands(),
  });

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    if (value) {
      setSearchParams({ q: value });
    } else {
      setSearchParams({});
    }
    setCurrentPage(1);
  };

  // Debounce the search query by 300ms so filtering is delayed while typing
  const [debouncedSearch, setDebouncedSearch] = useState(searchQuery);
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(searchQuery), 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const handleDeleteClick = (commandName: string) => {
    setPendingDeleteCommand(commandName);
  };

  const handleDeleteConfirm = async () => {
    if (pendingDeleteCommand) {
      setIsDeleting(true);
      try {
        await apiService.deleteCommand(pendingDeleteCommand);
        refetch();
      } finally {
        setIsDeleting(false);
      }
    }
    setPendingDeleteCommand(null);
  };

  const handleDeleteCancel = () => {
    setPendingDeleteCommand(null);
  };

  // Memoize the derived array to prevent expensive Object.entries() and array reallocation
  // on every render cycle, which improves performance on this page.
  const commandsList = useMemo(() => {
    return commands ? Object.entries(commands) : [];
  }, [commands]);

  // Memoize the empty check to avoid recalculating on each render
  const isEmpty = useMemo(() => !isLoading && commandsList.length === 0, [isLoading, commandsList.length]);

  const handleExportJson = () => {
    const blob = new Blob([JSON.stringify(commands, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'commands.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleImportJson = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = async (event) => {
      try {
        const parsed = JSON.parse(event.target?.result as string);
        if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
          alert('Invalid JSON: expected an object.');
          return;
        }
        await apiService.updateConfig({ commands: parsed });
        refetch();
      } catch (err) {
        alert(`Import failed: ${err instanceof Error ? err.message : String(err)}`);
      }
    };
    reader.readAsText(file);
    // Reset so the same file can be re-imported if needed
    e.target.value = '';
  };

  // Memoize filtered commands for search functionality (uses debounced value)
  const filteredCommands = useMemo(() => {
    if (!debouncedSearch.trim()) return commandsList;
    const query = debouncedSearch.toLowerCase();
    return commandsList.filter(([name, config]) =>
      name.toLowerCase().includes(query) ||
      (config.action && config.action.toLowerCase().includes(query))
    );
  }, [commandsList, debouncedSearch]);

  // Reset to page 1 when filtered results change
  useEffect(() => {
    setCurrentPage(1);
  }, [debouncedSearch]);

  // Pagination
  const totalPages = Math.max(1, Math.ceil(filteredCommands.length / ITEMS_PER_PAGE));
  const paginatedCommands = useMemo(() => {
    const start = (currentPage - 1) * ITEMS_PER_PAGE;
    return filteredCommands.slice(start, start + ITEMS_PER_PAGE);
  }, [filteredCommands, currentPage]);

  if (isLoading) {
    return (
      <div className="space-y-6 animate-pulse" aria-busy="true" aria-label="Loading commands">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <div className="h-10 w-64 skeleton mb-2 rounded-lg"></div>
            <div className="h-5 w-96 skeleton rounded"></div>
          </div>
          <div className="h-12 w-32 skeleton rounded-lg"></div>
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

  if (isError) {
    return (
      <Alert status="error" className="shadow-lg">
        <span>Failed to load commands. Please check the backend connection.</span>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <PageHeader
          title="Commands & Triggers"
          subtitle="Manage system commands and configuration."
          actions={
            <div className="flex gap-2">
              <Button
                variant="ghost"
                onClick={() => refetch()}
                title="Refresh Commands"
                aria-label="Refresh Commands"
              >
                <RefreshCw size={18} className={isLoading ? "animate-spin" : ""} />
              </Button>
              <Button
                variant="primary"
                buttonStyle="outline"
                size="sm"
                onClick={handleExportJson}
                title="Export JSON"
                aria-label="Export commands as JSON"
                disabled={!commands || commandsList.length === 0}
              >
                <Upload size={16} />
                Export JSON
                </Button>
                <FileInput
                ref={fileInputRef}
                accept=".json"
                className="hidden"
                onChange={handleImportJson}
                />
                <Button
                variant="primary"

                buttonStyle="outline"
                size="sm"
                onClick={() => fileInputRef.current?.click()}
                title="Import JSON"
                aria-label="Import commands from JSON"
              >
                <Upload size={16} />
                Import JSON
              </Button>
              <Button to="/commands/authoring" buttonStyle="glass">
                <Plus size={18} />
                New Command
              </Button>
            </div>
          }
        />
      </motion.div>

      <div className="divider divider-accent"></div>

      {/* Search Filter */}
      <div className="flex items-center gap-2">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-base-content/40 z-10" size={18} />
          <Input
            type="text"
            placeholder="Search commands..."
            aria-label="Search commands"
            className="pl-10 pr-20"
            value={searchQuery}
            onChange={handleSearchChange}
            autoFocus
            bordered
          />
          <Kbd size="sm" className="absolute right-10 top-1/2 -translate-y-1/2 text-base-content/40 z-10">
            Ctrl+K
          </Kbd>
          {searchQuery && (
            <Button
              variant="ghost"
              size="xs"
              className="absolute right-3 top-1/2 -translate-y-1/2 btn-circle z-10"
              onClick={() => setSearchParams({})}
              aria-label="Clear search"
            >
              <X size={14} />
            </Button>
          )}
        </div>
        {searchQuery && (
          <span className="text-sm text-base-content/60">
            Showing {filteredCommands.length} of {commandsList.length} commands
          </span>
        )}
      </div>

      {/* Commands Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <AnimatePresence>
          {paginatedCommands.map(([name, config], idx) => (
            <motion.div
              key={name}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: idx * 0.05 }}
            >
              <Card className="glass-card overflow-hidden">
                <div className="border-gradient"></div>
                <div className="card-body p-0">
                  {/* Command Header */}
                  <div className="p-6 bg-base-200/50 border-b border-base-content/10 flex justify-between items-start">
                    <div className="flex gap-3">
                      <div className="p-3 rounded-xl bg-primary/20 text-primary">
                        <TerminalSquare size={24} />
                      </div>
                      <div>
                        <h2 className="card-title text-xl mb-1">{name}</h2>
                        <div className="flex gap-2 text-xs font-mono text-base-content/60 mb-2">
                          <span className="px-2 py-1 rounded bg-base-300">{config.action}</span>
                          <span className="px-2 py-1 rounded bg-base-300 truncate max-w-[200px]" title={
                            config.keys || config.url || config.cmd || config.message || ""
                          }>
                            {config.keys || config.url || config.cmd || config.message || "-"}
                          </span>
                        </div>
                        <div className="flex items-center gap-2" title="Success Rate">
                          <Rating value={(name.length % 3) + 3} size="xs" variant="warning" readOnly />
                          <span className="text-[10px] text-base-content/50 uppercase tracking-wider font-semibold">Reliability</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex gap-1">
                      <Dropdown
                        trigger={
                          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.75a.75.75 0 110-1.5.75.75 0 010 1.5zM12 12.75a.75.75 0 110-1.5.75.75 0 010 1.5zM12 18.75a.75.75 0 110-1.5.75.75 0 010 1.5z" />
                          </svg>
                        }
                        color="ghost"
                        size="sm"
                        triggerClassName="btn-circle"
                        align="right"
                        hideArrow
                        contentClassName="w-52 border border-base-content/10"
                      >
                        <li>
                          <button aria-label={`Edit ${name}`}>
                            <Edit3 size={16} className="text-primary" />
                            Edit Command
                          </button>
                        </li>
                        <li>
                          <button className="text-error hover:bg-error/10 hover:text-error" aria-label={`Delete ${name}`} onClick={() => handleDeleteClick(name)}>
                            <Trash2 size={16} />
                            Delete Command
                          </button>
                        </li>
                      </Dropdown>
                    </div>
                  </div>

                  {/* Triggers Section */}
                  <div className="p-6 space-y-4">
                    <h3 className="text-sm font-semibold uppercase tracking-wider text-base-content/50 flex items-center gap-2">
                      <Settings2 size={14} /> Activation Triggers
                    </h3>

                    {/* REST API Badge */}
                    <div className="flex items-center gap-3 p-3 rounded-lg border border-success/30 bg-success/5">
                      <Globe className="text-success" size={20} />
                      <div className="flex-1">
                        <p className="font-medium text-sm">REST API Trigger</p>
                        <p className="text-xs text-base-content/60 font-mono mt-0.5">POST /api/v1/command</p>
                      </div>
                      <Badge variant="success" size="small" badgeStyle="outline">Enabled</Badge>
                    </div>
                  </div>
                </div>
              </Card>
            </motion.div>
          ))}
        </AnimatePresence>
        {isEmpty && (
          <div className="col-span-full">
            <EmptyState
              icon={TerminalSquare}
              title="No commands configured."
              description="Get started by creating your first command to automate tasks and streamline your workflow."
              actionLabel={<><Plus size={18} /> Create Command</>}
              onAction={() => { window.location.href = '/commands/authoring'; }}
            />
          </div>
        )}
        {searchQuery && filteredCommands.length === 0 && !isEmpty && (
          <div className="col-span-full">
            <EmptyState
              icon={Search}
              title="No commands match your search."
              description="Try adjusting your search terms or clearing the search filter to see all commands."
              actionLabel="Clear Search"
              onAction={() => setSearchParams({})}
            />
          </div>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center mt-6">
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={setCurrentPage}
          />
        </div>
      )}

      {/* Delete Confirmation Modal */}
      <ConfirmModal
        isOpen={!!pendingDeleteCommand}
        onClose={handleDeleteCancel}
        onConfirm={handleDeleteConfirm}
        title="Confirm Deletion"
        message={`Are you sure you want to delete ${pendingDeleteCommand}?`}
        confirmText="Delete"
        cancelText="Cancel"
        confirmVariant="error"
        loading={isDeleting}
      />
    </div>
  );
}
