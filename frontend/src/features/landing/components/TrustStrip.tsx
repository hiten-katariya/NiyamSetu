import React from 'react';
import { GitBranch, Shield, ClipboardCheck, History, CheckCircle2 } from 'lucide-react';

export const TrustStrip: React.FC = () => {
  const pillars = [
    {
      icon: GitBranch,
      stat: '6 Modules',
      statLabel: 'Full Lifecycle Coverage',
      title: 'Structured Workflow',
      desc: 'Transparent stage-by-stage application progression with version pinning.',
      badge: 'Version Controlled',
      badgeColor: 'bg-blue-50 text-blue-700',
    },
    {
      icon: Shield,
      stat: '7 Scoped Roles',
      statLabel: 'Multi-Tenant Isolation',
      title: 'Server Authorization',
      desc: 'Strict server-side isolation between institutions, regions, and committees.',
      badge: 'Zero Frontend Trust',
      badgeColor: 'bg-indigo-50 text-indigo-700',
    },
    {
      icon: ClipboardCheck,
      stat: '24/7 SLAs',
      statLabel: 'Working-Day Clock',
      title: 'Active Compliance',
      desc: 'Time-bound undertakings, visit inspections, and document renewal engines.',
      badge: 'Auto Alerts',
      badgeColor: 'bg-teal-50 text-teal-700',
    },
    {
      icon: History,
      stat: '100% SHA-256',
      statLabel: 'Cryptographic Ledger',
      title: 'Tamper-Evident Trail',
      desc: 'Immutable hash chain linking state transitions with real-time audit verification.',
      badge: 'Zero Mutations',
      badgeColor: 'bg-emerald-50 text-emerald-700',
    },
  ];

  return (
    <section className="py-12 bg-white border-b border-niyam-border/80">
      <div className="liquid-container !py-0">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {pillars.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div
                key={idx}
                className="group p-5 rounded-2xl bg-gradient-to-b from-white to-niyam-bg/40 border border-niyam-border/70 transition-all hover:bg-white hover:shadow-md hover:border-niyam-primary/40 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-10 h-10 rounded-xl bg-niyam-primary-tint flex items-center justify-center text-niyam-primary transition-transform group-hover:scale-110">
                      <Icon className="w-5 h-5" />
                    </div>
                    <span className={`text-[10px] font-extrabold px-2 py-0.5 rounded-full ${item.badgeColor}`}>
                      {item.badge}
                    </span>
                  </div>

                  <div className="mb-2">
                    <span className="text-xl font-black text-niyam-text tracking-tight block">
                      {item.stat}
                    </span>
                    <span className="text-[11px] font-semibold text-niyam-primary tracking-wide uppercase">
                      {item.statLabel}
                    </span>
                  </div>

                  <h3 className="text-sm font-bold text-niyam-text mt-3">{item.title}</h3>
                  <p className="text-xs text-niyam-text-muted mt-1 leading-relaxed">
                    {item.desc}
                  </p>
                </div>

                <div className="mt-4 pt-3 border-t border-niyam-border/40 flex items-center gap-1 text-[11px] font-bold text-niyam-primary group-hover:underline">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Enforced in Production</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
