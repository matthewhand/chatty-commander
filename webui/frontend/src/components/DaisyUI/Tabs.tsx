import React, { memo, useCallback } from 'react';
import classNames from 'classnames';

export interface TabItem {
  key: string;
  label: string | React.ReactNode;
  icon?: React.ReactNode;
  disabled?: boolean;
}

export interface TabsProps {
  tabs: TabItem[];
  activeTab: string;
  onChange: (key: string) => void;
  variant?: 'boxed' | 'bordered' | 'lifted';
  size?: 'xs' | 'sm' | 'md' | 'lg';
  className?: string;
}

const variantClasses: Record<string, string> = {
  boxed: 'tabs-boxed', bordered: 'tabs-bordered', lifted: 'tabs-lifted',
};
const sizeClasses: Record<string, string> = {
  xs: 'tabs-xs', sm: 'tabs-sm', md: '', lg: 'tabs-lg',
};

export const Tabs = memo(({ tabs, activeTab, onChange, variant = 'boxed', size = 'md', className }: TabsProps) => {
  const handleClick = useCallback((key: string, disabled?: boolean) => {
    if (!disabled) onChange(key);
  }, [onChange]);

  return (
    <div role="tablist" className={classNames('tabs', variantClasses[variant], sizeClasses[size], className)}>
      {tabs.map((tab) => (
        <button key={tab.key} role="tab"
          className={classNames('tab', { 'tab-active': tab.key === activeTab, 'tab-disabled': tab.disabled })}
          aria-selected={tab.key === activeTab} disabled={tab.disabled}
          onClick={() => handleClick(tab.key, tab.disabled)}>
          {tab.icon && <span className="mr-1" aria-hidden="true">{tab.icon}</span>}
          {tab.label}
        </button>
      ))}
    </div>
  );
});

Tabs.displayName = 'Tabs';
export default Tabs;
