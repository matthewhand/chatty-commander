import React, { useState } from 'react';
import { Info, CheckCircle2, AlertCircle, MousePointer2 } from 'lucide-react';
import { Button, Card, Alert, Tooltip, ConfirmModal, LoadingModal, SkeletonAvatar, SkeletonText, SkeletonCard, SkeletonTableLayout } from '..';

export const FeedbackDemo: React.FC = () => {
  const [isConfirmModalOpen, setIsConfirmModalOpen] = useState(false);
  const [isLoadingModalOpen, setIsLoadingModalOpen] = useState(false);

  return (
    <div className="space-y-8">
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
    </div>
  );
};
