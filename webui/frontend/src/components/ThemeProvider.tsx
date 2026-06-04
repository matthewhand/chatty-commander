import React, { createContext, useContext, useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';

interface ThemeContextType {
    theme: string;
    setTheme: (theme: string) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
    const [theme, setTheme] = useState<string>('dark'); // Default to dark

    // Fetch initial theme from backend configuration
    useQuery({
        queryKey: ['configTheme'],
        queryFn: async () => {
            try {
                const res = await fetch("/api/v1/config");
                if (res.ok) {
                    const data = await res.json();
                    if (data.ui?.theme) {
                        setTheme(data.ui.theme);
                        return data.ui.theme;
                    }
                }
            } catch { /* ignore */ }
            return 'dark'; // Fallback
        },
        staleTime: Infinity, // Only fetch once on mount
    });

    // Apply theme to the HTML document root for DaisyUI
    useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme);
    }, [theme]);

    return (
        <ThemeContext.Provider value={{ theme, setTheme }}>
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
