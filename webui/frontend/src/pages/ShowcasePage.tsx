import React, { useState, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Layers, 
  Info, 
  CheckCircle2, 
  AlertCircle, 
  HelpCircle, 
  Plus, 
  Search, 
  Download, 
  Trash2, 
  Edit3,
  RefreshCw,
  Clock,
  Navigation,
  MessageSquare,
  Zap,
  Play,
  MousePointer2,
  Box,
  Layout,
  Table as TableIcon,
  Smartphone,
  History,
  Trello
} from 'lucide-react';
import {
  Button,
  Card,
  ConfirmModal,
  LoadingModal,
  Alert,
  Badge,
  Input,
  Tabs,
  Select,
  Textarea,
  Toggle,
  Checkbox,
  Tooltip,
  Avatar,
  LoadingSpinner,
  Progress,
  LoadingOverlay,
  Accordion,
  Dropdown,
  Skeleton,
  SkeletonAvatar,
  SkeletonText,
  SkeletonCard,
  SkeletonTableLayout,
  EmptyState,
  Chat,
  Timeline,
  Steps,
  Pagination,
  Rating,
  Kbd,
  Hero,
  Dock,
  Diff,
  Countdown,
  PageHeader,
  StatsCard,
  FileInput,
  Breadcrumbs
} from '../components/DaisyUI';

/* --- Helpers for Animation Demos --- */
function useReplay(): [number, () => void] {
  const [key, setKey] = useState(0);
  const replay = useCallback(() => setKey((k) => k + 1), []);
  return [key, replay];
}

const Code: React.FC<{ children: string }> = ({ children }) => (
  <pre className="bg-base-300 text-base-content text-[10px] md:text-xs rounded-lg p-3 overflow-x-auto mt-2 whitespace-pre-wrap font-mono">
    <code>{children}</code>
  </pre>
);

const ShowcasePage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('Buttons');
  const [isConfirmModalOpen, setIsConfirmModalOpen] = useState(false);
  const [isLoadingModalOpen, setIsLoadingModalOpen] = useState(false);
  const [rating, setRating] = useState(4);
  const [toggle, setToggle] = useState(true);
  const [checkbox, setCheckbox] = useState(true);
  const [currentStep, setCurrentStep] = useState(1);
  const [currentPage, setCurrentPage] = useState(1);
  
  // Animation state
  const [key1, replay1] = useReplay();
  const [key2, replay2] = useReplay();
  const [key3, replay3] = useReplay();

  const tabs = [
    { id: 'Buttons', label: 'Actions', icon: <Zap size={16} /> },
    { id: 'Forms', label: 'Inputs & Forms', icon: <Edit3 size={16} /> },
    { id: 'Data', label: 'Data Display', icon: <Layers size={16} /> },
    { id: 'Feedback', label: 'Feedback & Overlays', icon: <Info size={16} /> },
    { id: 'Navigation', label: 'Navigation', icon: <Navigation size={16} /> },
    { id: 'Animations', label: 'Animations', icon: <Play size={16} /> },
  ];

  return (
    <div className="pb-32">
      <PageHeader
        title="Component Showcase"
        subtitle="A comprehensive reference for our system's design language and UI library."
        icon={<Layers size={32} className="text-primary" />}
      />

      <div className="mt-8">
        <Tabs 
          tabs={tabs} 
          activeTab={activeTab} 
          onChange={setActiveTab} 
          className="mb-8"
          variant="boxed"
        />

        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
            className="space-y-8"
          >
            {activeTab === 'Buttons' && (
              <>
                <Card title="Button Variants">
                  <div className="space-y-8">
                    <div>
                      <p className="text-xs font-bold uppercase tracking-widest opacity-40 mb-4">Core Colors</p>
                      <div className="flex flex-wrap gap-2">
                        <Button variant="primary">Primary</Button>
                        <Button variant="secondary">Secondary</Button>
                        <Button variant="accent">Accent</Button>
                        <Button variant="neutral">Neutral</Button>
                        <Button variant="ghost">Ghost</Button>
                        <Button variant="link">Link</Button>
                      </div>
                    </div>
                    <div>
                      <p className="text-xs font-bold uppercase tracking-widest opacity-40 mb-4">Semantic Colors</p>
                      <div className="flex flex-wrap gap-2">
                        <Button variant="info">Info</Button>
                        <Button variant="success">Success</Button>
                        <Button variant="warning">Warning</Button>
                        <Button variant="error">Error</Button>
                      </div>
                    </div>
                  </div>
                </Card>

                <Card title="Sizes & Styles">
                  <div className="space-y-8">
                    <div>
                      <p className="text-xs font-bold uppercase tracking-widest opacity-40 mb-4">Size Options</p>
                      <div className="flex flex-wrap gap-2 items-center">
                        <Button size="lg">Large</Button>
                        <Button size="md">Normal</Button>
                        <Button size="sm">Small</Button>
                        <Button size="xs">Tiny</Button>
                      </div>
                    </div>
                    <div>
                      <p className="text-xs font-bold uppercase tracking-widest opacity-40 mb-4">Outline & Glass</p>
                      <div className="flex flex-wrap gap-2">
                        <Button variant="primary" buttonStyle="outline">Primary Outline</Button>
                        <Button variant="secondary" buttonStyle="outline">Secondary Outline</Button>
                        <Button variant="accent" buttonStyle="glass">Accent Glass</Button>
                        <Button variant="primary" buttonStyle="glass">Primary Glass</Button>
                      </div>
                    </div>
                  </div>
                </Card>

                <Card title="States & Interaction">
                  <div className="space-y-8">
                    <div>
                      <p className="text-xs font-bold uppercase tracking-widest opacity-40 mb-4">Loading States</p>
                      <div className="flex flex-wrap gap-2">
                        <Button loading>Default Loading</Button>
                        <Button variant="secondary" loading loadingText="Saving Changes...">Saving</Button>
                        <Button variant="accent" size="sm" loading />
                      </div>
                    </div>
                    <div>
                      <p className="text-xs font-bold uppercase tracking-widest opacity-40 mb-4">Icons</p>
                      <div className="flex flex-wrap gap-2">
                        <Button icon={<Plus size={16} />}>Start Icon</Button>
                        <Button iconRight={<Zap size={16} />} variant="secondary">End Icon</Button>
                        <Button icon={<Search size={16} />} className="btn-circle" aria-label="Search" />
                        <Button icon={<Trash2 size={16} />} variant="error" className="btn-square" aria-label="Delete" />
                      </div>
                    </div>
                  </div>
                </Card>
              </>
            )}

            {activeTab === 'Forms' && (
              <>
                <Card title="Text Inputs">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <Input label="Basic Text" placeholder="Type here..." />
                    <Input label="With Icon" prefix={<Search size={16} />} placeholder="Search system..." />
                    <Input label="Password" type="password" placeholder="Enter secret" />
                    <Input label="With Suffix" suffix=".chatty.io" placeholder="subdomain" />
                    <Input label="Error State" error="This field is required" defaultValue="Invalid" />
                    <Input label="Helper Text" helperText="Provide your full username." placeholder="Username" />
                  </div>
                </Card>

                <Card title="Complex Inputs">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <Select label="System Role">
                      <option disabled selected>Select a role</option>
                      <option>Admin</option>
                      <option>Developer</option>
                      <option>User</option>
                    </Select>
                    <FileInput label="Import Configuration (.json, .onnx)" variant="primary" />
                    <Textarea label="Agent Description" placeholder="Define the agent's behavior..." className="md:col-span-2" />
                  </div>
                </Card>

                <Card title="Selection & Toggles">
                  <div className="flex flex-wrap gap-12">
                    <div className="space-y-4">
                      <p className="text-xs font-bold uppercase tracking-widest opacity-40">Toggles</p>
                      <div className="flex flex-col gap-2">
                        <Toggle label="Enable Voice Mode" checked={toggle} onChange={() => setToggle(!toggle)} color="primary" />
                        <Toggle label="Debug Output" checked={toggle} onChange={() => setToggle(!toggle)} color="secondary" />
                        <Toggle label="Admin Privileges" checked={toggle} onChange={() => setToggle(!toggle)} color="accent" />
                      </div>
                    </div>
                    <div className="space-y-4">
                      <p className="text-xs font-bold uppercase tracking-widest opacity-40">Checkboxes</p>
                      <div className="flex flex-col gap-2">
                        <Checkbox label="Remember this device" checked={checkbox} onChange={() => setCheckbox(!checkbox)} variant="primary" />
                        <Checkbox label="Accept terms & conditions" checked={checkbox} onChange={() => setCheckbox(!checkbox)} variant="success" />
                        <Checkbox label="Newsletter subscription" checked={checkbox} onChange={() => setCheckbox(!checkbox)} variant="info" />
                      </div>
                    </div>
                    <div className="space-y-4">
                      <p className="text-xs font-bold uppercase tracking-widest opacity-40">Rating</p>
                      <div className="flex flex-col gap-4">
                        <Rating value={rating} onChange={setRating} />
                        <Rating value={rating} onChange={setRating} variant="warning" size="sm" />
                        <Rating value={3} readOnly size="xs" />
                      </div>
                    </div>
                  </div>
                </Card>
              </>
            )}

            {activeTab === 'Data' && (
              <>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <StatsCard title="Real-time Latency" value="12ms" icon={<Zap size={20} />} trend={{ value: 5, isPositive: true }} color="primary" />
                  <StatsCard title="System Load" value="2.4%" icon={<Box size={20} />} color="secondary" />
                  <StatsCard title="Uptime" value="99.98%" icon={<Clock size={20} />} trend={{ value: 0.01, isPositive: true }} color="success" />
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  <Card title="Activity Timeline">
                    <Timeline 
                      items={[
                        { id: '1', title: 'Wake word detected', subtitle: 'Just now', content: 'Voice recognition activated.', icon: <CheckCircle2 size={16} /> },
                        { id: '2', title: 'Executing Command', subtitle: '2m ago', content: 'Running "System: Update" workflow.', icon: <Play size={16} />, color: 'primary' },
                        { id: '3', title: 'Connection Refused', subtitle: '15m ago', content: 'Worker node 04 is offline.', icon: <AlertCircle size={16} />, color: 'error' },
                      ]}
                    />
                  </Card>

                  <Card title="System Components">
                    <Accordion 
                      items={[
                        { id: '1', title: 'Model Engine v2.4', content: 'Running ONNX Runtime with CUDA acceleration.' },
                        { id: '2', title: 'Network Bridge', content: 'Encrypted WebSocket tunnel on port 8100.' },
                        { id: '3', title: 'Persistence Layer', content: 'Local SQLite with automated snapshots.' },
                      ]}
                    />
                  </Card>
                </div>

                <Card title="Communication Log">
                  <div className="bg-base-300/30 p-6 rounded-2xl border border-base-content/5">
                    <Chat 
                      messages={[
                        { text: "System, initiate security sweep.", isUser: true, time: "10:30" },
                        { text: "Security sweep initiated. Scanning all modules...", isUser: false, time: "10:30", avatar: "S" },
                        { text: "Sweep complete. All systems nominal.", isUser: false, time: "10:31", avatar: "S", variant: "success" },
                      ]}
                    />
                  </div>
                </Card>
              </>
            )}

            {activeTab === 'Feedback' && (
              <>
                <Card title="Notifications & Alerts">
                  <div className="space-y-4">
                    <Alert variant="info" icon={<Info size={18} />}>System update available (v2.5.0).</Alert>
                    <Alert variant="success" icon={<CheckCircle2 size={18} />}>Profile changes saved successfully.</Alert>
                    <Alert variant="warning" icon={<AlertCircle size={18} />}>Low disk space remaining on /var/log.</Alert>
                    <Alert variant="error" icon={<AlertCircle size={18} />}>Critical: Agent service stopped unexpectedly.</Alert>
                  </div>
                </Card>

                <Card title="Modals & Context">
                  <div className="flex flex-wrap gap-4 items-center">
                    <Button variant="primary" onClick={() => setIsConfirmModalOpen(true)}>Trigger Confirm Modal</Button>
                    <Button variant="secondary" onClick={() => setIsLoadingModalOpen(true)}>Trigger Loading Modal</Button>
                    
                    <div className="divider divider-horizontal"></div>
                    
                    <div className="flex gap-4">
                      <Tooltip content="Tooltip on top" position="top">
                        <div className="p-3 bg-base-300 rounded-lg cursor-help"><MousePointer2 size={18} /></div>
                      </Tooltip>
                      <Tooltip content="Tooltip on right" position="right" color="secondary">
                        <div className="p-3 bg-base-300 rounded-lg cursor-help"><MousePointer2 size={18} /></div>
                      </Tooltip>
                    </div>
                  </div>

                  <ConfirmModal 
                    isOpen={isConfirmModalOpen}
                    onClose={() => setIsConfirmModalOpen(false)}
                    onConfirm={() => setIsConfirmModalOpen(false)}
                    title="Confirm System Purge"
                    message="You are about to delete all cached models. This action is irreversible."
                  />
                  
                  <LoadingModal 
                    isOpen={isLoadingModalOpen}
                    title="Synchronizing Models"
                    message="Fetching latest ONNX checkpoints from server..."
                  />
                </Card>

                <Card title="Skeleton States">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div className="space-y-6">
                      <div className="flex items-center gap-4">
                        <SkeletonAvatar size="md" />
                        <div className="space-y-2 flex-1">
                          <SkeletonText lines={2} />
                        </div>
                      </div>
                      <SkeletonCard />
                    </div>
                    <div>
                      <SkeletonTableLayout rows={4} columns={3} />
                    </div>
                  </div>
                </Card>
              </>
            )}

            {activeTab === 'Navigation' && (
              <>
                <Card title="Wizards & Steps">
                  <div className="space-y-8">
                    <Steps 
                      steps={[{ label: 'Discovery' }, { label: 'Mapping' }, { label: 'Execution' }, { label: 'Verification' }]}
                      currentStep={currentStep}
                    />
                    <div className="flex justify-center gap-4">
                      <Button size="sm" variant="ghost" onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}>Previous Step</Button>
                      <Button size="sm" variant="primary" onClick={() => setCurrentStep(Math.min(3, currentStep + 1))}>Next Step</Button>
                    </div>
                  </div>
                </Card>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <Card title="Menu & Dropdowns">
                    <div className="flex flex-wrap gap-4">
                      <Dropdown trigger="Quick Actions" position="bottom" color="primary">
                        <li className="menu-title">Control</li>
                        <li><a>Restart Worker</a></li>
                        <li><a>Purge Cache</a></li>
                        <div className="divider my-0"></div>
                        <li className="text-error"><a>Emergency Stop</a></li>
                      </Dropdown>

                      <Dropdown trigger="System Menu" position="top" align="right" variant="secondary">
                        <li><a>Settings</a></li>
                        <li><a>Profile</a></li>
                        <li><a>Logout</a></li>
                      </Dropdown>
                    </div>
                  </Card>

                  <Card title="Pagination">
                    <div className="flex flex-col items-center gap-4">
                      <Pagination currentPage={currentPage} totalPages={10} onPageChange={setCurrentPage} />
                      <Pagination currentPage={currentPage} totalPages={5} onPageChange={setCurrentPage} size="sm" />
                    </div>
                  </Card>
                </div>

                <Card title="Structural Layout">
                  <div className="space-y-12">
                    <Breadcrumbs />
                    <Hero 
                      title="Ready for Voice Commands" 
                      subtitle="Say 'Hey Chatty' to begin a conversation or command sequence."
                      className="bg-base-200/50 rounded-3xl"
                    >
                      <Button variant="primary" size="lg">Open Voice Panel</Button>
                    </Hero>
                    
                    <div className="flex justify-center p-4 bg-base-300 rounded-xl relative overflow-hidden h-24">
                       <p className="text-xs opacity-30">Dock Component Preview</p>
                       <Dock 
                        items={[
                          { label: 'Dash', icon: <Trello size={18} />, active: true },
                          { label: 'Stats', icon: <History size={18} /> },
                          { label: 'Admin', icon: <Smartphone size={18} /> }
                        ]}
                        className="absolute bottom-2"
                       />
                    </div>
                  </div>
                </Card>
              </>
            )}

            {activeTab === 'Animations' && (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <Card title="DaisyUI Loaders">
                    <div className="space-y-8">
                      <div>
                        <p className="text-xs font-bold uppercase tracking-widest opacity-40 mb-4">Spinners</p>
                        <div className="flex flex-wrap gap-6 items-center">
                          <LoadingSpinner size="lg" variant="primary" />
                          <LoadingSpinner size="md" variant="secondary" />
                          <LoadingSpinner size="sm" variant="accent" />
                          <LoadingSpinner size="xs" />
                        </div>
                      </div>
                      <div>
                        <p className="text-xs font-bold uppercase tracking-widest opacity-40 mb-4">Progress Bars</p>
                        <div className="space-y-4">
                          <Progress variant="primary" value={65} />
                          <Progress variant="secondary" indeterminate />
                        </div>
                      </div>
                    </div>
                  </Card>

                  <Card title="Tailwind Transitions">
                     <div className="space-y-8">
                        <div>
                          <p className="text-xs font-bold uppercase tracking-widest opacity-40 mb-4">Hover Effects</p>
                          <div className="flex flex-wrap gap-4">
                             <div className="w-16 h-16 bg-primary rounded-xl flex items-center justify-center text-primary-content transition-transform hover:scale-110 cursor-pointer">Scale</div>
                             <div className="w-16 h-16 bg-secondary rounded-xl flex items-center justify-center text-secondary-content transition-transform hover:-translate-y-2 cursor-pointer">Up</div>
                             <div className="w-16 h-16 bg-accent rounded-xl flex items-center justify-center text-accent-content transition-transform hover:rotate-12 cursor-pointer">Rotate</div>
                          </div>
                        </div>
                        <div>
                          <p className="text-xs font-bold uppercase tracking-widest opacity-40 mb-4">Shadow & Color</p>
                          <div className="flex flex-wrap gap-4">
                             <div className="w-20 h-12 bg-base-100 border border-base-300 rounded-lg flex items-center justify-center text-[10px] transition-shadow hover:shadow-xl cursor-pointer">Shadow</div>
                             <div className="w-20 h-12 btn btn-outline transition-colors hover:bg-success hover:text-success-content cursor-pointer">Color</div>
                          </div>
                        </div>
                     </div>
                  </Card>
                </div>

                <Card title="Custom CSS Keyframes">
                   <p className="text-sm opacity-70 mb-6">Built-in keyframe animations from our <code className="text-xs bg-base-300 px-1 rounded">index.css</code>.</p>
                   <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      <div className="space-y-4">
                        <div className="flex items-center justify-between">
                          <Badge variant="primary">fadeIn</Badge>
                          <Button size="xs" variant="ghost" onClick={replay1}><RefreshCw size={12} /></Button>
                        </div>
                        <div className="h-24 bg-base-200 rounded-xl flex items-center justify-center">
                          <div key={key1} className="w-10 h-10 bg-primary rounded-lg shadow-lg" style={{ animation: 'fadeIn 0.6s ease-out forwards' }} />
                        </div>
                      </div>

                      <div className="space-y-4">
                        <div className="flex items-center justify-between">
                          <Badge variant="secondary">dropdownSlide</Badge>
                          <Button size="xs" variant="ghost" onClick={replay2}><RefreshCw size={12} /></Button>
                        </div>
                        <div className="h-24 bg-base-200 rounded-xl flex items-center justify-center overflow-hidden">
                          <div key={key2} className="w-24 h-12 bg-secondary rounded-lg shadow-lg" style={{ animation: 'dropdownSlide 0.3s ease-out forwards' }} />
                        </div>
                      </div>

                      <div className="space-y-4">
                        <div className="flex items-center justify-between">
                          <Badge variant="accent">modalScale</Badge>
                          <Button size="xs" variant="ghost" onClick={replay3}><RefreshCw size={12} /></Button>
                        </div>
                        <div className="h-24 bg-base-200 rounded-xl flex items-center justify-center">
                          <div key={key3} className="w-12 h-12 bg-accent rounded-full shadow-lg" style={{ animation: 'modalScale 0.4s ease-out forwards' }} />
                        </div>
                      </div>
                   </div>
                </Card>

                <Card title="Motion Patterns">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div>
                      <p className="text-xs font-bold uppercase tracking-widest opacity-40 mb-4">Staggered Reveal</p>
                      <div className="space-y-2">
                        {[0, 1, 2, 3].map(i => (
                          <motion.div 
                            key={i}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: i * 0.1 }}
                            className="p-3 bg-base-200 rounded-lg flex items-center gap-3 border border-base-content/5"
                          >
                            <div className="w-2 h-2 rounded-full bg-primary" />
                            <span className="text-sm font-medium">Sequential Intelligence Module {i+1}</span>
                          </motion.div>
                        ))}
                      </div>
                    </div>
                    <div>
                      <p className="text-xs font-bold uppercase tracking-widest opacity-40 mb-4">Gradient Pulse</p>
                      <div 
                        className="h-full min-h-[140px] rounded-2xl flex items-center justify-center text-white font-bold text-xl"
                        style={{
                          background: 'linear-gradient(270deg, hsl(var(--p)), hsl(var(--s)), hsl(var(--a)), hsl(var(--p)))',
                          backgroundSize: '400% 400%',
                          animation: 'gradientShift 8s ease infinite',
                        }}
                      >
                         <style>{`
                           @keyframes gradientShift {
                             0%   { background-position: 0% 50%; }
                             50%  { background-position: 100% 50%; }
                             100% { background-position: 0% 50%; }
                           }
                         `}</style>
                         Dynamic Flow
                      </div>
                    </div>
                  </div>
                </Card>
              </>
            )}
          </motion.div>
        </AnimatePresence>
      </div>

      <div className="mt-16 text-center">
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-base-300 rounded-full text-[10px] font-bold uppercase tracking-widest opacity-40">
           <Trello size={12} />
           Project Structure Verified
        </div>
      </div>
    </div>
  );
};

export default ShowcasePage;
