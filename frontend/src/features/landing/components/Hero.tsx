import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  Clock,
  Layers,
  Lock,
  ChevronRight,
} from 'lucide-react';
import { useAuth } from '../../../app/AuthContext';
import { InteractiveHeadline } from './InteractiveHeadline';
import { SwarmCursor } from '../../../components/SwarmCursor';
import { InstitutionalHeroBackground } from './InstitutionalHeroBackground';

export const Hero: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  return (
    <section className="relative pt-32 pb-20 lg:pt-40 lg:pb-28 overflow-hidden bg-gradient-to-b from-[#F8FAFC] via-[#F1F5F9] to-[#EEF2F7]">
      {/* Dynamic Animated Dual Background (AeroShards + Connected Institutional Network) */}
      <InstitutionalHeroBackground />

      <div className="liquid-container relative z-10">
        <SwarmCursor
          count={500}
          size={2.5}
          spread={80}
          swirl={0.65}
          speed={0.8}
          wander={0.4}
          clickEffect="burst"
          lightMode={true}
          accentColor="#0284c7"
          color="#94a3b8"
          className="!overflow-visible"
        >
          <div className="flex flex-col items-center text-center max-w-4xl mx-auto">
          {/* Top Pill / Platform Badge */}
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/80 border border-niyam-border/80 backdrop-blur-sm shadow-xs mb-8 transition-transform hover:scale-105">
            <span className="flex h-2 w-2 rounded-full bg-niyam-focus animate-pulse" />
            <span className="text-xs font-bold text-niyam-primary tracking-wide">
              Official Institutional Process Management
            </span>
            <span className="text-xs text-niyam-border font-medium">|</span>
            <span className="text-xs font-medium text-niyam-text-muted flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5 text-niyam-status-success" />
              Human Governance
            </span>
          </div>

          {/* Interactive Editorial Headline */}
          <div className="mb-6">
            <InteractiveHeadline
              text="A clearer, more connected approach to approval workflows and institutional compliance."
              highlightWords={['connected', 'workflows', 'compliance']}
            />
          </div>

          {/* Supporting Copy */}
          <p className="text-lg sm:text-xl text-niyam-text-muted max-w-2xl font-normal leading-relaxed mb-10">
            NiyamSetu organizes application routing, stage-wise pendency, committee visits,
            compliance undertakings, document validity, automated alerts, and tamper-evident audit
            trails in one unified institutional platform.
          </p>

          {/* Action CTAs */}
          <div className="flex flex-col sm:flex-row items-center gap-4 w-full sm:w-auto mb-14">
            <button
              onClick={() => navigate(isAuthenticated ? '/' : '/login')}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-7 py-3.5 rounded-xl bg-niyam-primary text-white text-base font-bold shadow-md hover:bg-niyam-primary-hover hover:shadow-lg transition-all focus-visible:ring-2 focus-visible:ring-niyam-focus"
            >
              <span>{isAuthenticated ? 'Enter Portal Dashboard' : 'Access Authorized Portal'}</span>
              <ArrowRight className="w-5 h-5" />
            </button>
            <a
              href="#workflow"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl bg-white/90 text-niyam-text border border-niyam-border font-bold text-base hover:bg-niyam-surface-alt hover:text-niyam-primary transition-all shadow-xs backdrop-blur-sm"
            >
              <span>Explore Lifecycle</span>
              <ChevronRight className="w-4 h-4 text-niyam-text-muted" />
            </a>
          </div>

          {/* Key Assurance Indicators */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 w-full max-w-3xl mb-16">
            <div className="flex items-center gap-2.5 px-4 py-2.5 rounded-xl bg-white/70 border border-niyam-border/70 backdrop-blur-xs shadow-xs text-left">
              <div className="w-7 h-7 rounded-lg bg-niyam-primary-tint flex items-center justify-center shrink-0">
                <Layers className="w-4 h-4 text-niyam-primary" />
              </div>
              <div className="flex flex-col">
                <span className="text-xs font-bold text-niyam-text">7 Scoped Roles</span>
                <span className="text-[10px] text-niyam-text-muted">Strict Tenant Isolation</span>
              </div>
            </div>

            <div className="flex items-center gap-2.5 px-4 py-2.5 rounded-xl bg-white/70 border border-niyam-border/70 backdrop-blur-xs shadow-xs text-left">
              <div className="w-7 h-7 rounded-lg bg-teal-50 flex items-center justify-center shrink-0">
                <Clock className="w-4 h-4 text-teal-700" />
              </div>
              <div className="flex flex-col">
                <span className="text-xs font-bold text-niyam-text">Working-Day SLAs</span>
                <span className="text-[10px] text-niyam-text-muted">Auto Reminders &amp; Alerts</span>
              </div>
            </div>

            <div className="col-span-2 sm:col-span-1 flex items-center gap-2.5 px-4 py-2.5 rounded-xl bg-white/70 border border-niyam-border/70 backdrop-blur-xs shadow-xs text-left">
              <div className="w-7 h-7 rounded-lg bg-purple-50 flex items-center justify-center shrink-0">
                <Lock className="w-4 h-4 text-purple-700" />
              </div>
              <div className="flex flex-col">
                <span className="text-xs font-bold text-niyam-text">SHA-256 Ledger</span>
                <span className="text-[10px] text-niyam-text-muted">Tamper-Evident History</span>
              </div>
            </div>
          </div>
        </div>
        </SwarmCursor>

        {/* Hero Interactive Interface Mockup / Preview Card */}
        <div className="max-w-5xl mx-auto rounded-2xl bg-white/95 border border-niyam-border shadow-2xl p-4 sm:p-7 backdrop-blur-xl relative transition-all duration-300 hover:shadow-niyam-primary/10">
          {/* Top Window Bar */}
          <div className="flex items-center justify-between border-b border-niyam-border/80 pb-4 mb-6">
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-red-400" />
              <span className="w-3 h-3 rounded-full bg-amber-400" />
              <span className="w-3 h-3 rounded-full bg-emerald-400" />
              <span className="ml-3 text-xs font-bold text-niyam-text-muted hidden sm:inline">
                NiyamSetu &bull; Live Institutional Workflow Workspace (Demo Preview)
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 text-[11px] font-bold">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse" />
                Live Engine Ready
              </span>
            </div>
          </div>

          {/* Workflow Stage Stepper Bar */}
          <div className="mb-8">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-niyam-primary tracking-wider uppercase">
                Active Application: AICTE-APP-2026-N092 (Engineering &amp; Technology Extension)
              </span>
              <span className="text-xs font-semibold text-niyam-text-muted">
                Route: Standard APH Route (Version 1)
              </span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 flex flex-col gap-1">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-bold text-emerald-800">1. Drafting</span>
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                </div>
                <span className="text-[10px] text-emerald-700">Completed 12 Oct 2026</span>
              </div>

              <div className="p-3 rounded-xl bg-blue-50 border border-niyam-focus flex flex-col gap-1 ring-1 ring-niyam-focus shadow-xs">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-bold text-niyam-primary">2. Scrutiny</span>
                  <span className="w-2 h-2 rounded-full bg-niyam-focus animate-ping" />
                </div>
                <span className="text-[10px] text-niyam-focus font-semibold">Active &bull; Due in 3 Days</span>
              </div>

              <div className="p-3 rounded-xl bg-niyam-surface-alt/70 border border-niyam-border flex flex-col gap-1">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-bold text-niyam-text-muted">3. EVC Inspection</span>
                  <Clock className="w-3.5 h-3.5 text-niyam-text-muted" />
                </div>
                <span className="text-[10px] text-niyam-text-muted">Assigned to North Committee</span>
              </div>

              <div className="p-3 rounded-xl bg-niyam-surface-alt/70 border border-niyam-border flex flex-col gap-1">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-bold text-niyam-text-muted">4. Statutory Approval</span>
                  <ShieldCheck className="w-3.5 h-3.5 text-niyam-text-muted" />
                </div>
                <span className="text-[10px] text-niyam-text-muted">Authorized Council Signoff</span>
              </div>
            </div>
          </div>

          {/* Sample Metrics Strip */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 border-t border-niyam-border/60">
            <div className="p-3.5 rounded-xl bg-niyam-bg/80 border border-niyam-border flex items-center justify-between">
              <div>
                <span className="text-xs text-niyam-text-muted font-medium">Regional Average SLA</span>
                <p className="text-xl font-black text-niyam-text mt-0.5">4.2 Working Days</p>
              </div>
              <div className="text-right">
                <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800">
                  -28% Pendency
                </span>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-niyam-bg/80 border border-niyam-border flex items-center justify-between">
              <div>
                <span className="text-xs text-niyam-text-muted font-medium">Compliance Undertakings</span>
                <p className="text-xl font-black text-niyam-text mt-0.5">94.8% Fulfilled</p>
              </div>
              <div className="text-right">
                <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-niyam-primary">
                  Dual Verified
                </span>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-niyam-bg/80 border border-niyam-border flex items-center justify-between">
              <div>
                <span className="text-xs text-niyam-text-muted font-medium">Audit Ledger Verification</span>
                <p className="text-xl font-black text-niyam-text mt-0.5">100% Intact</p>
              </div>
              <div className="text-right">
                <span className="inline-block px-2 py-0.5 rounded text-[10px] font-bold bg-purple-100 text-purple-800">
                  SHA-256 Valid
                </span>
              </div>
            </div>
          </div>

          <div className="mt-4 text-center">
            <span className="text-[11px] font-medium text-niyam-text-muted italic">
              * Demonstration visualization using synthetic institutional data. Statutory decisions are exercised by designated human authorities.
            </span>
          </div>
        </div>
      </div>
    </section>
  );
};
