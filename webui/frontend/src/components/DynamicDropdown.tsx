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

  // Returns the focusable menu items inside the floating panel, tagging each
  // with role="menuitem" so the menu has correct semantics. The children are
  // typically DaisyUI <li> wrappers around <a>/<button>, so we target the
  // actual interactive descendants for roving focus.
  const getItems = useCallback((): HTMLElement[] => {
    const panel = refs.floating.current;
    if (!panel) return [];
    return Array.from(
      panel.querySelectorAll<HTMLElement>('a, button, [role="menuitem"]'),
    );
  }, [refs]);

  const focusItemAt = useCallback(
    (index: number) => {
      const items = getItems();
      if (items.length === 0) return;
      const clamped = (index + items.length) % items.length;
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

  // Handle clicking outside to close (no focus restore: focus should follow
  // the user's click target, not jump back to the trigger).
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

  // When the menu opens, tag items as menuitems and move focus to the first one.
  useEffect(() => {
    if (!isOpen) return;
    const items = getItems();
    items.forEach((el) => {
      if (!el.getAttribute('role')) {
        el.setAttribute('role', 'menuitem');
      }
      // Items participate in roving focus; keep them keyboard-reachable.
      if (!el.hasAttribute('tabindex')) {
        el.setAttribute('tabindex', '-1');
      }
    });
    // Defer to ensure the floating panel is laid out before focusing.
    const raf = requestAnimationFrame(() => focusItemAt(0));
    return () => cancelAnimationFrame(raf);
  }, [isOpen, getItems, focusItemAt]);

  const handlePanelKeyDown = useCallback(
    (event: React.KeyboardEvent<HTMLDivElement>) => {
      const items = getItems();
      const currentIndex = items.indexOf(
        document.activeElement as HTMLElement,
      );
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
