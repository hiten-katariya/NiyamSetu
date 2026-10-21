import React from 'react';

export interface BadgeProps {
  variant?: 'success' | 'warning' | 'danger' | 'info' | 'neutral';
  children: React.ReactNode;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  variant = 'neutral',
  children,
  className = '',
}) => {
  const variantStyles = {
    success: 'bg-niyam-status-success-bg text-niyam-status-success border-emerald-200',
    warning: 'bg-niyam-status-warning-bg text-niyam-status-warning border-amber-200',
    danger: 'bg-niyam-status-danger-bg text-niyam-status-danger border-rose-200',
    info: 'bg-niyam-primary-tint text-niyam-primary border-blue-200',
    neutral: 'bg-niyam-status-neutral-bg text-niyam-status-neutral border-slate-200',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${variantStyles[variant]} ${className}`}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current opacity-80" />
      {children}
    </span>
  );
};
