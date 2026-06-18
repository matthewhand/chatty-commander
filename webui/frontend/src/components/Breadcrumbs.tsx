import React from 'react';
import { Link, useLocation } from 'react-router-dom';

const HOME_PATH = '/dashboard';

const pathNameMap: Record<string, string> = {
    '/dashboard': 'Dashboard',
    '/commands': 'Commands',
    '/commands/authoring': 'Command Authoring',
    '/configuration': 'Configuration',
    '/voice-test': 'Voice Test',
};

function labelFor(path: string, segment: string): string {
    return pathNameMap[path] ?? segment.charAt(0).toUpperCase() + segment.slice(1);
}

const Breadcrumbs: React.FC = () => {
    const location = useLocation();
    const pathname = location.pathname;

    // Build breadcrumb segments from the current path.
    const segments = pathname.split('/').filter(Boolean);

    const crumbs: { label: string; path: string }[] = [];

    let accumulated = '';
    for (const segment of segments) {
        accumulated += `/${segment}`;
        crumbs.push({ label: labelFor(accumulated, segment), path: accumulated });
    }

    // Prepend a synthetic "Home" crumb, but dedupe it when the first real
    // segment already resolves to Home (avoids "Home / Dashboard" at /dashboard).
    if (crumbs[0]?.path !== HOME_PATH) {
        crumbs.unshift({ label: 'Home', path: HOME_PATH });
    }

    // Don't render breadcrumbs if we're just at the home/dashboard level.
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
                            <span aria-current="page">{crumb.label}</span>
                        )}
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default Breadcrumbs;
