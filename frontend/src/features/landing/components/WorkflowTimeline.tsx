import React from 'react';
import {
  FileText,
  GitMerge,
  Search,
  Building2,
  FileCheck2,
  Award,
  Info,
} from 'lucide-react';

export const WorkflowTimeline: React.FC = () => {
  const steps = [
    {
      num: '01',
      title: 'Application Submission',
      role: 'Educational Institution',
      desc: 'Institutions draft requirements, upload mandatory statutory documents, and submit under their verified institutional account.',
      icon: FileText,
      tag: 'Initial Stage',
    },
    {
      num: '02',
      title: 'Configured Workflow Routing',
      role: 'System Engine',
      desc: 'The application is pinned to the active route version. Stage sequence, working-day SLA clock, and assigned regional office are locked.',
      icon: GitMerge,
      tag: 'Version Pinned',
    },
    {
      num: '03',
      title: 'Document Scrutiny & Review',
      role: 'Scrutiny Officer',
      desc: 'Authorized scrutinizer verifies document checklists. Any deficiencies can be formally returned with mandatory written justification.',
      icon: Search,
      tag: 'Deficiency Tracking',
    },
    {
      num: '04',
      title: 'EVC Visit & Reporting',
      role: 'Visiting Committee & Regional Officer',
      desc: 'Where required by route policy, expert committee members are assigned to conduct physical/virtual inspection and upload verified reports.',
      icon: Building2,
      tag: 'Where Applicable',
    },
    {
      num: '05',
      title: 'Undertakings & Document Compliance',
      role: 'Institution & Regional Directorate',
      desc: 'Institutions upload compliance evidence for time-bound conditions. Dual-control verification is required before obligations can be marked fulfilled.',
      icon: FileCheck2,
      tag: 'Dual-Control Signoff',
    },
    {
      num: '06',
      title: 'Authorized Statutory Decision',
      role: 'Statutory Council & Senior Authority',
      desc: 'Designated human authorities render the formal approval decision. The transition and justification are sealed into the cryptographic SHA-256 audit ledger.',
      icon: Award,
      tag: 'Human Decision',
    },
  ];

  return (
    <section className="py-24 bg-white" id="workflow">
      <div className="liquid-container">
        {/* Section Header */}
        <div className="max-w-3xl mx-auto text-center mb-16">
          <span className="text-xs font-bold text-niyam-primary uppercase tracking-widest bg-niyam-primary-tint px-3 py-1 rounded-full">
            Lifecycle Architecture
          </span>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-niyam-text tracking-tight mt-4">
            From Submission to Accountable Review
          </h2>
          <p className="mt-4 text-base sm:text-lg text-niyam-text-muted leading-relaxed">
            Every step is attributed, time-bounded, and recorded. Below is an illustrative standard route demonstrating how approvals navigate through structured human governance.
          </p>
        </div>

        {/* Timeline Layout */}
        <div className="max-w-4xl mx-auto relative">
          {/* Vertical Connecting Line (Hidden on very small screens, visible on sm+) */}
          <div className="hidden sm:block absolute left-8 top-12 bottom-12 w-0.5 bg-gradient-to-b from-niyam-primary via-niyam-focus to-niyam-border" />

          <div className="space-y-8">
            {steps.map((step) => {
              const Icon = step.icon;
              return (
                <div
                  key={step.num}
                  className="relative flex flex-col sm:flex-row items-start gap-6 p-6 rounded-2xl bg-niyam-bg/50 border border-niyam-border/80 hover:bg-white hover:border-niyam-primary/40 hover:shadow-md transition-all duration-200 group"
                >
                  {/* Step Number / Icon Bubble */}
                  <div className="w-16 h-16 rounded-2xl bg-white border border-niyam-border shadow-xs flex items-center justify-center shrink-0 text-niyam-primary group-hover:bg-niyam-primary group-hover:text-white transition-colors z-10">
                    <Icon className="w-7 h-7" />
                  </div>

                  {/* Step Details */}
                  <div className="flex-1">
                    <div className="flex flex-wrap items-center justify-between gap-2 mb-1.5">
                      <div className="flex items-center gap-2.5">
                        <span className="text-xs font-black text-niyam-primary tracking-wider font-mono">
                          STEP {step.num}
                        </span>
                        <h3 className="text-lg font-bold text-niyam-text group-hover:text-niyam-primary transition-colors">
                          {step.title}
                        </h3>
                      </div>
                      <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-white border border-niyam-border text-niyam-text-muted">
                        {step.tag}
                      </span>
                    </div>

                    <div className="text-xs font-semibold text-niyam-primary/90 mb-2">
                      Actor: {step.role}
                    </div>

                    <p className="text-sm text-niyam-text-muted leading-relaxed">
                      {step.desc}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Disclaimer Box */}
          <div className="mt-12 p-4 rounded-xl bg-niyam-surface-alt/70 border border-niyam-border flex items-start gap-3">
            <Info className="w-5 h-5 text-niyam-text-muted shrink-0 mt-0.5" />
            <p className="text-xs text-niyam-text-muted leading-relaxed">
              <strong className="font-semibold text-niyam-text">Note on Route Flexibility:</strong> Workflow routes and stages in NiyamSetu are fully configurable in the administrative database. Specific programmes or institutions may follow different stage paths, alternate committee reviews, or customized timelines as determined by applicable AICTE regulations.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
};
