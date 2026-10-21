import React from 'react';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, helperText, id, className = '', ...props }, ref) => {
    const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

    return (
      <div className="w-full">
        {label && (
          <label htmlFor={inputId} className="block text-sm font-medium text-niyam-text mb-1">
            {label}
            {props.required && <span className="text-niyam-status-danger ml-1">*</span>}
          </label>
        )}
        <input
          id={inputId}
          ref={ref}
          className={`w-full rounded border px-3 py-2 text-sm bg-niyam-surface text-niyam-text transition-colors placeholder:text-niyam-text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-niyam-focus ${
            error ? 'border-niyam-status-danger focus-visible:ring-niyam-status-danger' : 'border-niyam-border hover:border-niyam-text-muted'
          } ${className}`}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? `${inputId}-error` : helperText ? `${inputId}-desc` : undefined}
          {...props}
        />
        {error ? (
          <p id={`${inputId}-error`} className="text-xs text-niyam-status-danger mt-1">
            {error}
          </p>
        ) : helperText ? (
          <p id={`${inputId}-desc`} className="text-xs text-niyam-text-muted mt-1">
            {helperText}
          </p>
        ) : null}
      </div>
    );
  }
);

Input.displayName = 'Input';
