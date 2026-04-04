import React, { memo } from 'react';

export interface StepItem {
  label: string;
  description?: string;
}

export interface StepsProps {
  steps: StepItem[];
  currentStep: number;
  variant?: 'primary' | 'secondary' | 'accent' | 'success' | 'error' | 'warning' | 'info';
  vertical?: boolean;
  className?: string;
}

export const Steps = memo(({ steps, currentStep, variant = 'primary', vertical = false, className = '' }: StepsProps) => {
  return (
    <ul className={`steps ${vertical ? 'steps-vertical' : 'steps-horizontal'} ${className}`.trim()}>
      {steps.map((step, idx) => {
        const isComplete = idx < currentStep;
        const isCurrent = idx === currentStep;
        const stepClass = isComplete || isCurrent ? `step-${variant}` : '';

        return (
          <li
            key={idx}
            className={`step ${stepClass}`.trim()}
            data-content={isComplete ? '\u2713' : undefined}
          >
            <div className="flex flex-col items-center">
              <span className={isCurrent ? 'font-semibold' : ''}>{step.label}</span>
              {step.description && (
                <span className="text-xs opacity-60">{step.description}</span>
              )}
            </div>
          </li>
        );
      })}
    </ul>
  );
});

Steps.displayName = 'Steps';

export default Steps;
