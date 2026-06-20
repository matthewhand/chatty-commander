import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
    LayoutDashboard as DashboardIcon,
    Settings as SettingsIcon,
    Terminal as TerminalIcon,
    LogOut as LogoutIcon,
    Wand2,
    Mic as MicIcon,
    Menu as MenuIcon,
    X as CloseIcon,
    Palette as PaletteIcon
} from "lucide-react";
import { useAuth } from '../hooks/useAuth';
import ScrollToTop from './ScrollToTop';
import Breadcrumbs from './Breadcrumbs';
import ErrorBoundary from './ErrorBoundary';
import Logo from './Logo';
import { useTheme } from './ThemeProvider';

// Human-readable labels for the live themes (AVAILABLE_THEMES in ThemeProvider:
// light, dark, corporate, business, emerald, nord). Any unmapped theme falls
// back to a title-cased version of its id so a new/renamed theme can never
// silently render as a raw lowercase token again.
const THEME_LABELS: Record<string, string> = {
    light: 'Light',
    dark: 'Dark',
    corporate: 'Corporate',
    business: 'Business',
    emerald: 'Emerald',
    nord: 'Nord',
};

function themeLabelFor(theme: string): string {
    if (THEME_LABELS[theme]) {
        return THEME_LABELS[theme];
    }
    if (!theme) {
        return theme;
    }
    return theme.charAt(0).toUpperCase() + theme.slice(1);
}

const ThemeSwitcher: React.FC = () => {
    const { theme, setTheme, availableThemes } = useTheme();
    return (
        <label className="flex items-center gap-2 text-sm">
            <PaletteIcon size={20} className="text-base-content/70 shrink-0" aria-hidden="true" />
            <span className="sr-only">Theme</span>
            <select
                className="select select-sm select-bordered flex-1 min-h-[44px]"
                value={theme}
                onChange={(e) => setTheme(e.target.value)}
                aria-label="Select theme"
            >
                {availableThemes.map((t) => (
                    <option key={t} value={t}>
                        {themeLabelFor(t)}
                    </option>
                ))}
            </select>
        </label>
    );
};

const MainLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { logout } = useAuth();
    const location = useLocation();
    const navigate = useNavigate();
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);

    const asideRef = useRef<HTMLElement>(null);
    const closeButtonRef = useRef<HTMLButtonElement>(null);
    // Remembers the trigger so focus can return to it when the dialog closes.
    const lastTriggerRef = useRef<HTMLElement | null>(null);

    const closeSidebar = useCallback(() => setIsSidebarOpen(false), []);
    const openSidebar = useCallback(() => {
        lastTriggerRef.current = document.activeElement as HTMLElement | null;
        setIsSidebarOpen(true);
    }, []);

    // Close sidebar when route changes
    useEffect(() => {
        setIsSidebarOpen(false);
    }, [location.pathname]);

    // Global Ctrl+K / Cmd+K shortcut to navigate to Commands and focus search
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                navigate('/commands');
                // Focus the search input after navigation completes
                requestAnimationFrame(() => {
                    const searchInput = document.querySelector<HTMLInputElement>('input[aria-label="Search commands"]');
                    searchInput?.focus();
                });
            }
        };
        document.addEventListener('keydown', handleKeyDown);
        return () => document.removeEventListener('keydown', handleKeyDown);
    }, [navigate]);

    // Mobile sidebar behaves as a modal dialog: focus the close button on open,
    // trap Tab focus within the aside, close on Escape, and restore focus to the
    // trigger on close.
    useEffect(() => {
        if (!isSidebarOpen) {
            return;
        }

        // Focus the close button when the dialog opens.
        closeButtonRef.current?.focus();

        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Escape') {
                e.preventDefault();
                closeSidebar();
                return;
            }
            if (e.key !== 'Tab') {
                return;
            }
            const aside = asideRef.current;
            if (!aside) {
                return;
            }
            const focusable = aside.querySelectorAll<HTMLElement>(
                'a[href], button:not([disabled]), select, input, [tabindex]:not([tabindex="-1"])'
            );
            if (focusable.length === 0) {
                return;
            }
            const first = focusable[0];
            const last = focusable[focusable.length - 1];
            const active = document.activeElement;
            if (e.shiftKey) {
                if (active === first || !aside.contains(active)) {
                    e.preventDefault();
                    last.focus();
                }
            } else if (active === last) {
                e.preventDefault();
                first.focus();
            }
        };

        document.addEventListener('keydown', handleKeyDown);
        return () => {
            document.removeEventListener('keydown', handleKeyDown);
            // Restore focus to whatever opened the dialog.
            lastTriggerRef.current?.focus();
        };
    }, [isSidebarOpen, closeSidebar]);

    const navItems = [
        { label: 'Dashboard', path: '/dashboard', icon: <DashboardIcon size={20} /> },
        { label: 'Commands', path: '/commands', icon: <TerminalIcon size={20} /> },
        { label: 'Command Authoring', path: '/commands/authoring', icon: <Wand2 size={20} /> },
        { label: 'Voice Test', path: '/voice-test', icon: <MicIcon size={20} /> },
        { label: 'Configuration', path: '/configuration', icon: <SettingsIcon size={20} /> },
    ];

    return (
        <div className="flex h-screen bg-base-200 font-sans text-base-content overflow-hidden">
            <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:p-2 focus:bg-primary focus:text-primary-content focus:rounded">Skip to main content</a>
            {/* Mobile Backdrop */}
            {isSidebarOpen && (
                <button
                    type="button"
                    className="fixed inset-0 bg-black/50 z-20 lg:hidden backdrop-blur-sm"
                    aria-label="Close sidebar"
                    onClick={closeSidebar}
                />
            )}

            {/* Sidebar */}
            <aside
                ref={asideRef}
                id="app-sidebar"
                role={isSidebarOpen ? 'dialog' : undefined}
                aria-modal={isSidebarOpen ? true : undefined}
                aria-label="Main navigation"
                className={`
                w-64 bg-base-300 flex flex-col border-r border-base-content/10 fixed h-full z-30 overflow-y-auto
                transition-transform duration-300 ease-in-out
                ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'}
                lg:translate-x-0
            `}>
                {/* Header */}
                <div className="p-4 border-b border-base-content/10 bg-base-300 flex items-center justify-between">
                    <Link to="/dashboard" aria-label="ChattyCommander home" className="min-h-[44px] flex items-center">
                        <Logo size={28} className="text-lg" />
                    </Link>
                    <button
                        ref={closeButtonRef}
                        className="lg:hidden p-2 hover:bg-base-content/10 rounded-lg min-h-[44px] min-w-[44px] flex items-center justify-center"
                        onClick={closeSidebar}
                        aria-label="Close sidebar"
                    >
                        <CloseIcon size={20} />
                    </button>
                </div>

                {/* Menu */}
                <ul className="menu p-4 w-full flex-1 gap-2">
                    {navItems.map((item) => {
                        const isActive = location.pathname === item.path;
                        // Self-contained active state: high-contrast on neon themes,
                        // with a non-color cue (left bar + bold label) and
                        // aria-current for assistive tech. Does not rely on the
                        // .menu li>a.active CSS rule.
                        const activeClasses = isActive
                            ? 'bg-primary text-primary-content font-semibold ring-2 ring-primary border-l-4 border-primary-content/60'
                            : 'hover:bg-base-content/10 border-l-4 border-transparent';
                        return (
                            <li key={item.path}>
                                <Link
                                    to={item.path}
                                    aria-current={isActive ? 'page' : undefined}
                                    className={`${activeClasses} transition-all flex items-center gap-3 p-3 rounded-xl min-h-[44px]`}
                                >
                                    <span className={isActive ? 'text-primary-content' : 'text-base-content/70'}>
                                        {item.icon}
                                    </span>
                                    <span>{item.label}</span>
                                </Link>
                            </li>
                        );
                    })}
                </ul>

                {/* Footer actions */}
                <div className="p-4 border-t border-base-content/10 bg-base-300 space-y-3">
                    <ThemeSwitcher />
                    <ul className="menu w-full p-0">
                        <li>
                            <button
                                onClick={logout}
                                className="text-error hover:bg-error/10 min-h-[44px]"
                            >
                                <LogoutIcon size={20} />
                                Logout
                            </button>
                        </li>
                    </ul>
                </div>
            </aside>

            {/* Main Content */}
            <div className="flex-1 lg:ml-64 flex flex-col min-h-screen">
                {/* Mobile Header */}
                <header className="lg:hidden h-16 bg-base-300 flex items-center px-4 border-b border-base-content/10 gap-4">
                    <button
                        className="p-2 hover:bg-base-content/10 rounded-lg min-h-[44px] min-w-[44px] flex items-center justify-center"
                        onClick={openSidebar}
                        aria-label="Open sidebar"
                        aria-controls="app-sidebar"
                        aria-expanded={isSidebarOpen}
                    >
                        <MenuIcon size={24} />
                    </button>
                    <Link to="/dashboard" aria-label="ChattyCommander home" className="flex items-center">
                        <Logo size={24} className="text-base" />
                    </Link>
                </header>

                {/* Content Scroll Area */}
                <main id="main-content" className="flex-1 overflow-y-auto ml-0">
                    {/* Persistent desktop app bar: sticks to the top of the scroll
                        area so the breadcrumb and global controls stay visible
                        while content scrolls. It deliberately does NOT render the
                        page title — each page owns its own hero title, and
                        duplicating it here produced two visible headings / two
                        <h1>s. Hidden on mobile, which uses the dedicated mobile
                        header above. */}
                    <header
                        aria-label="Page toolbar"
                        className="hidden lg:flex sticky top-0 z-10 bg-base-100/95 backdrop-blur border-b border-base-content/10 px-6 py-3 items-center gap-4"
                    >
                        <div className="min-w-0 flex-1">
                            <Breadcrumbs />
                        </div>
                    </header>

                    <div className="p-4 md:p-6">
                        <div className="max-w-7xl mx-auto space-y-6 animate-on-load">
                            {/* Breadcrumb stays in-flow on mobile, where the sticky
                                desktop header is hidden. */}
                            <div className="lg:hidden">
                                <Breadcrumbs />
                            </div>
                            <ErrorBoundary>{children}</ErrorBoundary>
                        </div>
                    </div>
                </main>
            </div>

            {/* Scroll-to-top observes the actual scrolling <main> element. */}
            <ScrollToTop target="#main-content" />
        </div>
    );
};

export default MainLayout;
