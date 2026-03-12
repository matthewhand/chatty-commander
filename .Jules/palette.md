# Palette's Journal - UX Learnings

This journal records critical UX and accessibility learnings for the Chatty Commander project.

## 2024-05-23 - Initial Setup
**Learning:** Accessibility should be built-in, not bolted on. Icon-only buttons are a common accessibility anti-pattern if not properly labeled.
**Action:** Systematically audit all icon-only buttons for `aria-label` and tooltip presence.

## 2024-05-23 - Accessibility & Micro-UX Additions
**Learning:** Icon-only buttons (like error dismissals and model deletions) frequently lack `aria-label`s, preventing screen readers from understanding their purpose. Also, async operations (like deletions) bound to lists without granular loading states can leave users wondering if their action registered.
**Action:** Always add `aria-label`s to icon-only buttons. Consider conditionally rendering a small spinner component in place of an icon for actions bound to `useMutation` that take noticeable time.

## 2024-05-23 - Actionable Empty States
**Learning:** Bare text empty states (e.g. "No commands") leave users at a dead end. Providing a clear illustration (icon) and an actionable call-to-action (like "Create Command" or "Clear Search") immediately guides the user to the next logical step.
**Action:** Always design empty states as starting points. Include a descriptive icon, helpful text, and a primary button to resolve the empty state.
