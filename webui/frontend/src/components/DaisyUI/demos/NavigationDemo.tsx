import React, { useState } from 'react';
import { LayoutGrid, History, Smartphone } from 'lucide-react';
import { Button, Card, Steps, Dropdown, Pagination, Breadcrumbs, Hero, Dock } from '..';

export const NavigationDemo: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const [currentPage, setCurrentPage] = useState(1);

  return (
    <div className="space-y-8">
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
              <li><button type="button">Restart Worker</button></li>
              <li><button type="button">Purge Cache</button></li>
              <div className="divider my-0"></div>
              <li className="text-error"><button type="button">Emergency Stop</button></li>
            </Dropdown>

            <Dropdown trigger="System Menu" position="top" align="right" variant="secondary">
              <li><button type="button">Settings</button></li>
              <li><button type="button">Profile</button></li>
              <li><button type="button">Logout</button></li>
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
                { label: 'Dash', icon: <LayoutGrid size={18} />, active: true },
                { label: 'Stats', icon: <History size={18} /> },
                { label: 'Admin', icon: <Smartphone size={18} /> }
              ]}
              className="absolute bottom-2"
             />
          </div>
        </div>
      </Card>
    </div>
  );
};
