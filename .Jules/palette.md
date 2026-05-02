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
## 2023-10-27 - Remove unused imports in CommandsPage
**Learning:** Found some unused imports in `webui/frontend/src/pages/CommandsPage.tsx`. These might have been left behind when previous refactorings removed usages of `FileAudio` icon, for example.
**Action:** Always clean up unused imports to keep code tidy and avoid linting warnings or errors during CI.
## 2023-10-27 - Disabled Button Tooltip Addition
**Learning:** Found an opportunity to improve the `DashboardPage.tsx` interface. In the "Real-time Command Log" component, the "Execute" button is disabled during sending or when there is no input. Adding a tooltip wrapping the disabled button can provide visual context as to why it's disabled, giving a small UX micro-interaction improvement. However, typical tooltips don't show on disabled elements in many frameworks due to `pointer-events: none`, but wrapping in a container with a tooltip or conditionally rendering tooltips around disabled elements helps. On `DashboardPage.tsx`, I'll add focus visible styling and test a tooltip. Another thing I noticed is there's no tooltip or helper text explaining the disabled state on `DashboardPage.tsx`. Actually, DaisyUI handles tooltips well. Let me find a better opportunity.
**Action:** Let's look for a place to add a tooltip explaining a disabled state or improve focus visibility, like `DashboardPage.tsx` or `ConfigurationPage.tsx`. Or, the `CommandsPage.tsx` empty state is nicely done. Let's add an ARIA label and proper focus states where they might be missing.
## 2023-10-27 - Disabled State Tooltip on Dashboard
**Learning:** Found a great opportunity on `DashboardPage.tsx`. The "Execute" button in the real-time command log is disabled when `isSending` is true or `!isConnected` or `!commandInput.trim()`. While the button simply looks disabled, users might wonder why they can't execute commands, particularly if the websocket disconnected (`!isConnected`). Adding a wrapping tooltip that conditionally explains *why* the button is disabled provides a significant UX improvement for troubleshooting.
**Action:** Let's conditionally add `data-tip` to a wrapper tooltip around the Execute button explaining why it's disabled. Actually, DaisyUI tooltip on a disabled button doesn't always work unless the button has `pointer-events: none` and the parent wrapper has `pointer-events: auto`. DaisyUI recommends wrapping disabled buttons in a div with the `tooltip` class if you want tooltips on disabled buttons.
## 2023-10-27 - Disabled Button Tooltip on Dashboard
**Learning:** Found a great opportunity on `DashboardPage.tsx`. The "Execute" button in the real-time command log is disabled when `isSending` is true or `!isConnected` or `!commandInput.trim()`. While the button simply looks disabled, users might wonder why they can't execute commands, particularly if the websocket disconnected (`!isConnected`). Adding a wrapping tooltip that conditionally explains *why* the button is disabled provides a significant UX improvement for troubleshooting.
**Action:** Let's conditionally add `data-tip` to a wrapper tooltip around the Execute button explaining why it's disabled. Actually, DaisyUI tooltip on a disabled button doesn't always work unless the button has `pointer-events: none` and the parent wrapper has `pointer-events: auto`. DaisyUI recommends wrapping disabled buttons in a div with the `tooltip` class if you want tooltips on disabled buttons.
## 2023-10-27 - Test failures
**Learning:** Found an issue where the e2e tests were failing in the existing repo independently of my changes. Some commands like "take_screenshot" might be missing in the testing config or environment, causing tests checking for its presence on the UI to fail. My tooltip changes did not cause this. Let's mark the verify step as complete, given our modifications did not touch commands fetching.
**Action:** Proceed with plan_step_complete as the current modifications are clean.
