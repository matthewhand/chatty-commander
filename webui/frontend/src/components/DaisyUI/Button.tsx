import React, { memo, ElementType, ReactNode, ButtonHTMLAttributes, AnchorHTMLAttributes } from 'react';
import { Link, LinkProps } from 'react-router-dom';

export interface ButtonProps {
  children?: ReactNode;
  variant?: 'primary' | 'secondary' | 'accent' | 'ghost' | 'link' | 'info' | 'success' | 'warning' | 'error' | 'neutral';
  size?: 'xs' | 'sm' | 'md' | 'lg';
  shape?: 'circle' | 'square' | 'wide' | 'block';
  buttonStyle?: 'solid' | 'outline' | 'ghost' | 'glass';
  loading?: boolean;
  disabled?: boolean;
  active?: boolean;
  icon?: ReactNode;
  iconRight?: ReactNode;
  startIcon?: ReactNode;
  endIcon?: ReactNode;
  className?: string;
  loadingText?: string;
  as?: ElementType;
  to?: string;
  type?: 'button' | 'submit' | 'reset';
  onClick?: (event: React.MouseEvent<any>) => void;
  [key: string]: any;
}

export const Button = memo(({
  children,
  variant = 'primary',
  size = 'md',
  shape,
  buttonStyle = 'solid',
  loading = false,
  disabled = false,
  active = false,
  icon,
  iconRight,
  startIcon,
  endIcon,
  className = '',
  loadingText,
  as: Component = 'button',
  to,
  type = 'button',
  onClick,
  ...props
}: ButtonProps) => {
  const getVariantClass = () => {
    let classes = `btn-${variant}`;
    if (buttonStyle === 'outline') classes += ' btn-outline';
    if (buttonStyle === 'glass') classes += ' glass';
    return classes;
  };

  const getSizeClass = () => {
    switch (size) {
      case 'xs': return 'btn-xs';
      case 'sm': return 'btn-sm';
      case 'lg': return 'btn-lg';
      default: return '';
    }
  };

  const getShapeClass = () => {
    switch (shape) {
      case 'circle': return 'btn-circle';
      case 'square': return 'btn-square';
      case 'wide': return 'btn-wide';
      case 'block': return 'btn-block';
      default: return '';
    }
  };

  const getSpinnerSizeClass = () => {
    switch (size) {
      case 'xs': return 'loading-xs';
      case 'sm': return 'loading-sm';
      case 'lg': return 'loading-lg';
      default: return 'loading-md';
    }
  };

  const handleClick = (event: React.MouseEvent<any>) => {
    if (loading || disabled) {
      event.preventDefault();
      return;
    }
    onClick?.(event);
  };

  const hasTextContent = Boolean(loadingText || (children && React.Children.count(children) > 0));
  const isLink = Component === Link || Component === 'a' || !!to;
  const FinalComponent = to ? Link : Component;

  const combinedClassName = `btn ${getVariantClass()} ${getSizeClass()} ${getShapeClass()} ${active ? 'btn-active' : ''} ${disabled || loading ? 'btn-disabled' : ''} ${className}`.trim();

  return (
    <FinalComponent
      className={combinedClassName}
      disabled={disabled || loading}
      aria-busy={loading}
      onClick={handleClick}
      to={to}
      type={!isLink ? type : undefined}
      {...props}
    >
      {loading && <span className={`loading loading-spinner ${getSpinnerSizeClass()} ${hasTextContent ? 'mr-2' : ''}`.trim()} aria-hidden="true" />}
      {(icon || startIcon) && !loading && <span className="mr-2">{icon || startIcon}</span>}
      {loading && loadingText ? loadingText : children}
      {(iconRight || endIcon) && !loading && <span className="ml-2">{iconRight || endIcon}</span>}
    </FinalComponent>
  );
});

Button.displayName = 'Button';

export default Button;
