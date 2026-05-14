## 2024-06-25 - Explicit ID & Label Linking in Dynamic Components
**Learning:** When building dynamic form lists in React (like mapping over an array of custom inputs), using implicit labels (`<label><input/></label>`) isn't always feasible, but simply placing `<label>` next to `<input>` with no mapping completely breaks screen reader association.
**Action:** Always explicitly define uniquely generated IDs (e.g. `id={`field-${index}`}`) and bind them directly using the `htmlFor` property on the label elements in dynamically generated components. Additionally, ensure bare `<textarea>` tags with placeholder text still have a proper `aria-label` or visually hidden label text to serve as the accessible name.

## 2026-05-14 - Explicit aria-label for 'close' form modals in DaisyUI
**Learning:** When using DaisyUI's `<form method="dialog">` modal backdrop pattern, always explicitly add a descriptive `aria-label` (e.g., `aria-label="Close dialog"`) to the visually hidden `<button>`. Even if it contains the text 'close', a descriptive label provides better context for screen reader users about what exactly is being closed.
**Action:** Add `aria-label="Close dialog"` to the internal button of `<form method="dialog" className="modal-backdrop">`.
