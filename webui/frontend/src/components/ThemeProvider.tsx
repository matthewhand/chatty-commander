import React, { createContext, useContext, useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';

interface ThemeContextType {
    theme: string;
    setTheme: (theme: string) => void;
    isLoading: boolean;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
    const [theme, setTheme] = useState<string>(() => {
        // Initialize from localStorage for faster load
        return localStorage.getItem('theme') || 'dark';
    });
    const [isInitialized, setIsInitialized] = useState(false);

    // Fetch initial theme from backend configuration
    const { isLoading } = useQuery({
        queryKey: ['configTheme'],
        queryFn: async () => {
            try {
                const res = await fetch("/api/v1/config");
                if (res.ok) {
                    const data = await res.json();
                    if (data.ui?.theme) {
                        setTheme(data.ui.theme);
                        localStorage.setItem('theme', data.ui.theme);
                        return data.ui.theme;
                    }
                }
            } catch (error) {
                console.warn('Failed to fetch theme from backend, using localStorage or default:', error);
            } finally {
                setIsInitialized(true);
            }
            return localStorage.getItem('theme') || 'dark'; // Fallback to localStorage or default
        },
        staleTime: Infinity, // Only fetch once on mount
    });

    // Apply theme to the HTML document root for DaisyUI
    useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme);
        // Persist to localStorage whenever theme changes
        localStorage.setItem('theme', theme);
    }, [theme]);

    return (
        <ThemeContext.Provider value={{ theme, setTheme, isLoading: !isInitialized }}>
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
