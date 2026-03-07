## 2024-03-07 - Form Labels for Screen Readers
**Learning:** Adding visible text inside `<label>` tags is not enough for screen readers. Inputs must explicitly have an `id` that matches the `<label htmlFor="...">` attribute for proper form accessibility.
**Action:** Always ensure inputs have an `id` and are explicitly linked to their `<label>` using `htmlFor`. When visible labels are not desired (like a chat input), use `<label className="sr-only" htmlFor="input-id">Description</label>`.
