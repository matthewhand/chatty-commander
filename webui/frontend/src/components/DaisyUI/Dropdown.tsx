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
  contentClassName = '', disabled = false, hideArrow = false, ariaLabel = 'Toggle dropdown',
}) => {
  const [uncontrolledIsOpen, setUncontrolledIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const isOpen = controlledIsOpen ?? uncontrolledIsOpen;
  
  const setIsOpen = useCallback((newState: boolean) => {
    if (onToggle) {
      onToggle(newState);
    } else {
      setUncontrolledIsOpen(newState);
    }
  }, [onToggle]);

  const appliedColor = variant || color;

  const handleToggle = (e?: React.MouseEvent | React.KeyboardEvent) => {
    e?.stopPropagation();
    if (!disabled) setIsOpen(!isOpen);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleToggle(e);
    }
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

  const positionCls = { top: 'dropdown-top', bottom: 'dropdown-bottom', left: 'dropdown-left', right: 'dropdown-right' }[position];
  const alignCls = align === 'right' ? 'dropdown-end' : '';
  const sizeCls = size === 'none' ? '' : `btn-${size}`;
  const colorCls = appliedColor === 'none' ? '' : `btn-${appliedColor}`;

  return (
    <div className={`dropdown ${positionCls} ${alignCls} ${className}`} ref={dropdownRef}>
      <div tabIndex={disabled ? -1 : 0} role="button"
        className={`btn ${sizeCls} ${colorCls} ${disabled ? 'btn-disabled opacity-50' : ''} ${triggerClassName}`}
        onClick={handleToggle} onKeyDown={handleKeyDown} aria-haspopup="true" aria-expanded={isOpen} aria-label={ariaLabel}>
        {trigger}
        {!hideArrow && <ChevronDown className="h-5 w-5" aria-hidden="true" />}
      </div>
      {isOpen && (
        <ul tabIndex={0} className={`dropdown-content menu p-2 shadow bg-base-100 rounded-box w-52 z-50 ${contentClassName}`} role="menu">
          {children}
        </ul>
      )}
    </div>
  );
};

export default Dropdown;
