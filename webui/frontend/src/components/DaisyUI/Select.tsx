import type { SelectHTMLAttributes, ReactNode } from 'react';
import React, { forwardRef, useId, memo } from 'react';
import { twMerge } from 'tailwind-merge';

export type SelectOption = { label: string; value: string | number; disabled?: boolean };
export type SelectOptionGroup = { label: string; options: SelectOption[] };

export interface SelectProps extends Omit<SelectHTMLAttributes<HTMLSelectElement>, 'size'> {
  options?: SelectOption[];
  optionGroups?: SelectOptionGroup[];
  size?: 'xs' | 'sm' | 'md' | 'lg';
  variant?: 'primary' | 'secondary' | 'accent' | 'ghost' | 'info' | 'success' | 'warning' | 'error';
  bordered?: boolean;
  loading?: boolean;
  label?: ReactNode;
  error?: ReactNode;
  helperText?: ReactNode;
  renderOption?: (option: SelectOption) => ReactNode;
}

const Select = memo(forwardRef<HTMLSelectElement, SelectProps>(
  ({ options = [], optionGroups = [], size = 'md', variant, bordered = true, loading = false, 
     label, error, helperText, className, children, renderOption, id: providedId, ...props }, ref) => {
    const uniqueId = useId();
    const id = providedId || uniqueId;

    const variantClasses: Record<string, string> = {
      primary: 'select-primary', secondary: 'select-secondary', accent: 'select-accent',
      info: 'select-info', success: 'select-success', warning: 'select-warning', error: 'select-error',
    };
    const sizeClasses: Record<string, string> = {
      xs: 'select-xs', sm: 'select-sm', md: 'select-md', lg: 'select-lg',
    };

    const appliedVariant = error ? 'error' : variant;
    const selectClasses = twMerge(
      'select w-full',
      bordered && 'select-bordered',
      appliedVariant && variantClasses[appliedVariant],
      size && sizeClasses[size],
      loading && 'animate-pulse',
      className,
    );

    const renderSingleOption = (option: SelectOption) => {
      if (renderOption) return renderOption(option);
      return <option key={option.value} value={option.value} disabled={option.disabled}>{option.label}</option>;
    };

    const selectContent = (
      <div className="relative w-full">
        <select
          ref={ref} id={id}
          className={selectClasses}
          disabled={props.disabled || loading}
          aria-busy={loading || undefined}
          aria-invalid={!!error}
          aria-describedby={error ? `${id}-error` : helperText ? `${id}-helper` : undefined}
          {...props}
        >
          {children}
          {options.map(renderSingleOption)}
          {optionGroups.map((group) => (
            <optgroup key={group.label} label={group.label}>{group.options.map(renderSingleOption)}</optgroup>
          ))}
        </select>
        {loading && <span className="loading loading-spinner absolute right-8 top-1/2 -translate-y-1/2 w-4 h-4" aria-hidden="true" />}
      </div>
    );

    if (label || error || helperText) {
      return (
        <div className="form-control w-full">
          {label && <label htmlFor={id} className="label"><span className="label-text">{label}</span></label>}
          {selectContent}
          {error && <label className="label" id={`${id}-error`}><span className="label-text-alt text-error">{error}</span></label>}
          {helperText && !error && <label className="label" id={`${id}-helper`}><span className="label-text-alt text-base-content/60">{helperText}</span></label>}
        </div>
      );
    }

    return selectContent;
  },
));

Select.displayName = 'Select';
export default Select;
