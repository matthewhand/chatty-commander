## 2024-05-28 - DaisyUI Form Label Accessibility
**Learning:** DaisyUI `form-control` wrappers look visually like they connect labels and inputs, but screen readers require standard HTML linking (`id` on input, `htmlFor` on label) for proper accessibility.
**Action:** Always verify `htmlFor` and `id` linking is present when using DaisyUI form wrappers, especially on critical unauthenticated flows like the login page.
