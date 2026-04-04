import React from 'react';
import { Link, useLocation } from 'react-router-dom';

const pathNameMap: Record<string, string> = {
    '/dashboard': 'Dashboard',
    '/commands': 'Commands',
    '/commands/authoring': 'Command Editor',
    '/configuration': 'Configuration',
};

const Breadcrumbs: React.FC = () => {
    const location = useLocation();
    const pathname = location.pathname;

    // Build breadcrumb segments from the current path
    const segments = pathname.split('/').filter(Boolean);
    const crumbs: { label: string; path: string }[] = [
        { label: 'Home', path: '/dashboard' },
    ];

    let accumulated = '';
    for (const segment of segments) {
        accumulated += `/${segment}`;
        const label = pathNameMap[accumulated] || segment.charAt(0).toUpperCase() + segment.slice(1);
        crumbs.push({ label, path: accumulated });
    }

    // Don't render breadcrumbs if we're just at the home/dashboard level
    if (crumbs.length <= 1) {
        return null;
    }

    return (
        <div className="breadcrumbs text-sm">
            <ul>
                {crumbs.map((crumb, index) => (
                    <li key={crumb.path}>
                        {index < crumbs.length - 1 ? (
                            <Link to={crumb.path}>{crumb.label}</Link>
                        ) : (
                            <span>{crumb.label}</span>
                        )}
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default Breadcrumbs;
