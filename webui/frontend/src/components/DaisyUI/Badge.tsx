import React from 'react';

export interface BadgeProps {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'accent' | 'success' | 'warning' | 'error' | 'info' | 'neutral' | 'ghost';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'small' | 'normal' | 'large';
  badgeStyle?: 'solid' | 'outline';
  icon?: React.ReactNode;
  avatar?: React.ReactNode;
  className?: string;
  'aria-label'?: string;
  role?: string;
}

export const Badge: React.FC<BadgeProps> = React.memo(({
  children, variant = 'neutral', size = 'md', badgeStyle = 'solid',
  icon, avatar, className = '', 'aria-label': ariaLabel, role = 'status', ...props
}) => {
  const variantClass = badgeStyle === 'outline' ? `badge-outline badge-${variant}` : `badge-${variant}`;
  
  const getSizeClass = () => {
    switch (size) {
      case 'xs':
      case 'small': return 'badge-xs';
      case 'sm': return 'badge-sm';
      case 'md':
      case 'normal': return 'badge-md';
      case 'lg':
      case 'large': return 'badge-lg';
      default: return 'badge-md';
    }
  };

  return (
    <span className={`badge ${variantClass} ${getSizeClass()} ${className}`.trim()} role={role} aria-label={ariaLabel} {...props}>
      {avatar && <span className="avatar placeholder">{avatar}</span>}
      {icon && <span className="mr-1">{icon}</span>}
      {children}
    </span>
  );
});

Badge.displayName = 'Badge';

export default Badge;
