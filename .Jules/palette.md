# Palette's Journal - UX Learnings

This journal records critical UX and accessibility learnings for the Chatty Commander project.

## 2024-05-23 - Initial Setup
**Learning:** Accessibility should be built-in, not bolted on. Icon-only buttons are a common accessibility anti-pattern if not properly labeled.
**Action:** Systematically audit all icon-only buttons for `aria-label` and tooltip presence.

## 2024-05-23 - Accessibility & Micro-UX Additions
**Learning:** Icon-only buttons (like error dismissals and model deletions) frequently lack `aria-label`s, preventing screen readers from understanding their purpose. Also, async operations (like deletions) bound to lists without granular loading states can leave users wondering if their action registered.
**Action:** Always add `aria-label`s to icon-only buttons. Consider conditionally rendering a small spinner component in place of an icon for actions bound to `useMutation` that take noticeable time.

## 2024-05-24 - Redundant ARIA Labels
**Learning:** Adding `aria-label`s to elements that already have clearly visible and descriptive text content (like "Edit Command" or "Delete Command") is an anti-pattern. This causes screen readers to read the `aria-label` instead of the visible text, potentially confusing voice control users if the spoken label doesn't match the visible text.
**Action:** Only use `aria-label` when an element lacks sufficient visible text, such as icon-only buttons (e.g., dropdown triggers).
