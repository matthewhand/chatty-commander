import React from 'react';

export interface StatsCardProps {
  title: string;
  value: string | number;
  description?: React.ReactNode;
  icon?: React.ReactNode;
  trend?: {
    value: number | string;
    isPositive: boolean;
  };
  color?: 'primary' | 'secondary' | 'accent' | 'info' | 'success' | 'warning' | 'error';
  className?: string;
}

export const StatsCard: React.FC<StatsCardProps> = React.memo(({
  title,
  value,
  description,
  icon,
  trend,
  color = 'primary',
  className = '',
}) => {
  const colorClass = `text-${color}`;

  return (
    <div className={`stats shadow bg-base-100 border border-base-content/10 ${className}`.trim()}>
      <div className="stat">
        {icon && (
          <div className={`stat-figure ${colorClass}`}>
            {icon}
          </div>
        )}
        <div className="stat-title text-base-content/60">{title}</div>
        <div className={`stat-value ${colorClass}`}>{value}</div>
        {(description || trend) && (
          <div className="stat-desc mt-1 flex items-center gap-1">
            {trend && (
              <span className={trend.isPositive ? 'text-success' : 'text-error'}>
                {trend.isPositive ? '↑' : '↓'} {trend.value}%
              </span>
            )}
            {description}
          </div>
        )}
      </div>
    </div>
  );
});

StatsCard.displayName = 'StatsCard';

export default StatsCard;
