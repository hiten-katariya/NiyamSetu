import React from 'react';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string;
  subtitle?: string;
  action?: React.ReactNode;
}

export const Card: React.FC<CardProps> = ({
  title,
  subtitle,
  action,
  children,
  className = '',
  ...props
}) => {
  return (
    <div
      className={`bg-niyam-surface rounded-lg border border-niyam-border shadow-sm p-5 transition-shadow hover:shadow ${className}`}
      {...props}
    >
      {(title || action) && (
        <div className="flex items-center justify-between pb-3 mb-4 border-b border-niyam-border">
          <div>
            {title && <h3 className="text-base font-semibold text-niyam-text">{title}</h3>}
            {subtitle && <p className="text-xs text-niyam-text-muted mt-0.5">{subtitle}</p>}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      {children}
    </div>
  );
};
