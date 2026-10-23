import React from 'react';
import { GitBranch, Shield, ClipboardCheck, History } from 'lucide-react';

export const TrustStrip: React.FC = () => {
  const pillars = [
    {
      icon: GitBranch,
      title: 'Structured Workflow Management',
      desc: 'Transparent, stage-by-stage application progression with version pinning.',
    },
    {
      icon: Shield,
      title: 'Role-Based Access Control',
      desc: 'Strict server-side isolation between institutions, regions, and committees.',
    },
    {
      icon: ClipboardCheck,
      title: 'Active Compliance Tracking',
      desc: 'Time-bound undertakings, visit inspections, and document validity monitoring.',
    },
    {
      icon: History,
      title: 'Traceable Cryptographic History',
      desc: 'SHA-256 hash-chained immutable audit log with real-time tamper alarms.',
    },
  ];

  return (
    <section className="py-10 bg-white border-b border-niyam-border/80">
      <div className="liquid-container !py-0">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {pillars.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div
                key={idx}
                className="flex items-start gap-3.5 p-4 rounded-xl bg-niyam-bg/60 border border-niyam-border/60 transition-all hover:bg-white hover:shadow-xs hover:border-niyam-border"
              >
                <div className="w-10 h-10 rounded-lg bg-niyam-primary-tint flex items-center justify-center shrink-0">
                  <Icon className="w-5 h-5 text-niyam-primary" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-niyam-text">{item.title}</h3>
                  <p className="text-xs text-niyam-text-muted mt-1 leading-relaxed">
                    {item.desc}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
