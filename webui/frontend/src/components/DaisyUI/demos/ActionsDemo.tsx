import React from 'react';
import { Plus, Zap, Search, Trash2 } from 'lucide-react';
import { Button, Card } from '..';

export const ActionsDemo: React.FC = () => {
  return (
    <div className="space-y-8">
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
          <div>
            <p className="text-xs font-bold uppercase tracking-widest opacity-40 mb-4">Shapes</p>
            <div className="flex flex-wrap gap-2">
              <Button shape="circle" variant="primary">C</Button>
              <Button shape="square" variant="secondary">SQ</Button>
              <Button shape="wide" variant="accent">Wide Button</Button>
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
              <Button icon={<Search size={16} />} shape="circle" aria-label="Search" />
              <Button icon={<Trash2 size={16} />} variant="error" shape="square" aria-label="Delete" />
            </div>
          </div>
          <div>
            <p className="text-xs font-bold uppercase tracking-widest opacity-40 mb-4">Active State</p>
            <div className="flex flex-wrap gap-2">
              <Button active variant="primary">Active Primary</Button>
              <Button active variant="secondary">Active Secondary</Button>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};
