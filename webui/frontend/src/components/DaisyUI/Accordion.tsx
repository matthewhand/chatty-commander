import React, { useState, useCallback } from 'react';

export interface AccordionItem {
  id: string;
  title: string;
  content: React.ReactNode;
  icon?: string | React.ReactNode;
  disabled?: boolean;
  className?: string;
}

export interface AccordionProps {
  items: AccordionItem[];
  allowMultiple?: boolean;
  defaultOpenItems?: string[];
  className?: string;
  variant?: 'default' | 'bordered' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  iconPosition?: 'left' | 'right';
  onItemToggle?: (itemId: string, isOpen: boolean) => void;
}

const Accordion: React.FC<AccordionProps> = ({
  items, allowMultiple = false, defaultOpenItems = [], className = '',
  variant = 'default', size = 'md', iconPosition = 'left', onItemToggle,
}) => {
  const [openItems, setOpenItems] = useState<Set<string>>(new Set(defaultOpenItems));

  const handleToggle = useCallback((itemId: string) => {
    const isOpen = openItems.has(itemId);
    if (allowMultiple) {
      setOpenItems(prev => { const s = new Set(prev); isOpen ? s.delete(itemId) : s.add(itemId); return s; });
    } else {
      setOpenItems(() => { const s = new Set<string>(); if (!isOpen) s.add(itemId); return s; });
    }
    onItemToggle?.(itemId, !isOpen);
  }, [openItems, allowMultiple, onItemToggle]);

  const variantCls = { default: '', bordered: 'collapse-bordered', ghost: 'collapse-ghost' }[variant];
  const sizeTitleCls = { sm: 'text-sm', md: 'text-base', lg: 'text-lg' }[size];

  return (
    <div className={`accordion ${className}`}>
      {items.map((item) => {
        const isOpen = openItems.has(item.id);
        return (
          <div key={item.id} className={`collapse ${variantCls} ${item.className || ''}`}>
            <input type="checkbox" checked={isOpen} onChange={() => !item.disabled && handleToggle(item.id)}
              disabled={item.disabled} aria-expanded={isOpen} aria-controls={`accordion-content-${item.id}`}
              id={`accordion-toggle-${item.id}`} className="peer" />
            <div className={`collapse-title text-xl font-medium ${sizeTitleCls}`} role="button" tabIndex={item.disabled ? -1 : 0}
              onClick={() => !item.disabled && handleToggle(item.id)}
              onKeyDown={(e) => { if (!item.disabled && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); handleToggle(item.id); } }}
              aria-expanded={isOpen} aria-controls={`accordion-content-${item.id}`} aria-disabled={item.disabled}>
              <div className={`flex items-center gap-2 ${iconPosition === 'right' ? 'justify-between' : ''}`}>
                {iconPosition === 'left' && item.icon && <span className="text-2xl" aria-hidden="true">{item.icon}</span>}
                <span className="flex-1">{item.title}</span>
                {iconPosition === 'right' && item.icon && <span className="text-2xl" aria-hidden="true">{item.icon}</span>}
              </div>
            </div>
            <div className={`collapse-content ${sizeTitleCls}`} id={`accordion-content-${item.id}`}
              role="region" aria-labelledby={`accordion-toggle-${item.id}`}>
              {item.content}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default Accordion;
