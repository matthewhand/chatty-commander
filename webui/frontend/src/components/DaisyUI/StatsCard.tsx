import React from 'react';

export interface StatsCardProps {
  title: string;
  value: string | number;
  description?: string;
  icon?: React.ReactNode;
  color?: string;
  className?: string;
}

/**
 * Shared stats card component wrapping the DaisyUI `.stats > .stat` pattern.
 *
 * Matches the stat cards used on the DashboardPage:
 * `.stats shadow bg-base-100 border border-base-content/10`
 *
 * The `color` prop applies a text color class to the stat-figure and stat-value
 * (e.g. "text-primary", "text-info"). Defaults to "text-primary".
 */
export const StatsCard: React.FC<StatsCardProps> = React.memo(({
  title,
  value,
  description,
  icon,
  color = 'text-primary',
  className = '',
}) => {
  return (
    <div className={`stats shadow bg-base-100 border border-base-content/10 ${className}`.trim()}>
      <div className="stat">
        {icon && (
          <div className={`stat-figure ${color}`}>
            {icon}
          </div>
        )}
        <div className="stat-title">{title}</div>
        <div className={`stat-value ${color}`}>{value}</div>
        {description && (
          <div className="stat-desc">{description}</div>
        )}
      </div>
    </div>
  );
});

StatsCard.displayName = 'StatsCard';

export default StatsCard;
