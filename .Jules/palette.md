# Palette's Journal - UX Learnings

This journal records critical UX and accessibility learnings for the Chatty Commander project.

## 2024-05-23 - Initial Setup
**Learning:** Accessibility should be built-in, not bolted on. Icon-only buttons are a common accessibility anti-pattern if not properly labeled.
**Action:** Systematically audit all icon-only buttons for `aria-label` and tooltip presence.

## 2024-05-23 - Accessibility & Micro-UX Additions
**Learning:** Icon-only buttons (like error dismissals and model deletions) frequently lack `aria-label`s, preventing screen readers from understanding their purpose. Also, async operations (like deletions) bound to lists without granular loading states can leave users wondering if their action registered.
**Action:** Always add `aria-label`s to icon-only buttons. Consider conditionally rendering a small spinner component in place of an icon for actions bound to `useMutation` that take noticeable time.

## 2025-02-28 - Explicit Label Association with DaisyUI Form Controls
**Learning:** DaisyUI's `form-control` wrapper classes do not inherently link labels to inputs. Missing standard HTML `id`/`htmlFor` bindings degrades screen reader compatibility and prevents users from clicking labels to focus inputs.
**Action:** When creating forms or reviewing `form-control` components, explicitly ensure `id` on inputs and a matching `htmlFor` on `<label>` elements are present. Enhance UX by adding the `cursor-pointer` utility to labels.
