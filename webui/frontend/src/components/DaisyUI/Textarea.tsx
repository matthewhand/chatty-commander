import type { TextareaHTMLAttributes } from 'react';
import React, { forwardRef } from 'react';

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  variant?: 'primary' | 'secondary' | 'accent' | 'info' | 'success' | 'warning' | 'error' | 'ghost';
  size?: 'xs' | 'sm' | 'md' | 'lg';
  bordered?: boolean;
  resize?: 'none' | 'vertical' | 'horizontal' | 'both';
}

const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className = '', variant = 'primary', size = 'md', bordered = true, resize = 'vertical', ...props }, ref) => {
    const variants: Record<string, string> = {
      primary: 'textarea-primary', secondary: 'textarea-secondary', accent: 'textarea-accent',
      info: 'textarea-info', success: 'textarea-success', warning: 'textarea-warning',
      error: 'textarea-error', ghost: 'textarea-ghost',
    };
    const sizes: Record<string, string> = { xs: 'textarea-xs', sm: 'textarea-sm', md: 'textarea-md', lg: 'textarea-lg' };
    const resizes: Record<string, string> = { none: 'resize-none', vertical: 'resize-y', horizontal: 'resize-x', both: 'resize' };

    return (
      <textarea ref={ref}
        className={`textarea ${variants[variant]} ${sizes[size]} ${bordered ? 'textarea-bordered' : ''} ${resizes[resize]} ${className}`}
        {...props} />
    );
  },
);

Textarea.displayName = 'Textarea';
export default Textarea;
