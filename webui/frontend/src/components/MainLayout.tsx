import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
    LayoutDashboard as DashboardIcon,
    Settings as SettingsIcon,
    Terminal as TerminalIcon,
    LogOut as LogoutIcon,
    Wand2,
    Menu as MenuIcon,
    X as CloseIcon
} from "lucide-react";
import { useAuth } from '../hooks/useAuth';
import ScrollToTop from './ScrollToTop';
import Breadcrumbs from './Breadcrumbs';

const MainLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { logout } = useAuth();
    const location = useLocation();
    const navigate = useNavigate();
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);

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

    const navItems = [
        { label: 'Dashboard', path: '/dashboard', icon: <DashboardIcon size={20} /> },
        { label: 'Commands', path: '/commands', icon: <TerminalIcon size={20} /> },
        { label: 'Command Authoring', path: '/commands/authoring', icon: <Wand2 size={20} /> },
        { label: 'Configuration', path: '/configuration', icon: <SettingsIcon size={20} /> },
    ];

    return (
        <div className="flex h-screen bg-base-200 font-sans text-base-content overflow-hidden">
            {/* Mobile Backdrop */}
            {isSidebarOpen && (
                <div
                    className="fixed inset-0 bg-black/50 z-20 lg:hidden backdrop-blur-sm"
                    onClick={() => setIsSidebarOpen(false)}
                />
            )}

            {/* Sidebar */}
            <aside className={`
                w-64 bg-base-300 flex flex-col border-r border-base-content/10 fixed h-full z-30 overflow-y-auto
                transition-transform duration-300 ease-in-out
                ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'}
                lg:translate-x-0
            `}>
                {/* Header */}
                <div className="p-4 border-b border-base-content/10 bg-base-300 flex items-center justify-between">
                    <div>
                        <h1 className="text-xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
                            Chatty
                        </h1>
                        <p className="text-xs text-base-content/60">Voice Commander</p>
                    </div>
                    <button
                        className="lg:hidden p-2 hover:bg-base-content/10 rounded-lg"
                        onClick={() => setIsSidebarOpen(false)}
                        aria-label="Close sidebar"
                    >
                        <CloseIcon size={20} />
                    </button>
                </div>

                {/* Menu */}
                <ul className="menu p-4 w-full flex-1 gap-2">
                    {navItems.map((item) => {
                        const isActive = location.pathname === item.path;
                        return (
                            <li key={item.path}>
                                <Link
                                    to={item.path}
                                    className={`${isActive ? 'active bg-primary/20 text-primary border-l-4 border-primary' : 'hover:bg-base-content/10'} transition-all flex items-center gap-3 p-3 rounded-xl`}
                                >
                                    <span className={isActive ? 'text-primary' : 'text-base-content/70'}>
                                        {item.icon}
                                    </span>
                                    <span className="font-medium">{item.label}</span>
                                </Link>
                            </li>
                        );
                    })}
                </ul>

                {/* Footer actions */}
                <div className="p-4 border-t border-base-content/10 bg-base-300">
                    <ul className="menu w-full p-0">
                        <li>
                            <button onClick={logout} className="text-error hover:bg-error/10">
                                <LogoutIcon size={20} />
                                Logout
                            </button>
                        </li>
                    </ul>
                </div>
            </aside>

            <ScrollToTop />

            {/* Main Content */}
            <div className="flex-1 lg:ml-64 flex flex-col min-h-screen">
                {/* Mobile Header */}
                <header className="lg:hidden h-16 bg-base-300 flex items-center px-4 border-b border-base-content/10 gap-4">
                    <button
                        className="p-2 hover:bg-base-content/10 rounded-lg"
                        onClick={() => setIsSidebarOpen(true)}
                        aria-label="Open sidebar"
                    >
                        <MenuIcon size={24} />
                    </button>
                    <div className="font-bold">Chatty Commander</div>
                </header>

                {/* Content Scroll Area */}
                <main className="flex-1 overflow-y-auto p-4 md:p-6 ml-0">
                    <div className="max-w-7xl mx-auto space-y-6 animate-on-load">
                        <Breadcrumbs />
                        {children}
                    </div>
                </main>
            </div>
        </div>
    );
};

export default MainLayout;
