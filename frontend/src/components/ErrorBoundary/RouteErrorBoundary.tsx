import React from 'react';
import { useRouteError, isRouteErrorResponse, Link } from 'react-router-dom';
import { ShieldAlert, RefreshCw, Home } from 'lucide-react';
import { Button } from '../Button';

export const RouteErrorBoundary: React.FC = () => {
  const error = useRouteError();

  let title = 'Unexpected Application Error';
  let message = 'An unexpected error occurred while rendering this view. Our system integrity remains uncompromised.';
  let statusCode: number | null = null;

  if (isRouteErrorResponse(error)) {
    statusCode = error.status;
    title = error.status === 404 ? 'Page Not Found' : `HTTP Error ${error.status}`;
    message = error.statusText || message;
  } else if (error instanceof Error) {
    message = error.message;
  }

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-xl shadow-lg border border-niyam-border p-6 space-y-5 text-center">
        <div className="w-14 h-14 bg-rose-50 text-rose-600 rounded-full flex items-center justify-center mx-auto border border-rose-200">
          <ShieldAlert className="w-8 h-8" />
        </div>

        <div className="space-y-1">
          {statusCode && (
            <span className="text-[11px] font-mono uppercase tracking-wider text-rose-600 font-bold bg-rose-50 px-2 py-0.5 rounded">
              Error {statusCode}
            </span>
          )}
          <h2 className="text-xl font-bold text-niyam-text">{title}</h2>
          <p className="text-xs text-niyam-text-muted leading-relaxed">{message}</p>
        </div>

        <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-left text-[11px] text-slate-600 space-y-1">
          <p className="font-semibold text-slate-800">Operational Guarantee:</p>
          <p>Your session and audit trail are secure. You can safely reload the page or return to the main dashboard.</p>
        </div>

        <div className="flex items-center justify-center gap-3 pt-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => window.location.reload()}
            className="gap-1.5 text-xs"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Reload Page</span>
          </Button>

          <Link to="/">
            <Button variant="primary" size="sm" className="gap-1.5 text-xs">
              <Home className="w-3.5 h-3.5" />
              <span>Back to Dashboard</span>
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
};
