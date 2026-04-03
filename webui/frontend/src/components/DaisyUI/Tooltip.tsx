import React from 'react';

interface TooltipProps {
  content: React.ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
  children: React.ReactElement;
  className?: string;
  color?: 'primary' | 'secondary' | 'accent' | 'info' | 'success' | 'warning' | 'error';
}

const Tooltip: React.FC<TooltipProps> = ({ content, position = 'top', children, className = '', color }) => {
  const colorClass = color ? `tooltip-${color}` : '';
  return (
    <div className={`tooltip tooltip-${position} ${colorClass} ${className}`} data-tip={content} role="tooltip" aria-live="polite">
      {children}
    </div>
  );
};

export default Tooltip;
