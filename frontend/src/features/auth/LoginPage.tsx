import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Shield, KeyRound, AlertTriangle } from 'lucide-react';
import { Button } from '../../components/Button';
import { Input } from '../../components/Input';
import { ApiClientError } from '../../lib/apiClient';
import { useAuth } from '../../app/AuthContext';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, isAuthenticated } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // If already authenticated, redirect to destination or home
  useEffect(() => {
    if (isAuthenticated) {
      const from = (location.state as { from?: { pathname?: string } })?.from?.pathname || '/';
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, location]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email || !password) {
      setError('Please provide both email and password.');
      return;
    }

    setIsLoading(true);
    try {
      await login(email, password);
      const from = (location.state as { from?: { pathname?: string } })?.from?.pathname || '/';
      navigate(from, { replace: true });
    } catch (err) {
      if (err instanceof ApiClientError) {
        if (err.status === 429) {
          setError('Too many failed login attempts. Please wait 5 minutes before trying again.');
        } else if (err.status === 403) {
          setError('Account has been deactivated. Contact the system administrator.');
        } else {
          setError(err.message || 'Invalid email or password.');
        }
      } else {
        setError('Login request failed. Verify backend service is running.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const fillDemoCredentials = (roleEmail: string) => {
    setEmail(roleEmail);
    setPassword('ChangeMeDev123!');
  };

  return (
    <div className="min-h-screen bg-niyam-bg flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="w-12 h-12 rounded-lg bg-niyam-primary text-white font-bold flex items-center justify-center text-lg mx-auto shadow-md">
          NS
        </div>
        <h2 className="mt-4 text-2xl font-bold text-niyam-text tracking-tight">
          NiyamSetu
        </h2>
        <p className="mt-1 text-xs text-niyam-text-muted">
          AICTE Workflow & Statutory Compliance Monitoring Platform
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-niyam-surface py-8 px-6 shadow-sm border border-niyam-border rounded-lg sm:px-10">
          {error && (
            <div className="mb-4 p-3 rounded bg-red-50 border border-red-200 text-niyam-status-danger text-xs font-medium flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Email Address"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="user@niyamsetu.local"
              required
              autoComplete="email"
            />

            <Input
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              autoComplete="current-password"
            />

            <Button
              type="submit"
              variant="primary"
              className="w-full mt-2"
              isLoading={isLoading}
            >
              Sign In to NiyamSetu
            </Button>
          </form>

          {/* Demonstration Quick-Fill Helper */}
          <div className="mt-6 pt-6 border-t border-niyam-border">
            <div className="flex items-center gap-1.5 mb-2 text-xs font-semibold text-niyam-text-muted">
              <Shield className="w-3.5 h-3.5 text-niyam-primary" />
              <span>Development Demonstration Accounts</span>
            </div>
            <p className="text-[11px] text-niyam-text-muted mb-3">
              Click any synthetic role account below to pre-fill test credentials:
            </p>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <button
                type="button"
                onClick={() => fillDemoCredentials('scrutiny.officer@niyamsetu.local')}
                className="p-1.5 rounded border border-niyam-border hover:bg-niyam-surface-alt text-left text-[11px] font-medium text-niyam-text"
              >
                Scrutiny Officer
              </button>
              <button
                type="button"
                onClick={() => fillDemoCredentials('ro.north@niyamsetu.local')}
                className="p-1.5 rounded border border-niyam-border hover:bg-niyam-surface-alt text-left text-[11px] font-medium text-niyam-text"
              >
                Regional Officer
              </button>
              <button
                type="button"
                onClick={() => fillDemoCredentials('institution.user@apex-demo.edu')}
                className="p-1.5 rounded border border-niyam-border hover:bg-niyam-surface-alt text-left text-[11px] font-medium text-niyam-text"
              >
                Institution User
              </button>
              <button
                type="button"
                onClick={() => fillDemoCredentials('admin@niyamsetu.local')}
                className="p-1.5 rounded border border-niyam-border hover:bg-niyam-surface-alt text-left text-[11px] font-medium text-niyam-text"
              >
                System Admin
              </button>
              <button
                type="button"
                onClick={() => fillDemoCredentials('committee.member@niyamsetu.local')}
                className="p-1.5 rounded border border-niyam-border hover:bg-niyam-surface-alt text-left text-[11px] font-medium text-niyam-text"
              >
                Committee Member
              </button>
              <button
                type="button"
                onClick={() => fillDemoCredentials('senior.authority@niyamsetu.local')}
                className="p-1.5 rounded border border-niyam-border hover:bg-niyam-surface-alt text-left text-[11px] font-medium text-niyam-text"
              >
                Senior Authority
              </button>
            </div>
          </div>

          <div className="mt-4 p-2.5 rounded bg-amber-50 border border-amber-200 text-[11px] text-amber-900 flex items-start gap-1.5">
            <KeyRound className="w-3.5 h-3.5 shrink-0 mt-0.5 text-amber-700" />
            <span>
              All demonstration accounts use password: <code className="font-mono bg-amber-100 px-1 rounded">ChangeMeDev123!</code>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
