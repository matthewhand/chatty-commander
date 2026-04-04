import React, { memo } from 'react';

export interface KbdProps {
  children: React.ReactNode;
  size?: 'xs' | 'sm' | 'md' | 'lg';
  className?: string;
}

export const Kbd = memo(({ children, size = 'md', className = '' }: KbdProps) => {
  const sizeClass = size !== 'md' ? `kbd-${size}` : '';

  return (
    <kbd className={`kbd ${sizeClass} ${className}`.trim()}>
      {children}
    </kbd>
  );
});

Kbd.displayName = 'Kbd';

export default Kbd;
