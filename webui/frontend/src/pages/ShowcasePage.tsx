import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Layers, 
  Zap,
  Edit3,
  Info,
  Navigation,
  Play,
  LayoutGrid
} from 'lucide-react';
import {
  Tabs,
  PageHeader
} from '../components/DaisyUI';

// Demo components
import { ActionsDemo } from '../components/DaisyUI/demos/ActionsDemo';
import { FormsDemo } from '../components/DaisyUI/demos/FormsDemo';
import { DataDemo } from '../components/DaisyUI/demos/DataDemo';
import { FeedbackDemo } from '../components/DaisyUI/demos/FeedbackDemo';
import { NavigationDemo } from '../components/DaisyUI/demos/NavigationDemo';
import { AnimationsDemo } from '../components/DaisyUI/demos/AnimationsDemo';

const ShowcasePage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('Buttons');

  const tabs = [
    { key: 'Buttons', label: 'Actions', icon: <Zap size={16} /> },
    { key: 'Forms', label: 'Inputs & Forms', icon: <Edit3 size={16} /> },
    { key: 'Data', label: 'Data Display', icon: <Layers size={16} /> },
    { key: 'Feedback', label: 'Feedback & Overlays', icon: <Info size={16} /> },
    { key: 'Navigation', label: 'Navigation', icon: <Navigation size={16} /> },
    { key: 'Animations', label: 'Animations', icon: <Play size={16} /> },
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
            className="min-h-[400px]"
          >
            {activeTab === 'Buttons' && <ActionsDemo />}
            {activeTab === 'Forms' && <FormsDemo />}
            {activeTab === 'Data' && <DataDemo />}
            {activeTab === 'Feedback' && <FeedbackDemo />}
            {activeTab === 'Navigation' && <NavigationDemo />}
            {activeTab === 'Animations' && <AnimationsDemo />}
          </motion.div>
        </AnimatePresence>
      </div>

      <div className="mt-16 text-center">
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-base-300 rounded-full text-[10px] font-bold uppercase tracking-widest opacity-40">
           <LayoutGrid size={12} />
           Design System v1.0.0
        </div>
      </div>
    </div>
  );
};

export default ShowcasePage;
