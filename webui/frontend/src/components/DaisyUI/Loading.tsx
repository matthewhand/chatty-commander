import React from 'react';

interface LoadingSpinnerProps {
  size?: 'xs' | 'sm' | 'md' | 'lg';
  variant?: 'spinner' | 'dots' | 'ring' | 'ball' | 'bars' | 'infinity' | 'primary' | 'secondary' | 'accent' | 'neutral' | 'info' | 'success' | 'warning' | 'error';
  color?: 'primary' | 'secondary' | 'accent' | 'neutral' | 'info' | 'success' | 'warning' | 'error';
  className?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ size = 'md', variant = 'spinner', color = 'primary', className = '' }) => {
  const isColorVariant = ['primary', 'secondary', 'accent', 'neutral', 'info', 'success', 'warning', 'error'].includes(variant as string);
  const type = isColorVariant ? 'spinner' : variant;
  const appliedColor = isColorVariant ? variant : color;
  
  return (
    <span className={`loading loading-${type} loading-${size} text-${appliedColor} ${className}`} aria-hidden="true" />
  );
};

export const Loading: React.FC<{ type?: LoadingSpinnerProps['variant']; size?: LoadingSpinnerProps['size']; color?: LoadingSpinnerProps['color']; className?: string }> = ({
  type = 'spinner', size = 'md', color = 'primary', className = '',
}) => <LoadingSpinner variant={type} size={size} color={color} className={className} />;

interface ProgressProps {
  value?: number; max?: number;
  variant?: 'primary' | 'secondary' | 'accent' | 'info' | 'success' | 'warning' | 'error';
  size?: 'xs' | 'sm' | 'md' | 'lg';
  indeterminate?: boolean; showValue?: boolean; className?: string;
}

export const Progress: React.FC<ProgressProps> = ({ value = 0, max = 100, variant = 'primary', size = 'md', indeterminate = false, showValue = false, className = '' }) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);
  const sizeClass = { xs: 'h-1', sm: 'h-2', md: 'h-3', lg: 'h-4' }[size] || 'h-3';
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <progress className={`progress progress-${variant} ${sizeClass} flex-1`}
        value={indeterminate ? undefined : percentage} max="100"
        aria-label={indeterminate ? 'Loading in progress' : `Progress: ${Math.round(percentage)}%`} />
      {showValue && !indeterminate && <span className="text-sm font-medium min-w-[3rem] text-right" aria-hidden="true">{Math.round(percentage)}%</span>}
    </div>
  );
};

interface LoadingOverlayProps { isLoading: boolean; children: React.ReactNode; message?: string; className?: string; }

export const LoadingOverlay: React.FC<LoadingOverlayProps> = ({ isLoading, children, message = 'Loading...', className = '' }) => (
  <div className={`relative ${className}`}>
    {children}
    {isLoading && (
      <div className="absolute inset-0 bg-base-100/80 backdrop-blur-sm flex items-center justify-center z-10" role="status" aria-live="polite">
        <div className="text-center">
          <LoadingSpinner size="lg" />
          <p className="mt-2 text-base-content/70">{message}</p>
        </div>
      </div>
    )}
  </div>
);

const LoadingComponents = { Loading, LoadingSpinner, Progress, LoadingOverlay };
export default LoadingComponents;
