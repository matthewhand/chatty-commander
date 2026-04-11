import React, { forwardRef, useId, memo } from 'react';
import { twMerge } from 'tailwind-merge';

export interface FileInputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  variant?: 'primary' | 'secondary' | 'accent' | 'info' | 'success' | 'warning' | 'error' | 'ghost';
  size?: 'xs' | 'sm' | 'md' | 'lg';
  bordered?: boolean;
  label?: string;
  helperText?: string;
  error?: string;
}

export const FileInput = memo(forwardRef<HTMLInputElement, FileInputProps>(
  ({ variant = 'primary', size = 'md', bordered = true, label, helperText, error, className, id: providedId, ...props }, ref) => {
    const uniqueId = useId();
    const id = providedId || uniqueId;

    const variantClasses: Record<string, string> = {
      primary: 'file-input-primary',
      secondary: 'file-input-secondary',
      accent: 'file-input-accent',
      info: 'file-input-info',
      success: 'file-input-success',
      warning: 'file-input-warning',
      error: 'file-input-error',
      ghost: 'file-input-ghost',
    };

    const sizeClasses: Record<string, string> = {
      xs: 'file-input-xs',
      sm: 'file-input-sm',
      md: 'file-input-md',
      lg: 'file-input-lg',
    };

    const inputClasses = twMerge(
      'file-input w-full',
      bordered && 'file-input-bordered',
      variant && variantClasses[variant],
      size && sizeClasses[size],
      error && 'file-input-error',
      className
    );

    const inputElement = (
      <input
        ref={ref}
        id={id}
        type="file"
        className={inputClasses}
        aria-invalid={!!error}
        aria-describedby={error ? `${id}-error` : helperText ? `${id}-helper` : undefined}
        {...props}
      />
    );

    if (label || error || helperText) {
      return (
        <div className="form-control w-full">
          {label && (
            <label htmlFor={id} className="label">
              <span className="label-text font-medium">{label}</span>
            </label>
          )}
          {inputElement}
          {error && (
            <label className="label" id={`${id}-error`}>
              <span className="label-text-alt text-error">{error}</span>
            </label>
          )}
          {helperText && !error && (
            <label className="label" id={`${id}-helper`}>
              <span className="label-text-alt text-base-content/60">{helperText}</span>
            </label>
          )}
        </div>
      );
    }

    return inputElement;
  }
));

FileInput.displayName = 'FileInput';
export default FileInput;
