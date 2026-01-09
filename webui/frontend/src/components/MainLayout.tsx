import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import DashboardIcon from '@mui/icons-material/Dashboard';
import SettingsIcon from '@mui/icons-material/Settings';
import MicIcon from '@mui/icons-material/Mic';
import GroupIcon from '@mui/icons-material/Group';
import AssessmentIcon from '@mui/icons-material/Assessment';
import LogoutIcon from '@mui/icons-material/Logout';
import { useAuth } from '../hooks/useAuth';

const MainLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { logout } = useAuth();
    const location = useLocation();

    // Mock mock status
    const systemHealthy = true;
    const hasErrors = false;

    const navItems = [
        { label: 'Dashboard', path: '/dashboard', icon: <DashboardIcon /> },
        { label: 'Configuration', path: '/configuration', icon: <SettingsIcon /> },
        { label: 'Audio Settings', path: '/audio-settings', icon: <MicIcon /> },
        { label: 'Personas', path: '/personas', icon: <GroupIcon /> },
        {
            label: 'Agent Status',
            path: '/agent-status',
            icon: <AssessmentIcon />,
            badge: hasErrors || !systemHealthy ? '!' : null,
            badgeColor: 'badge-error'
        },
    ];

    return (
        <div className="flex h-screen bg-base-200 font-sans text-base-content">
            {/* Sidebar */}
            <aside className="w-64 bg-base-300 flex flex-col border-r border-base-content/10 fixed h-full z-20 overflow-y-auto hidden lg:flex">
                {/* Header */}
                <div className="p-4 border-b border-base-content/10 bg-base-300">
                    <h1 className="text-xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
                        Chatty
                    </h1>
                    <p className="text-xs text-base-content/60">Voice Commander</p>
                </div>

                {/* Menu */}
                <ul className="menu p-4 w-full flex-1 gap-2">
                    {navItems.map((item) => {
                        const isActive = location.pathname === item.path;
                        return (
                            <li key={item.path}>
                                <Link
                                    to={item.path}
                                    className={`${isActive ? 'active bg-primary/20 text-primary border-l-4 border-primary' : 'hover:bg-base-content/10'} transition-all`}
                                >
                                    <span className={isActive ? 'text-primary' : 'text-base-content/70'}>
                                        {item.icon}
                                    </span>
                                    <span className="font-medium">{item.label}</span>
                                    {item.badge && (
                                        <span className={`badge ${item.badgeColor} badge-sm ml-auto animate-pulse`}>
                                            {item.badge}
                                        </span>
                                    )}
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
                                <LogoutIcon />
                                Logout
                            </button>
                        </li>
                    </ul>
                </div>
            </aside>

            {/* Main Content */}
            <div className="flex-1 lg:ml-64 flex flex-col min-h-screen">
                {/* Mobile Header (TODO: implement drawer toggle for mobile if needed) */}
                <header className="lg:hidden h-16 bg-base-300 flex items-center px-4 border-b border-base-content/10">
                    <div className="font-bold">Chatty Commander</div>
                </header>

                {/* Content Scroll Area */}
                <main className="flex-1 overflow-y-auto p-4 md:p-6 ml-0">
                    <div className="max-w-7xl mx-auto space-y-6 animate-on-load">
                        {children}
                    </div>
                </main>
            </div>
        </div>
    );
};

export default MainLayout;
