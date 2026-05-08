## 2024-06-25 - Explicit ID & Label Linking in Dynamic Components
**Learning:** When building dynamic form lists in React (like mapping over an array of custom inputs), using implicit labels (`<label><input/></label>`) isn't always feasible, but simply placing `<label>` next to `<input>` with no mapping completely breaks screen reader association.
**Action:** Always explicitly define uniquely generated IDs (e.g. ``id={`field-${index}`}``) and bind them directly using the `htmlFor` property on the label elements in dynamically generated components. Additionally, ensure bare `<textarea>` tags with placeholder text still have a proper `aria-label` or visually hidden label text to serve as the accessible name.

## 2024-05-14 - Add ARIA label to DaisyUI modal backdrops
**Learning:** DaisyUI's `<form method="dialog">` modal backdrop pattern implicitly creates a hidden button for closing the dialog by clicking outside. While visually hidden and containing the text 'close', adding an explicit `aria-label="Close dialog"` ensures screen readers accurately convey the action (closing the dialog) rather than just reading the word "close" which might be ambiguous out of context.
**Action:** Always explicitly add a descriptive `aria-label` to visually hidden backdrop close buttons in DaisyUI modals.
