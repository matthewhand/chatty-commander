import React from 'react';

export interface PageHeaderProps {
  title: string;
  subtitle?: string;
  icon?: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
}

/**
 * Shared page header with gradient title styling used across all pages.
 *
 * Renders a responsive flex layout with a gradient title, optional subtitle,
 * optional leading icon, and an actions slot (e.g. buttons) on the right.
 */
export const PageHeader: React.FC<PageHeaderProps> = React.memo(({
  title,
  subtitle,
  icon,
  actions,
  className = '',
}) => {
  return (
    <div className={`flex flex-col md:flex-row justify-between items-start md:items-center gap-4 ${className}`.trim()}>
      <div>
        <h1 className="text-3xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent flex items-center gap-2">
          {icon && <span className="inline-flex">{icon}</span>}
          {title}
        </h1>
        {subtitle && (
          <p className="text-base-content/60 mt-1">{subtitle}</p>
        )}
      </div>
      {actions && (
        <div className="flex gap-2 flex-wrap">
          {actions}
        </div>
      )}
    </div>
  );
});

PageHeader.displayName = 'PageHeader';

export default PageHeader;
