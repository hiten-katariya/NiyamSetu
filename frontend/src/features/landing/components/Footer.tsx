import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../../../lib/apiClient';
import { ReadinessCheckData } from '../../../types';

export const Footer: React.FC = () => {
  const [readiness, setReadiness] = useState<ReadinessCheckData | null>(null);

  useEffect(() => {
    api
      .get<ReadinessCheckData>('/health/ready')
      .then(setReadiness)
      .catch(() => setReadiness(null));
  }, []);

  return (
    <footer className="bg-white border-t border-niyam-border py-16" role="contentinfo">
      <div className="liquid-container">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10 pb-12 border-b border-niyam-border/80">
          {/* Brand Col */}
          <div className="md:col-span-2 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-white border border-niyam-border flex items-center justify-center shadow-xs overflow-hidden p-0.5">
                <img
                  src="/small-logo.png"
                  alt="NiyamSetu Logo"
                  className="w-full h-full object-contain"
                  onError={(e) => {
                    (e.currentTarget as HTMLElement).style.display = 'none';
                    e.currentTarget.parentElement!.innerText = 'NS';
                  }}
                />
              </div>
              <span className="text-xl font-extrabold text-niyam-primary tracking-tight">
                NiyamSetu
              </span>
            </div>
            <p className="text-xs sm:text-sm text-niyam-text-muted max-w-md leading-relaxed">
              Configurable digital process management platform supporting AICTE institutional approval
              workflows, document compliance, Expert Visit Committee scheduling, and cryptographic auditability.
            </p>
            <div className="flex items-center gap-2 pt-1">
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold">
                <span className="w-2 h-2 rounded-full bg-emerald-600 animate-pulse" />
                <span>
                  System Engine:{' '}
                  {readiness?.status === 'ready' ? 'Operational & Ready' : 'Operational'}
                </span>
              </div>
            </div>
          </div>

          {/* Navigation Links */}
          <div>
            <h4 className="text-xs font-bold text-niyam-text uppercase tracking-wider mb-4">
              Platform Sections
            </h4>
            <ul className="space-y-2.5 text-xs sm:text-sm">
              <li>
                <a href="#overview" className="text-niyam-text-muted hover:text-niyam-primary transition-colors">
                  Platform Overview
                </a>
              </li>
              <li>
                <a href="#architecture" className="text-niyam-text-muted hover:text-niyam-primary transition-colors">
                  Interactive 3D Modules
                </a>
              </li>
              <li>
                <a href="#capabilities" className="text-niyam-text-muted hover:text-niyam-primary transition-colors">
                  Capabilities Bento
                </a>
              </li>
              <li>
                <a href="#workflow" className="text-niyam-text-muted hover:text-niyam-primary transition-colors">
                  Approval Lifecycle
                </a>
              </li>
              <li>
                <a href="#security" className="text-niyam-text-muted hover:text-niyam-primary transition-colors">
                  Security Architecture
                </a>
              </li>
              <li>
                <a href="#preview" className="text-niyam-text-muted hover:text-niyam-primary transition-colors">
                  Interactive Preview
                </a>
              </li>
            </ul>
          </div>

          {/* Portal Access */}
          <div>
            <h4 className="text-xs font-bold text-niyam-text uppercase tracking-wider mb-4">
              Authorized Portal
            </h4>
            <ul className="space-y-2.5 text-xs sm:text-sm">
              <li>
                <Link to="/login" className="text-niyam-primary font-bold hover:underline">
                  Sign In to Workspace &rarr;
                </Link>
              </li>
              <li>
                <a href="#faq" className="text-niyam-text-muted hover:text-niyam-primary transition-colors">
                  Frequently Asked Questions
                </a>
              </li>
              <li>
                <span className="text-niyam-text-muted block text-xs">
                  Target Database: <span className="font-mono text-niyam-text">niyamsetu_dev</span>
                </span>
              </li>
              <li>
                <span className="text-niyam-text-muted block text-xs">
                  Ledger Algorithm: <span className="font-mono text-niyam-text">SHA-256</span>
                </span>
              </li>
            </ul>
          </div>
        </div>

        {/* Legal & Regulatory Disclaimer */}
        <div className="pt-8 flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-niyam-text-muted">
          <p className="text-center md:text-left max-w-2xl">
            <strong>Mandatory Governance Notice:</strong> NiyamSetu is a process orchestration and monitoring tool. The platform assists tracking, notification, and document management; it does not autonomously grant, deny, or replace statutory AICTE approvals, inspections, or regulatory decisions, which are strictly reserved for authorized human authorities.
          </p>
          <div className="text-center md:text-right shrink-0">
            <p>&copy; {new Date().getFullYear()} NiyamSetu. All rights reserved.</p>
          </div>
        </div>
      </div>
    </footer>
  );
};
