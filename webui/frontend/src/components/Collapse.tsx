import React, { useState } from "react";
import { ChevronDown } from "lucide-react";

export interface CollapseProps {
  /** Header label shown in the always-visible summary row. */
  title: React.ReactNode;
  /** Render expanded on first paint. Defaults to collapsed (secondary content). */
  defaultOpen?: boolean;
  /** Optional leading icon in the summary. */
  icon?: React.ReactNode;
  /** Optional trailing element in the summary (e.g. a count badge). */
  badge?: React.ReactNode;
  /** Extra classes for the outer <details> wrapper. */
  className?: string;
  children: React.ReactNode;
  "data-testid"?: string;
}

/**
 * Progressive-disclosure primitive: a DaisyUI-styled native <details>/<summary>.
 *
 * Used to keep secondary/diagnostic sections out of the way until a user opts in
 * — calmer pages, less scroll — while staying fully keyboard- and
 * screen-reader-accessible (native semantics) and themeable (base tokens only).
 * Prefer this over hand-rolling per-page collapsibles so disclosure looks and
 * behaves the same app-wide.
 */
const Collapse: React.FC<CollapseProps> = ({
  title,
  defaultOpen = false,
  icon,
  badge,
  className,
  children,
  ...rest
}) => {
  // Own the open state so the disclosure stays uncontrolled from the caller's
  // perspective: `defaultOpen` seeds the INITIAL state only (a later change to
  // the prop won't yank a section shut while the user is interacting with it),
  // and native summary toggles are synced back via onToggle.
  const [open, setOpen] = useState(defaultOpen);
  return (
    <details
      open={open}
      onToggle={(e) => setOpen((e.currentTarget as HTMLDetailsElement).open)}
      className={`group rounded-box border border-base-content/10 bg-base-100 shadow-sm ${className ?? ""}`.trim()}
      {...rest}
    >
      <summary className="flex items-center gap-2 cursor-pointer select-none px-4 py-3 font-bold list-none [&::-webkit-details-marker]:hidden">
        {icon}
        <span className="flex items-center gap-2">{title}</span>
        {badge != null && <span className="ml-1">{badge}</span>}
        <ChevronDown
          size={18}
          aria-hidden="true"
          className="ml-auto text-base-content/60 transition-transform duration-200 group-open:rotate-180"
        />
      </summary>
      <div className="px-4 pb-4 pt-1 border-t border-base-content/10">{children}</div>
    </details>
  );
};

export default Collapse;
