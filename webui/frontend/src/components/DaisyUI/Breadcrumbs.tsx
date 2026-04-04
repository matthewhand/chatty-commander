import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Home } from 'lucide-react';

const ROUTE_LABELS: Record<string, string> = {
  dashboard: 'Dashboard',
  commands: 'Commands',
  authoring: 'Authoring',
  configuration: 'Configuration',
  login: 'Login',
};

function getSegmentLabel(segment: string): string {
  if (ROUTE_LABELS[segment]) return ROUTE_LABELS[segment];
  return segment.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}

export interface BreadcrumbItem { label: string; href: string; isActive?: boolean; }
export interface BreadcrumbsProps { items?: BreadcrumbItem[]; }

const Breadcrumbs: React.FC<BreadcrumbsProps> = ({ items }) => {
  const location = useLocation();

  type Crumb = { label: string; path: string; isActive: boolean };
  let crumbs: Crumb[];

  if (items) {
    crumbs = items.map(item => ({ label: item.label, path: item.href, isActive: !!item.isActive }));
  } else {
    const segments = location.pathname.split('/').filter(Boolean);
    if (segments.length === 0 || (segments.length === 1 && segments[0] === 'login')) return null;
    crumbs = [];
    let currentPath = '';
    segments.forEach((segment, index) => {
      currentPath += `/${segment}`;
      crumbs.push({ label: getSegmentLabel(segment), path: currentPath, isActive: index === segments.length - 1 });
    });
  }

  return (
    <nav className="breadcrumbs text-sm mb-4" aria-label="Breadcrumb">
      <ul>
        <li>
          <Link to="/" className="inline-flex items-center gap-1 text-base-content/60 hover:text-primary transition-colors">
            <Home className="w-4 h-4" /> Home
          </Link>
        </li>
        {crumbs.map((crumb, index) => {
          const isLast = items ? !!crumb.isActive : index === crumbs.length - 1;
          return (
            <li key={crumb.path}>
              {isLast ? (
                <span className="text-base-content font-medium" aria-current="page">{crumb.label}</span>
              ) : (
                <Link to={crumb.path} className="text-base-content/60 hover:text-primary transition-colors">{crumb.label}</Link>
              )}
            </li>
          );
        })}
      </ul>
    </nav>
  );
};

export default Breadcrumbs;
