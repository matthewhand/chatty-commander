/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./src/**/*.{js,jsx,ts,tsx}",
    ],
    theme: {
        extend: {},
    },
    plugins: [require("daisyui")],
    daisyui: {
        themes: [
            "dark",
            "night",
            "light",
            "dracula",
            "cupcake",
            "emerald",
            "corporate",
            "synthwave",
            "cyberpunk",
            "forest",
            "aqua",
            "business",
            "coffee",
            "dim",
            "nord",
            "sunset"
        ],
    },
}
