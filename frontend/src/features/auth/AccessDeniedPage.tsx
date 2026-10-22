import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldAlert, ArrowLeft, Home } from 'lucide-react';
import { Button } from '../../components/Button';
import { useAuth } from '../../app/AuthContext';

export const AccessDeniedPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  return (
    <div className="min-h-[70vh] flex flex-col items-center justify-center text-center px-4">
      <div className="w-16 h-16 rounded-full bg-red-100 text-niyam-status-danger flex items-center justify-center mb-4 shadow-xs">
        <ShieldAlert className="w-8 h-8" />
      </div>

      <h1 className="text-2xl font-bold text-niyam-text mb-2">
        Access Restricted (403 Forbidden)
      </h1>

      <p className="text-sm text-niyam-text-muted max-w-md mb-4">
        Your current account role ({user?.role || 'unassigned'}) does not have permission to access this module or view records outside your authorised institutional or regional scope.
      </p>

      <div className="bg-niyam-surface-alt border border-niyam-border rounded-md p-3 text-xs text-niyam-text-muted max-w-md text-left mb-6">
        <p className="font-semibold text-niyam-text mb-1">Least-Privilege Enforcement Policy:</p>
        <p>
          In accordance with AICTE compliance governance, platform data access is strictly segmented by verified role, regional boundary, and assigned duty.
        </p>
      </div>

      <div className="flex gap-3">
        <Button variant="secondary" onClick={() => navigate(-1)} className="gap-1.5">
          <ArrowLeft className="w-4 h-4" />
          <span>Go Back</span>
        </Button>
        <Button variant="primary" onClick={() => navigate('/')} className="gap-1.5">
          <Home className="w-4 h-4" />
          <span>Return to Dashboard</span>
        </Button>
      </div>
    </div>
  );
};
