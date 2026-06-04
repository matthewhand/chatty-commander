## 2024-06-25 - Explicit ID & Label Linking in Dynamic Components
**Learning:** When building dynamic form lists in React (like mapping over an array of custom inputs), using implicit labels (`<label><input/></label>`) isn't always feasible, but simply placing `<label>` next to `<input>` with no mapping completely breaks screen reader association.
**Action:** Always explicitly define uniquely generated IDs (e.g. ``id={`field-${index}`}``) and bind them directly using the `htmlFor` property on the label elements in dynamically generated components. Additionally, ensure bare `<textarea>` tags with placeholder text still have a proper `aria-label` or visually hidden label text to serve as the accessible name.

## 2024-05-11 - Add ARIA label to DaisyUI's form method="dialog" backdrop
**Learning:** DaisyUI uses `<form method="dialog">` for modal backdrops. The close button inside this form is visually hidden but still accessible to screen readers. If it simply contains the text "close", it lacks the necessary context for users utilizing screen readers to understand what exactly is being closed.
**Action:** Always explicitly add a descriptive `aria-label` (e.g., `aria-label="Close dialog"`) to the `<button>` inside `<form method="dialog" className="modal-backdrop">` to provide screen reader users with the proper context.
