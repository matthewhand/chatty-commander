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
  ariaLabel = "Open options menu"
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
          ref={refs.setFloating}
          style={{
            position: strategy,
            top: y ?? 0,
            left: x ?? 0,
            zIndex: 50,
          }}
          className={menuClassName}
          onClick={() => setIsOpen(false)} // close on item click
        >
          {children}
        </div>
      )}
    </>
  );
}