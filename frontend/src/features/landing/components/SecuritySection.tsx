import React from 'react';
import {
  ShieldCheck,
  Lock,
  UserCheck,
  KeyRound,
  FileSpreadsheet,
  Cpu,
  CheckCircle2,
} from 'lucide-react';

export const SecuritySection: React.FC = () => {
  const securityFeatures = [
    {
      icon: UserCheck,
      title: '7 Scoped User Roles',
      desc: 'Institution users, scrutiny officers, regional officers, committee members, bureau officers, senior authorities, and administrators operate within strictly separated permission boundaries.',
    },
    {
      icon: Lock,
      title: 'Multi-Tenant Data Isolation',
      desc: 'Institutions can access only their own applications and compliance filings. Regional officers are scoped strictly to registered institutions in their jurisdiction.',
    },
    {
      icon: KeyRound,
      title: 'Authenticated Document Vault',
      desc: 'Document downloads require active session credentials and verify authorization. File uploads enforce magic-byte MIME signature verification and path traversal sanitization.',
    },
    {
      icon: ShieldCheck,
      title: 'SHA-256 Chained Audit Ledger',
      desc: 'All state transitions, stage returns, regulatory holds, EVC recommendations, and configuration updates are chained using cryptographic hashes for tamper detection.',
    },
    {
      icon: FileSpreadsheet,
      title: 'Spreadsheet Formula Sanitization',
      desc: 'All tabular exports to CSV prepended with escape characters to neutralize formula injection (CSV injection) vulnerabilities in Microsoft Excel and spreadsheet tools.',
    },
    {
      icon: Cpu,
      title: 'Preserved Human Prerogative',
      desc: 'The platform provides workflow management, pendency monitoring, and document verification. Statutory AICTE approvals are strictly rendered by authorized human decision-makers.',
    },
  ];

  return (
    <section className="py-24 bg-gradient-to-b from-niyam-bg to-white border-t border-niyam-border/70" id="security">
      <div className="liquid-container">
        {/* Section Header */}
        <div className="max-w-3xl mx-auto text-center mb-16">
          <span className="text-xs font-bold text-niyam-primary uppercase tracking-widest bg-niyam-primary-tint px-3 py-1 rounded-full">
            Security &amp; Governance
          </span>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-niyam-text tracking-tight mt-4">
            Designed for Accountability and Controlled Access
          </h2>
          <p className="mt-4 text-base sm:text-lg text-niyam-text-muted leading-relaxed">
            Institutional compliance demands trustworthy data stewardship. NiyamSetu implements defense-in-depth across authentication, data scoping, file validation, and immutable auditing.
          </p>
        </div>

        {/* Security Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {securityFeatures.map((feat) => {
            const Icon = feat.icon;
            return (
              <div
                key={feat.title}
                className="p-7 rounded-2xl bg-white border border-niyam-border shadow-xs hover:shadow-md transition-all duration-200 flex flex-col justify-between"
              >
                <div>
                  <div className="w-11 h-11 rounded-xl bg-niyam-primary-tint flex items-center justify-center text-niyam-primary mb-4">
                    <Icon className="w-6 h-6" />
                  </div>
                  <h3 className="text-lg font-bold text-niyam-text mb-2">
                    {feat.title}
                  </h3>
                  <p className="text-xs sm:text-sm text-niyam-text-muted leading-relaxed">
                    {feat.desc}
                  </p>
                </div>
                <div className="mt-5 pt-3 border-t border-niyam-border/50 flex items-center gap-1.5 text-xs text-niyam-status-success font-semibold">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Enforced in Architecture</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
