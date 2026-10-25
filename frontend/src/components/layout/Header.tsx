import React, { useEffect, useState } from 'react';
import { api } from '../../lib/apiClient';
import { ReadinessCheckData } from '../../types';
import { useAuth } from '../../app/AuthContext';
import { Shield, LogOut, Bell } from 'lucide-react';
import { Link } from 'react-router-dom';

export const Header: React.FC<{ onMenuToggle: () => void }> = ({ onMenuToggle }) => {
  const [readiness, setReadiness] = useState<ReadinessCheckData | null>(null);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const { user, logout } = useAuth();

  useEffect(() => {
    api.get<ReadinessCheckData>('/health/ready')
      .then(setReadiness)
      .catch(() => setReadiness(null));

    if (user) {
      api.get<{ unread_count: number }>('/notifications/unread-count')
        .then((res) => setUnreadCount(res.unread_count))
        .catch(() => setUnreadCount(0));
    }
  }, [user]);

  const getInitials = (name?: string) => {
    if (!name) return 'NS';
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const formatRole = (role?: string) => {
    if (!role) return 'Authorized User';
    return role
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (c) => c.toUpperCase());
  };

  return (
    <header className="h-16 bg-niyam-surface border-b border-niyam-border sticky top-0 z-30 flex items-center justify-between px-4 sm:px-6">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuToggle}
          className="p-2 -ml-2 rounded-md text-niyam-text-muted hover:text-niyam-text hover:bg-niyam-surface-alt lg:hidden"
          aria-label="Toggle navigation menu"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-white border border-niyam-border flex items-center justify-center shadow-xs overflow-hidden p-0.5">
            <img
              src="/small-logo.png"
              alt="NiyamSetu Logo"
              className="w-full h-full object-contain"
              onError={(e) => {
                e.currentTarget.style.display = 'none';
                if (e.currentTarget.parentElement) e.currentTarget.parentElement.innerText = 'NS';
              }}
            />
          </div>
          <div>
            <h1 className="text-base font-bold text-niyam-primary tracking-tight leading-none">
              NiyamSetu
            </h1>
            <span className="text-[10px] text-niyam-text-muted uppercase tracking-wider font-semibold">
              AICTE Compliance & Workflow Portal
            </span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Readiness indicator */}
        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded bg-niyam-surface-alt border border-niyam-border text-xs">
          <span
            className={`w-2 h-2 rounded-full ${
              readiness?.status === 'ready' ? 'bg-niyam-status-success' : 'bg-niyam-status-warning animate-pulse'
            }`}
          />
          <span className="text-niyam-text-muted font-medium">
            DB: {readiness?.database.status === 'connected' ? 'Connected' : 'Connecting'}
          </span>
        </div>

        <span className="hidden md:inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-amber-100 text-amber-800 border border-amber-200">
          <Shield className="w-3 h-3 text-amber-700" />
          <span>Demo Environment</span>
        </span>

        {/* Notifications Bell */}
        {user && (
          <Link
            to="/notifications"
            className="relative p-2 rounded text-niyam-text-muted hover:text-niyam-primary hover:bg-niyam-surface-alt transition-colors"
            title="Notifications & Alerts"
            aria-label="Notifications"
          >
            <Bell className="w-4 h-4" />
            {unreadCount > 0 && (
              <span className="absolute top-1 right-1 flex items-center justify-center min-w-[16px] h-4 px-1 rounded-full bg-niyam-status-danger text-white text-[10px] font-bold leading-none">
                {unreadCount > 99 ? '99+' : unreadCount}
              </span>
            )}
          </Link>
        )}

        {/* User profile avatar & details */}
        {user && (
          <div className="flex items-center gap-3 pl-2 border-l border-niyam-border">
            <div className="w-8 h-8 rounded-full bg-niyam-primary-tint text-niyam-primary font-bold text-xs flex items-center justify-center border border-niyam-border">
              {getInitials(user.full_name)}
            </div>
            <div className="hidden md:block text-left text-xs">
              <p className="font-semibold text-niyam-text leading-tight">{user.full_name}</p>
              <p className="text-niyam-text-muted text-[11px] font-medium">
                {formatRole(user.role)}
              </p>
            </div>
            <button
              onClick={() => logout()}
              title="Sign Out"
              className="p-1.5 rounded text-niyam-text-muted hover:text-niyam-status-danger hover:bg-niyam-surface-alt transition-colors"
              aria-label="Sign Out"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
