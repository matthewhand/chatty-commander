# Palette's Journal - UX Learnings

This journal records critical UX and accessibility learnings for the Chatty Commander project.

## 2024-05-23 - Initial Setup
**Learning:** Accessibility should be built-in, not bolted on. Icon-only buttons are a common accessibility anti-pattern if not properly labeled.
**Action:** Systematically audit all icon-only buttons for `aria-label` and tooltip presence.

## 2024-05-23 - Accessibility & Micro-UX Additions
**Learning:** Icon-only buttons (like error dismissals and model deletions) frequently lack `aria-label`s, preventing screen readers from understanding their purpose. Also, async operations (like deletions) bound to lists without granular loading states can leave users wondering if their action registered.
**Action:** Always add `aria-label`s to icon-only buttons. Consider conditionally rendering a small spinner component in place of an icon for actions bound to `useMutation` that take noticeable time.

## 2026-03-28 - Actionable Empty States and Custom Component A11y
**Learning:** Bare text for empty states or zero-results states is unhelpful. Users benefit from clear visual indicators (icons) and actionable next steps. Also, custom reusable components like dropdown triggers often forget `ariaLabel` props, making them inaccessible when they wrap icon-only buttons.
**Action:** Always replace bare text empty states with an illustrative icon (e.g., from `lucide-react`), explanatory text, and a primary call-to-action button, utilizing existing DaisyUI utility classes (`bg-base-200/50`, `rounded-box`). Ensure custom UI components with icon-only triggers accept an optional `ariaLabel` prop with sensible default fallbacks.
## 2025-04-03 - Dynamic form lists and htmlFor associations
**Learning:** When building dynamic lists of form components (like the Action field list in Command Authoring) in React where elements might be added or removed, it is crucial to use the array `index` (or a unique ID from the list item itself) to generate globally unique `id` and `htmlFor` attributes to maintain screen reader and click-to-focus accessibility. Using simple, static `id`s will cause collisions and invalid HTML when multiple items are rendered.
**Action:** When creating or reviewing components that iterate over arrays to render inputs, actively look for and apply `id={`prefix-${index}`}` and `htmlFor={`prefix-${index}`}` patterns.
