import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

// Unit-test configuration. Playwright e2e specs live in tests/e2e and are
// run separately via `npm run test:e2e`; they must never be collected here.
export default defineConfig({
    plugins: [
        react(),
    ],
    test: {
        environment: 'jsdom',
        globals: true,
        setupFiles: ['./src/setupTests.ts'],
        include: ['src/**/*.{test,spec}.{ts,tsx,js,jsx}'],
        exclude: ['node_modules/**', 'tests/e2e/**', 'build/**'],
    },
})
