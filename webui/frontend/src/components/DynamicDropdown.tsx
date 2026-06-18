import React, { useState } from 'react';
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

  const menuId = React.useId();

  // Handle keyboard interaction (Escape to close, Arrows for navigation)
  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Escape') {
      setIsOpen(false);
      refs.reference.current?.focus();
    } else if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault();
      const focusableElements = refs.floating.current?.querySelectorAll<HTMLElement>(
        'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
      );
      if (!focusableElements || focusableElements.length === 0) return;

      const elementsArray = Array.from(focusableElements);
      const currentIndex = elementsArray.indexOf(document.activeElement as HTMLElement);

      let nextIndex = 0;
      if (event.key === 'ArrowDown') {
        nextIndex = currentIndex < elementsArray.length - 1 ? currentIndex + 1 : 0;
      } else {
        nextIndex = currentIndex > 0 ? currentIndex - 1 : elementsArray.length - 1;
      }

      elementsArray[nextIndex].focus();
    }
  };

  return (
    <>
      <button
        ref={refs.setReference}
        onClick={() => setIsOpen(!isOpen)}
        onKeyDown={(e) => {
          if (e.key === 'ArrowDown' && !isOpen) {
            e.preventDefault();
            setIsOpen(true);
          }
        }}
        className={buttonClassName}
        aria-expanded={isOpen}
        aria-haspopup="true"
        aria-label={ariaLabel}
        aria-controls={isOpen ? menuId : undefined}
      >
        {buttonContent}
      </button>

      {isOpen && (
        <div
          id={menuId}
          ref={refs.setFloating}
          style={{
            position: strategy,
            top: y ?? 0,
            left: x ?? 0,
            zIndex: 50,
          }}
          className={menuClassName}
          onClick={() => {
            setIsOpen(false);
            refs.reference.current?.focus();
          }}
          onKeyDown={handleKeyDown}
          role="menu"
        >
          {/* We trap focus inside by listening to Arrow keys, which is common for menus */}
          {children}
        </div>
      )}
    </>
  );
}