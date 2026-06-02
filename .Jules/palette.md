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

## 2026-04-18 - Fallback ARIA labels for dynamic dropdown triggers
**Learning:** Components like `Dropdown.tsx` wrap trigger elements that may just be text, but sometimes lack a provided `ariaLabel`. If an icon is used instead of text, `ariaLabel` is critical. But if text is provided via the `trigger` prop and `ariaLabel` is omitted, the component fell back to a generic 'Toggle dropdown' which overrides the visual text if voice control is used, violating WCAG 2.5.3 (Label in Name).
**Action:** Conditionally fallback `ariaLabel` to the string value of the `trigger` prop if one is provided and `ariaLabel` is omitted. This ensures voice control maps correctly to the visible text.
