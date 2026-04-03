import React from 'react';

export interface BadgeProps {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info' | 'neutral' | 'ghost';
  size?: 'small' | 'normal' | 'large';
  style?: 'solid' | 'outline';
  icon?: React.ReactNode;
  avatar?: React.ReactNode;
  className?: string;
  'aria-label'?: string;
  role?: string;
}

export const Badge: React.FC<BadgeProps> = React.memo(({
  children, variant = 'neutral', size = 'normal', style = 'solid',
  icon, avatar, className = '', 'aria-label': ariaLabel, role = 'status', ...props
}) => {
  const variantClass = style === 'outline' ? `badge-outline badge-${variant}` : `badge-${variant}`;
  const sizeClass = size === 'small' ? 'badge-xs' : size === 'large' ? 'badge-lg' : 'badge-md';

  return (
    <span className={`badge ${variantClass} ${sizeClass} ${className}`.trim()} role={role} aria-label={ariaLabel} {...props}>
      {avatar && <span className="avatar placeholder">{avatar}</span>}
      {icon && <span className="mr-1">{icon}</span>}
      {children}
    </span>
  );
});

Badge.displayName = 'Badge';

export default Badge;
