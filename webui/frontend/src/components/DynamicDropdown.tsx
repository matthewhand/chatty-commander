import React, { useCallback, useEffect, useState } from 'react';
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

  const getItems = useCallback((): HTMLElement[] => {
    const panel = refs.floating.current;
    if (!panel) return [];
    // Target interactive elements within the panel.
    return Array.from(
      panel.querySelectorAll<HTMLElement>(
        'a[href]:not([disabled]), button:not([disabled]), [tabindex]:not([tabindex="-1"]), [role="menuitem"]'
      )
    ).filter(el => {
      // Allow jsdom test environment elements (where offsetWidth is 0) or real visible elements.
      return process.env.NODE_ENV === 'test' || el.offsetWidth > 0 || el.offsetHeight > 0 || el.getClientRects().length > 0;
    });
  }, [refs]);

  const focusItemAt = useCallback(
    (index: number) => {
      const items = getItems();
      if (items.length === 0) return;
      const clamped = (index + items.length) % items.length;

      // Update roving tabindex
      items.forEach((item, i) => {
        item.setAttribute('tabindex', i === clamped ? '0' : '-1');
      });

      items[clamped]?.focus();
    },
    [getItems],
  );

  const closeAndRestoreFocus = useCallback(() => {
    setIsOpen(false);
    if (refs.reference.current instanceof HTMLElement) {
      refs.reference.current.focus();
    }
  }, [refs]);

  // Handle clicking outside to close
  useEffect(() => {
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

  // Manage initial focus and semantics when menu opens
  useEffect(() => {
    if (!isOpen) return;
    const items = getItems();
    items.forEach((el, index) => {
      if (!el.getAttribute('role')) {
        el.setAttribute('role', 'menuitem');
      }
      // Initialize roving tabindex
      el.setAttribute('tabindex', index === 0 ? '0' : '-1');
    });

    // Use requestAnimationFrame to ensure DOM is painted before focusing
    const rafId = requestAnimationFrame(() => focusItemAt(0));
    return () => cancelAnimationFrame(rafId);
  }, [isOpen, getItems, focusItemAt]);

  const handlePanelKeyDown = useCallback(
    (event: React.KeyboardEvent<HTMLDivElement>) => {
      const items = getItems();
      const currentIndex = items.indexOf(
        document.activeElement as HTMLElement,
      );

      // Handle printable characters for type-ahead navigation
      if (event.key.length === 1 && !event.ctrlKey && !event.altKey && !event.metaKey) {
        const char = event.key.toLowerCase();
        // Start searching from next item, wrapping around
        const startIndex = currentIndex >= 0 ? (currentIndex + 1) % items.length : 0;

        for (let i = 0; i < items.length; i++) {
          const checkIndex = (startIndex + i) % items.length;
          const itemText = items[checkIndex].textContent?.trim().toLowerCase() || '';
          if (itemText.startsWith(char)) {
            event.preventDefault();
            focusItemAt(checkIndex);
            return;
          }
        }
      }

      switch (event.key) {
        case 'Escape':
          event.preventDefault();
          closeAndRestoreFocus();
          break;
        case 'ArrowDown':
          event.preventDefault();
          focusItemAt(currentIndex < 0 ? 0 : currentIndex + 1);
          break;
        case 'ArrowUp':
          event.preventDefault();
          focusItemAt(currentIndex < 0 ? items.length - 1 : currentIndex - 1);
          break;
        case 'Home':
          event.preventDefault();
          focusItemAt(0);
          break;
        case 'End':
          event.preventDefault();
          focusItemAt(items.length - 1);
          break;
        case 'Tab':
          // Close menu and let browser handle tab navigation
          setIsOpen(false);
          break;
        default:
          break;
      }
    },
    [getItems, focusItemAt, closeAndRestoreFocus],
  );

  return (
    <>
      <button
        ref={refs.setReference}
        onClick={() => setIsOpen((prev) => !prev)}
        onKeyDown={(event) => {
          if (!isOpen && (event.key === 'ArrowDown' || event.key === 'ArrowUp')) {
            event.preventDefault();
            setIsOpen(true);
          }
        }}
        className={buttonClassName}
        aria-expanded={isOpen}
        aria-haspopup="menu"
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
          role="menu"
          aria-label={ariaLabel}
          onKeyDown={handlePanelKeyDown}
          onClick={() => setIsOpen(false)} // close on item click
        >
          {children}
        </div>
      )}
    </>
  );
}
