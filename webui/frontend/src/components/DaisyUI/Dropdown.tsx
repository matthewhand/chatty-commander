import React, { useState, useRef, useEffect, useCallback } from 'react';
import { ChevronDown } from 'lucide-react';

type DropdownProps = {
  trigger: React.ReactNode;
  children: React.ReactNode;
  position?: 'top' | 'bottom' | 'left' | 'right';
  align?: 'left' | 'right';
  color?: 'primary' | 'secondary' | 'accent' | 'ghost' | 'none' | 'info' | 'success' | 'warning' | 'error';
  variant?: 'primary' | 'secondary' | 'accent' | 'ghost' | 'none' | 'info' | 'success' | 'warning' | 'error'; // Compatibility
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'none';
  isOpen?: boolean;
  onToggle?: (isOpen: boolean) => void;
  className?: string;
  triggerClassName?: string;
  contentClassName?: string;
  disabled?: boolean;
  hideArrow?: boolean;
  ariaLabel?: string;
};

const Dropdown: React.FC<DropdownProps> = ({
  trigger, children, position = 'bottom', align = 'left', color = 'ghost', variant, size = 'md',
  isOpen: controlledIsOpen, onToggle, className = '', triggerClassName = '',
  contentClassName = '', disabled = false, hideArrow = false, ariaLabel,
}) => {
  const [uncontrolledIsOpen, setUncontrolledIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const menuRef = useRef<HTMLUListElement>(null);
  const menuItemsRef = useRef<(HTMLLIElement | HTMLAnchorElement | HTMLButtonElement)[]>([]);
  const isOpen = controlledIsOpen ?? uncontrolledIsOpen;
  
  const setIsOpen = useCallback((newState: boolean) => {
    if (onToggle) {
      onToggle(newState);
    } else {
      setUncontrolledIsOpen(newState);
    }
  }, [onToggle]);

  const appliedColor = variant || color;

  const handleToggle = (e?: React.MouseEvent) => {
    e?.stopPropagation();
    if (!disabled) setIsOpen(!isOpen);
  };

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) setIsOpen(false);
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [setIsOpen]);

  useEffect(() => {
    if (!isOpen) return;
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') setIsOpen(false); };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [isOpen, setIsOpen]);

  // Keyboard navigation within menu
  useEffect(() => {
    if (!isOpen) return;
    const handler = (e: KeyboardEvent) => {
      const items = menuItemsRef.current.filter(Boolean);
      if (items.length === 0) return;

      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        e.preventDefault();
        const currentIndex = items.indexOf(document.activeElement as any);
        const direction = e.key === 'ArrowDown' ? 1 : -1;
        const nextIndex = currentIndex === -1 ? 0 : (currentIndex + direction + items.length) % items.length;
        items[nextIndex]?.focus();
      }

      if (e.key === 'Enter' || e.key === ' ') {
        const focusedElement = document.activeElement as any;
        if (focusedElement && menuItemsRef.current.includes(focusedElement)) {
          e.preventDefault();
          focusedElement.click();
        }
      }
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [isOpen]);

  // Focus management: move focus to first menu item when dropdown opens
  useEffect(() => {
    if (isOpen && menuRef.current) {
      const firstItem = menuItemsRef.current[0];
      if (firstItem) {
        firstItem.focus();
      }
    }
  }, [isOpen]);

  const positionCls = { top: 'dropdown-top', bottom: 'dropdown-bottom', left: 'dropdown-left', right: 'dropdown-right' }[position];
  const alignCls = align === 'right' ? 'dropdown-end' : '';
  const sizeCls = size === 'none' ? '' : `btn-${size}`;
  const colorCls = appliedColor === 'none' ? '' : `btn-${appliedColor}`;

  return (
    <div className={`dropdown ${positionCls} ${alignCls} ${className}`} ref={dropdownRef}>
      <div tabIndex={disabled ? -1 : 0} role="button"
        className={`btn ${sizeCls} ${colorCls} ${disabled ? 'btn-disabled opacity-50' : ''} ${triggerClassName}`}
        onClick={handleToggle} aria-haspopup="true" aria-expanded={isOpen} aria-label={ariaLabel || 'Toggle dropdown'}>
        {trigger}
        {!hideArrow && <ChevronDown className="h-5 w-5" aria-hidden="true" />}
      </div>
      {isOpen && (
        <ul 
          ref={menuRef}
          tabIndex={0} 
          className={`dropdown-content menu p-2 shadow bg-base-100 rounded-box w-52 z-50 ${contentClassName}`} 
          role="menu"
        >
          {React.Children.map(children, (child, index) => {
            if (React.isValidElement(child)) {
              return React.cloneElement(child as React.ReactElement<any>, {
                ref: (el: HTMLLIElement | HTMLAnchorElement | HTMLButtonElement | null) => {
                  if (el) menuItemsRef.current[index] = el;
                },
                role: 'menuitem',
                tabIndex: index === 0 ? 0 : -1,
              });
            }
            return child;
          })}
        </ul>
      )}
    </div>
  );
};

export default Dropdown;
