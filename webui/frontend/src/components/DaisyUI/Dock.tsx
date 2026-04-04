import React, { memo } from 'react';

export interface DockItem {
  label: string;
  icon: React.ReactNode;
  path?: string;
  active?: boolean;
  onClick?: () => void;
}

export interface DockProps {
  items: DockItem[];
  className?: string;
}

export const Dock = memo(({ items, className = '' }: DockProps) => {
  return (
    <div className={`dock ${className}`.trim()}>
      {items.map((item, idx) => (
        <button
          key={idx}
          className={item.active ? 'dock-active' : ''}
          onClick={item.onClick}
          aria-label={item.label}
          aria-current={item.active ? 'page' : undefined}
        >
          {item.icon}
          <span className="dock-label">{item.label}</span>
        </button>
      ))}
    </div>
  );
});

Dock.displayName = 'Dock';

export default Dock;
