## Palette's Journal
## 2025-03-09 - Accessible Form Inputs

**Learning:** When developing form inputs, standard HTML linking by assigning an `id` to the `<input>` and a matching `htmlFor` to the associated `<label>` is critical for accessibility. It supports screen readers by providing context and enables click-to-focus behavior, improving the UX for all users.
**Action:** Always verify that every form input field (e.g., text, password, select) has a corresponding `<label>` correctly linked via `id` and `htmlFor` attributes in React components, like what was done in `LoginPage.tsx`.
