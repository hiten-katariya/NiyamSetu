import React, { useEffect, useState } from 'react';
import { api } from '../../lib/apiClient';
import { ReadinessCheckData } from '../../types';

export const Header: React.FC<{ onMenuToggle: () => void }> = ({ onMenuToggle }) => {
  const [readiness, setReadiness] = useState<ReadinessCheckData | null>(null);

  useEffect(() => {
    api.get<ReadinessCheckData>('/health/ready')
      .then(setReadiness)
      .catch(() => setReadiness(null));
  }, []);

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
          <div className="w-8 h-8 rounded bg-niyam-primary text-white font-bold flex items-center justify-center text-sm shadow-sm">
            NS
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

        <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-amber-100 text-amber-800 border border-amber-200">
          Demo Environment
        </span>

        {/* User profile avatar / pill */}
        <div className="flex items-center gap-2 pl-2 border-l border-niyam-border">
          <div className="w-8 h-8 rounded-full bg-niyam-primary-tint text-niyam-primary font-semibold text-xs flex items-center justify-center">
            SO
          </div>
          <div className="hidden md:block text-left text-xs">
            <p className="font-semibold text-niyam-text leading-tight">Scrutiny Officer</p>
            <p className="text-niyam-text-muted text-[11px]">Regional Desk</p>
          </div>
        </div>
      </div>
    </header>
  );
};
