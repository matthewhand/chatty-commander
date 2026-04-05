import React, { useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { RefreshCw } from 'lucide-react';
import { Button, Card, LoadingSpinner, Progress, Badge } from '..';

function useReplay(): [number, () => void] {
  const [key, setKey] = useState(0);
  const replay = useCallback(() => setKey((k) => k + 1), []);
  return [key, replay];
}

export const AnimationsDemo: React.FC = () => {
  const [key1, replay1] = useReplay();
  const [key2, replay2] = useReplay();
  const [key3, replay3] = useReplay();

  return (
    <div className="space-y-8">
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
    </div>
  );
};
