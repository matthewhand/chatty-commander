# Palette's Journal - UX Learnings

This journal records critical UX and accessibility learnings for the Chatty Commander project.

## 2024-05-23 - Initial Setup
**Learning:** Accessibility should be built-in, not bolted on. Icon-only buttons are a common accessibility anti-pattern if not properly labeled.
**Action:** Systematically audit all icon-only buttons for `aria-label` and tooltip presence.

## 2024-05-23 - Accessibility & Micro-UX Additions
**Learning:** Icon-only buttons (like error dismissals and model deletions) frequently lack `aria-label`s, preventing screen readers from understanding their purpose. Also, async operations (like deletions) bound to lists without granular loading states can leave users wondering if their action registered.
**Action:** Always add `aria-label`s to icon-only buttons. Consider conditionally rendering a small spinner component in place of an icon for actions bound to `useMutation` that take noticeable time.
## 2026-03-18 - Actionable Empty States
**Learning:** Users encountering empty states (like empty lists or search results) need actionable next steps rather than bare text dead ends to maintain engagement and guide discovery.
**Action:** Use an illustrative icon, brief explanatory text, and a primary call-to-action button (using DaisyUI utility classes) when designing empty states.
