import React from 'react';
import { ShieldCheck, Activity, Lock, CheckCircle2, Cpu } from 'lucide-react';

export const IntegrityTicker: React.FC = () => {
  const tickerItems = [
    {
      icon: ShieldCheck,
      text: 'Ledger Audit Chain: 100% Cryptographic Verification Active',
      tag: 'SHA-256',
      tagColor: 'bg-emerald-100 text-emerald-800',
    },
    {
      icon: Activity,
      text: 'Working-Day SLAs: 0 Critical Breaches across all Jurisdictions',
      tag: 'On Track',
      tagColor: 'bg-sky-100 text-sky-800',
    },
    {
      icon: Lock,
      text: 'Tenant Scoping: Multi-Tenant Data Isolation Enforced',
      tag: 'RBAC Strict',
      tagColor: 'bg-indigo-100 text-indigo-800',
    },
    {
      icon: Cpu,
      text: 'AICTE Statutory Decisions: Human Decision-Maker Prerogative Preserved',
      tag: 'Statutory Rule',
      tagColor: 'bg-amber-100 text-amber-800',
    },
    {
      icon: CheckCircle2,
      text: 'EVC Inspections: Dual-Signoff & Geo-Verification Protocol Active',
      tag: 'Verified',
      tagColor: 'bg-emerald-100 text-emerald-800',
    },
  ];

  return (
    <div className="bg-white border-y border-niyam-border/70 py-2.5 overflow-hidden">
      <div className="liquid-container !py-0 flex items-center justify-between gap-4">
        <div className="flex items-center gap-2 shrink-0">
          <span className="flex h-2 w-2 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
          </span>
          <span className="text-[11px] font-black uppercase tracking-wider text-niyam-primary">
            Live System Integrity Pulse
          </span>
        </div>

        {/* Streaming Items */}
        <div className="flex items-center gap-6 overflow-x-auto no-scrollbar py-0.5 text-xs text-niyam-text">
          {tickerItems.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div key={idx} className="flex items-center gap-2 shrink-0 bg-slate-50 px-3 py-1 rounded-full border border-slate-200/80">
                <Icon className="w-3.5 h-3.5 text-niyam-primary shrink-0" />
                <span className="font-medium text-slate-700">{item.text}</span>
                <span className={`text-[10px] font-bold px-1.5 py-0.2 rounded ${item.tagColor}`}>
                  {item.tag}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
