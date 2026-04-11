import type { TextareaHTMLAttributes, ReactNode } from 'react';
import React, { forwardRef, useId, memo } from 'react';
import { twMerge } from 'tailwind-merge';

export interface TextareaProps extends Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, 'size'> {
  variant?: 'primary' | 'secondary' | 'accent' | 'info' | 'success' | 'warning' | 'error' | 'ghost';
  size?: 'xs' | 'sm' | 'md' | 'lg';
  bordered?: boolean;
  resize?: 'none' | 'vertical' | 'horizontal' | 'both';
  label?: ReactNode;
  error?: ReactNode;
  helperText?: ReactNode;
}

const Textarea = memo(forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, variant, size = 'md', bordered = true, resize = 'vertical', label, error, helperText, id: providedId, ...props }, ref) => {
    const uniqueId = useId();
    const id = providedId || uniqueId;

    const variantClasses: Record<string, string> = {
      primary: 'textarea-primary', secondary: 'textarea-secondary', accent: 'textarea-accent',
      info: 'textarea-info', success: 'textarea-success', warning: 'textarea-warning',
      error: 'textarea-error', ghost: 'textarea-ghost',
    };
    const sizeClasses: Record<string, string> = { 
      xs: 'textarea-xs', sm: 'textarea-sm', md: 'textarea-md', lg: 'textarea-lg' 
    };
    const resizeClasses: Record<string, string> = { 
      none: 'resize-none', vertical: 'resize-y', horizontal: 'resize-x', both: 'resize' 
    };

    const appliedVariant = error ? 'error' : variant;
    const textareaClasses = twMerge(
      'textarea w-full',
      bordered && 'textarea-bordered',
      appliedVariant && variantClasses[appliedVariant],
      size && sizeClasses[size],
      resize && resizeClasses[resize],
      className
    );

    const textareaContent = (
      <textarea
        ref={ref} id={id}
        className={textareaClasses}
        aria-invalid={!!error}
        aria-describedby={error ? `${id}-error` : helperText ? `${id}-helper` : undefined}
        {...props}
      />
    );

    if (label || error || helperText) {
      return (
        <div className="form-control w-full">
          {label && <label htmlFor={id} className="label"><span className="label-text">{label}</span></label>}
          {textareaContent}
          {error && <label className="label" id={`${id}-error`}><span className="label-text-alt text-error">{error}</span></label>}
          {helperText && !error && <label className="label" id={`${id}-helper`}><span className="label-text-alt text-base-content/60">{helperText}</span></label>}
        </div>
      );
    }

    return textareaContent;
  },
));

Textarea.displayName = 'Textarea';
export default Textarea;
