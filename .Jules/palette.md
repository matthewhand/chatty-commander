# Palette's Journal - UX Learnings

This journal records critical UX and accessibility learnings for the Chatty Commander project.

## 2024-05-23 - Initial Setup
**Learning:** Accessibility should be built-in, not bolted on. Icon-only buttons are a common accessibility anti-pattern if not properly labeled.
**Action:** Systematically audit all icon-only buttons for `aria-label` and tooltip presence.

## 2024-05-23 - Accessibility & Micro-UX Additions
**Learning:** Icon-only buttons (like error dismissals and model deletions) frequently lack `aria-label`s, preventing screen readers from understanding their purpose. Also, async operations (like deletions) bound to lists without granular loading states can leave users wondering if their action registered.
**Action:** Always add `aria-label`s to icon-only buttons. Consider conditionally rendering a small spinner component in place of an icon for actions bound to `useMutation` that take noticeable time.

## 2024-05-24 - Accessible Dynamic Components
**Learning:** Custom UI components, particularly those acting as wrappers for interactive elements like icon-only triggers (e.g., `DynamicDropdown`), often swallow accessibility attributes if they aren't explicitly forwarded or exposed as props. This breaks screen reader support for the underlying trigger button.
**Action:** When implementing custom UI components, ensure accessibility by using optional properties like `ariaLabel` with sensible default fallbacks. This guarantees baseline accessibility without breaking backward compatibility across shared components.
