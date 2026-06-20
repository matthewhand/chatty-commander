/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {},
    },
    plugins: [require("daisyui")],
    daisyui: {
        // Curated, intentionally distinct set: light + dark plus high-contrast /
        // neutral options. All exist in DaisyUI v4. Keep in sync with
        // AVAILABLE_THEMES in src/components/ThemeProvider.tsx.
        themes: ["light", "dark", "corporate", "business", "emerald", "nord"],
    },
}
