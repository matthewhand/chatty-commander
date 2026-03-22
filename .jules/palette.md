## 2024-03-22 - [Form Accessibility with DaisyUI]
**Learning:** For frontend accessibility, especially when using DaisyUI `form-control` wrappers, form inputs must use standard HTML linking by assigning an `id` to the `<input>` and a matching `htmlFor` to the associated `<label>`. This enables screen reader compatibility and allows users to click the label text to focus the input.
**Action:** Always verify that input fields have an explicitly linked label with matching `id` and `htmlFor` properties.
