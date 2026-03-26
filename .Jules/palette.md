# Palette's Journal - UX Learnings

This journal records critical UX and accessibility learnings for the Chatty Commander project.

## 2024-05-23 - Initial Setup
**Learning:** Accessibility should be built-in, not bolted on. Icon-only buttons are a common accessibility anti-pattern if not properly labeled.
**Action:** Systematically audit all icon-only buttons for `aria-label` and tooltip presence.

## 2024-05-23 - Accessibility & Micro-UX Additions
**Learning:** Icon-only buttons (like error dismissals and model deletions) frequently lack `aria-label`s, preventing screen readers from understanding their purpose. Also, async operations (like deletions) bound to lists without granular loading states can leave users wondering if their action registered.
**Action:** Always add `aria-label`s to icon-only buttons. Consider conditionally rendering a small spinner component in place of an icon for actions bound to `useMutation` that take noticeable time.

## 2024-06-11 - Actionable Empty States
**Learning:** Bare text empty states (like "No commands configured" or "No results found") create dead ends in the user flow. When users encounter an empty state, they often don't know what to do next or are discouraged from exploring.
**Action:** Replace bare text empty states with actionable ones. Provide an illustrative icon, explanatory text, and a primary call-to-action button (or a button to reset the current view, like clearing a search) utilizing existing utility classes.
