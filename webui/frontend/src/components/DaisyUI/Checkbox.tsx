import React, { useEffect, useRef } from 'react';

export interface CheckboxProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  label?: string;
  children?: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'accent';
  size?: 'xs' | 'sm' | 'md' | 'lg';
  indeterminate?: boolean;
  className?: string;
  onChange?: (event: React.ChangeEvent<HTMLInputElement>) => void;
}

export const Checkbox: React.FC<CheckboxProps> = ({
  label, children, variant, size = 'md', indeterminate = false,
  className = '', checked, disabled, onChange, id, ...props
}) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const generatedId = React.useId();
  const inputId = id || `checkbox-${generatedId}`;

  useEffect(() => {
    if (inputRef.current) inputRef.current.indeterminate = indeterminate;
  }, [indeterminate]);

  const variantClass = variant ? `checkbox-${variant}` : '';
  const sizeClass = size === 'xs' ? 'checkbox-xs' : size === 'sm' ? 'checkbox-sm' : size === 'lg' ? 'checkbox-lg' : '';

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (inputRef.current && indeterminate) inputRef.current.indeterminate = false;
    onChange?.(event);
  };

  return (
    <div className={`form-control ${className}`.trim()}>
      <label htmlFor={inputId} className="label cursor-pointer">
        <input ref={inputRef} type="checkbox" id={inputId}
          className={`checkbox ${variantClass} ${sizeClass}`.trim()}
          checked={checked} disabled={disabled} onChange={handleChange}
          aria-checked={indeterminate ? 'mixed' : checked ? 'true' : 'false'}
          aria-describedby={label ? `${inputId}-label` : undefined} {...props} />
        {(label || children) && (
          <span id={label ? `${inputId}-label` : undefined} className="label-text ml-2">
            {label || children}
          </span>
        )}
      </label>
    </div>
  );
};

export default Checkbox;
