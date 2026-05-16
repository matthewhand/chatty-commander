## 2024-06-25 - Explicit ID & Label Linking in Dynamic Components
**Learning:** When building dynamic form lists in React (like mapping over an array of custom inputs), using implicit labels (`<label><input/></label>`) isn't always feasible, but simply placing `<label>` next to `<input>` with no mapping completely breaks screen reader association.
**Action:** Always explicitly define uniquely generated IDs (e.g. ``id={`field-${index}`}``) and bind them directly using the `htmlFor` property on the label elements in dynamically generated components. Additionally, ensure bare `<textarea>` tags with placeholder text still have a proper `aria-label` or visually hidden label text to serve as the accessible name.

## 2024-07-26 - DaisyUI Modal Backdrop Labeling
**Learning:** When using the common DaisyUI pattern of `<form method="dialog">` wrapped around a hidden "close" button to create an invisible modal backdrop, leaving the inner button text as just "close" is technically accessible but highly ambiguous to screen readers if focused.
**Action:** Always explicitly add a descriptive `aria-label` (e.g., `aria-label="Close dialog"`) to the `<button>` element inside a `<form method="dialog" className="modal-backdrop">`, as it provides much better context for assistive technology users compared to the default inner text.
