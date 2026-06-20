import React, { createContext, useContext, useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { logger } from '../utils/logger';

interface ThemeContextType {
    theme: string;
    setTheme: (theme: string) => void;
    /** Themes available to the in-app theme switcher. */
    availableThemes: readonly string[];
}

/**
 * DaisyUI themes enabled in tailwind.config.js. Keep this list in sync with the
 * `daisyui.themes` array there — a theme not enabled in Tailwind won't render.
 */
export const AVAILABLE_THEMES = ['light', 'dark', 'corporate', 'business', 'emerald', 'nord'] as const;

const STORAGE_KEY = 'chatty.theme';
const DEFAULT_THEME = 'dark';

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

function readStoredTheme(): string | null {
    try {
        const stored = window.localStorage.getItem(STORAGE_KEY);
        if (stored && (AVAILABLE_THEMES as readonly string[]).includes(stored)) {
            return stored;
        }
    } catch (e) {
        // localStorage may be unavailable (private mode, SSR); degrade quietly.
        logger.debug('ThemeProvider: could not read theme from localStorage', e);
    }
    return null;
}

function persistTheme(theme: string): void {
    try {
        window.localStorage.setItem(STORAGE_KEY, theme);
    } catch (e) {
        logger.debug('ThemeProvider: could not persist theme to localStorage', e);
    }
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
    // Prefer a previously persisted choice so a refresh keeps the theme even
    // before (or without) the backend config round-trip.
    const [theme, setThemeState] = useState<string>(() => readStoredTheme() ?? DEFAULT_THEME);
    // Tracks whether the user explicitly picked a theme this session. Once they
    // have, we don't let a slower /api/v1/config response stomp their choice.
    const [userOverride, setUserOverride] = useState<boolean>(() => readStoredTheme() !== null);

    const setTheme = (next: string) => {
        setThemeState(next);
        setUserOverride(true);
        persistTheme(next);
    };

    // Fetch initial theme from backend configuration (only honored when the user
    // has not already chosen/persisted a theme locally).
    useQuery({
        queryKey: ['configTheme'],
        queryFn: async () => {
            try {
                const res = await fetch('/api/v1/config');
                if (res.ok) {
                    const data = await res.json();
                    if (data.ui?.theme) {
                        if (!userOverride) {
                            setThemeState(data.ui.theme);
                            persistTheme(data.ui.theme);
                        }
                        return data.ui.theme;
                    }
                }
            } catch (e) {
                // Non-fatal: fall back to the default theme, but don't fail silently.
                logger.debug('ThemeProvider: could not load theme from /api/v1/config, using default', e);
            }
            return DEFAULT_THEME; // Fallback
        },
        staleTime: Infinity, // Only fetch once on mount
    });

    // Apply theme to the HTML document root for DaisyUI
    useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme);
    }, [theme]);

    return (
        <ThemeContext.Provider value={{ theme, setTheme, availableThemes: AVAILABLE_THEMES }}>
            {children}
        </ThemeContext.Provider>
    );
}

export function useTheme() {
    const context = useContext(ThemeContext);
    if (context === undefined) {
        throw new Error('useTheme must be used within a ThemeProvider');
    }
    return context;
}
