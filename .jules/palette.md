## 2024-06-25 - Explicit ID & Label Linking in Dynamic Components
**Learning:** When building dynamic form lists in React (like mapping over an array of custom inputs), using implicit labels (`<label><input/></label>`) isn't always feasible, but simply placing `<label>` next to `<input>` with no mapping completely breaks screen reader association.
**Action:** Always explicitly define uniquely generated IDs (e.g. `id={\`field-${index}\`}`) and bind them directly using the `htmlFor` property on the label elements in dynamically generated components. Additionally, ensure bare `<textarea>` tags with placeholder text still have a proper `aria-label` or visually hidden label text to serve as the accessible name.

## 2024-06-25 - Descriptive ARIA Labels for Modal Backdrop Close Buttons
**Learning:** When using DaisyUI's `<form method="dialog">` modal backdrop pattern, the visually hidden close `<button>` inside it is often left as just `<button>close</button>`. This lacks context for screen reader users who might just hear "close button" without knowing what is being closed.
**Action:** Always explicitly add a descriptive `aria-label` (e.g., `aria-label="Close dialog"`) to the visually hidden `<button>` inside `<form method="dialog">` to provide better context for screen reader users.
