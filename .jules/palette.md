
## 2024-05-15 - Form accessibility improvements
**Learning:** Found inputs lacking proper labeling in the `ConfigurationPage` (e.g. `llmBaseUrl`, `apiKey`, `llmModel`). Adding `id` to `input` and `htmlFor` to `label` links them together, which is crucial for screen readers and allows clicking the label to focus the input.
**Action:** Always ensure that form labels are explicitly associated with their inputs using `htmlFor` and `id` across the application to enhance accessibility.
