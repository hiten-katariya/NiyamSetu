import React from 'react';

export const LoadingState: React.FC<{ message?: string }> = ({ message = 'Loading...' }) => {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="w-8 h-8 border-3 border-niyam-primary border-t-transparent rounded-full animate-spin mb-3" />
      <p className="text-sm font-medium text-niyam-text-muted">{message}</p>
    </div>
  );
};

export const EmptyState: React.FC<{
  title: string;
  description: string;
  action?: React.ReactNode;
  icon?: React.ReactNode;
}> = ({ title, description, action, icon }) => {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center bg-niyam-surface rounded-lg border border-dashed border-niyam-border">
      {icon && <div className="mb-3 text-niyam-text-muted">{icon}</div>}
      <h4 className="text-base font-semibold text-niyam-text mb-1">{title}</h4>
      <p className="text-sm text-niyam-text-muted max-w-md mb-4">{description}</p>
      {action && <div>{action}</div>}
    </div>
  );
};

export const ErrorState: React.FC<{
  title?: string;
  message: string;
  onRetry?: () => void;
}> = ({ title = 'Failed to load data', message, onRetry }) => {
  return (
    <div className="p-4 rounded-lg bg-niyam-status-danger-bg border border-red-200 text-niyam-status-danger mb-4">
      <h4 className="font-semibold text-sm mb-1">{title}</h4>
      <p className="text-xs mb-3">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="text-xs font-semibold underline hover:text-red-900 cursor-pointer"
        >
          Try Again
        </button>
      )}
    </div>
  );
};
