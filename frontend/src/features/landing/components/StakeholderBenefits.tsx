import React from 'react';
import { Building2, UserCheck, CalendarDays, Award, Check } from 'lucide-react';

export const StakeholderBenefits: React.FC = () => {
  const stakeholders = [
    {
      icon: Building2,
      role: 'Educational Institutions',
      tagline: 'Predictable Timelines & Clear Requirements',
      benefits: [
        'Real-time status tracking across every stage of the approval lifecycle.',
        'Immediate notification of deficiencies with clear, official written justification.',
        'Proactive expiry warnings for land leases, building safety, and society registrations.',
        'Direct evidence upload for conditional undertakings with verified timestamps.',
      ],
      color: 'bg-blue-50 text-niyam-primary border-blue-200',
    },
    {
      icon: UserCheck,
      role: 'Reviewing & Scrutiny Officers',
      tagline: 'Objective Checklists & Reduced Pendency',
      benefits: [
        'Organized jurisdictional queue with business-day countdown timers.',
        'Formal deficiency return mechanisms preventing arbitrary rejections.',
        'Automatic regional holiday and weekend exclusion in SLA calculations.',
        'Traceable stage advance controls backed by cryptographic audit entries.',
      ],
      color: 'bg-teal-50 text-teal-700 border-teal-200',
    },
    {
      icon: CalendarDays,
      role: 'Expert Committee Members',
      tagline: 'Focused On-Site Audits & Secure Reporting',
      benefits: [
        'Strict conflict-of-interest scoping preventing improper institutional assignment.',
        'Mobile-accessible digital inspection kits and infrastructure criteria checklists.',
        'Confidential report drafting and submission directly into the regional repository.',
        'Elimination of physical report transit delays and lost paper dossiers.',
      ],
      color: 'bg-purple-50 text-purple-700 border-purple-200',
    },
    {
      icon: Award,
      role: 'Senior Authorities & Bureau',
      tagline: 'Holistic Oversight & Strategic Assurance',
      benefits: [
        'Pan-regional pendency monitoring and comparative workload analytics.',
        'Sanitized CSV and tabular export capabilities for executive council review.',
        'Cryptographic audit integrity verification guaranteeing zero database tampering.',
        'Preserved statutory authority: systems support, while human councils decide.',
      ],
      color: 'bg-indigo-50 text-indigo-700 border-indigo-200',
    },
  ];

  return (
    <section className="py-24 bg-niyam-bg border-t border-niyam-border/70" id="stakeholders">
      <div className="liquid-container">
        {/* Section Header */}
        <div className="max-w-3xl mx-auto text-center mb-16">
          <span className="text-xs font-bold text-niyam-primary uppercase tracking-widest bg-niyam-primary-tint px-3 py-1 rounded-full">
            Stakeholder Alignment
          </span>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-niyam-text tracking-tight mt-4">
            Clarity for Every Stakeholder
          </h2>
          <p className="mt-4 text-base sm:text-lg text-niyam-text-muted leading-relaxed">
            By establishing defined roles and shared timelines, NiyamSetu transforms complex statutory processes into an orderly, collaborative experience for institutions and regulatory officials alike.
          </p>
        </div>

        {/* Stakeholder Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-5xl mx-auto">
          {stakeholders.map((item) => {
            const Icon = item.icon;
            return (
              <div
                key={item.role}
                className="p-8 rounded-3xl bg-white border border-niyam-border shadow-xs hover:shadow-md transition-all duration-200 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center gap-3.5 mb-4">
                    <div className={`w-12 h-12 rounded-2xl flex items-center justify-center border ${item.color}`}>
                      <Icon className="w-6 h-6" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-niyam-text">{item.role}</h3>
                      <p className="text-xs font-semibold text-niyam-text-muted">{item.tagline}</p>
                    </div>
                  </div>

                  <ul className="mt-6 space-y-3.5">
                    {item.benefits.map((benefit, bIdx) => (
                      <li key={bIdx} className="flex items-start gap-2.5 text-xs sm:text-sm text-niyam-text leading-relaxed">
                        <div className="w-4 h-4 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0 mt-0.5">
                          <Check className="w-3 h-3 stroke-[3]" />
                        </div>
                        <span>{benefit}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
