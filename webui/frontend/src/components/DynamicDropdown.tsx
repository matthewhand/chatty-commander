import React, { useState, useRef, useEffect } from 'react';
import { useFloating, shift, flip, offset, autoUpdate } from '@floating-ui/react-dom';

interface DropdownProps {
  buttonContent: React.ReactNode;
  children: React.ReactNode;
  buttonClassName?: string;
  menuClassName?: string;
  ariaLabel?: string;
}

export function DynamicDropdown({
  buttonContent,
  children,
  buttonClassName = "btn btn-ghost btn-sm btn-circle",
  menuClassName = "menu p-2 shadow bg-base-100 rounded-box w-52 border border-base-content/10",
  ariaLabel = "Open menu"
}: DropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const menuItemsRef = useRef<(HTMLButtonElement | HTMLAnchorElement)[]>([]);

  const { x, y, strategy, refs } = useFloating<HTMLButtonElement>({
    placement: 'bottom-end',
    middleware: [
      offset(4),
      flip({ padding: 8 }),
      shift({ padding: 8 })
    ],
    whileElementsMounted: autoUpdate,
  });

  // Handle clicking outside to close
  React.useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        refs.reference.current &&
        !(refs.reference.current as HTMLElement).contains(event.target as Node) &&
        refs.floating.current &&
        !refs.floating.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [refs]);

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (!isOpen) return;

      if (event.key === 'Escape') {
        setIsOpen(false);
        refs.reference.current?.focus();
        return;
      }

      if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
        event.preventDefault();
        const items = menuItemsRef.current.filter(Boolean);
        if (items.length === 0) return;

        const currentIndex = items.indexOf(document.activeElement as HTMLButtonElement | HTMLAnchorElement);
        const direction = event.key === 'ArrowDown' ? 1 : -1;
        const nextIndex = currentIndex === -1 ? 0 : (currentIndex + direction + items.length) % items.length;
        items[nextIndex]?.focus();
      }

      if (event.key === 'Enter' || event.key === ' ') {
        const focusedElement = document.activeElement as HTMLButtonElement | HTMLAnchorElement;
        if (focusedElement && menuItemsRef.current.includes(focusedElement)) {
          event.preventDefault();
          focusedElement.click();
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, refs]);

  // Focus management: move focus to first menu item when dropdown opens
  useEffect(() => {
    if (isOpen && menuRef.current) {
      const firstItem = menuItemsRef.current[0];
      if (firstItem) {
        firstItem.focus();
      }
    }
  }, [isOpen]);

  return (
    <>
      <button
        ref={refs.setReference}
        onClick={() => setIsOpen(!isOpen)}
        className={buttonClassName}
        aria-expanded={isOpen}
        aria-haspopup="true"
        aria-label={ariaLabel}
      >
        {buttonContent}
      </button>

      {isOpen && (
        <div
          ref={(node) => {
            refs.setFloating(node);
            if (node) menuRef.current = node;
          }}
          style={{
            position: strategy,
            top: y ?? 0,
            left: x ?? 0,
            zIndex: 50,
          }}
          className={menuClassName}
          role="menu"
          onClick={() => setIsOpen(false)} // close on item click
        >
          {React.Children.map(children, (child, index) => {
            if (React.isValidElement(child)) {
              return React.cloneElement(child as React.ReactElement<any>, {
                ref: (el: HTMLButtonElement | HTMLAnchorElement | null) => {
                  if (el) menuItemsRef.current[index] = el;
                },
                role: 'menuitem',
                tabIndex: index === 0 ? 0 : -1,
              });
            }
            return child;
          })}
        </div>
      )}
    </>
  );
}