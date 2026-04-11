import React from 'react';
import { Zap, Box, Clock, CheckCircle2, Play, AlertCircle } from 'lucide-react';
import { Card, StatsCard, Timeline, Accordion, Chat } from '..';

export const DataDemo: React.FC = () => {
  return (
    <div className="space-y-8">
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
    </div>
  );
};
