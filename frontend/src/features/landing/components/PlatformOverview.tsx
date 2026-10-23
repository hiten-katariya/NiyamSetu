import React from 'react';
import {
  FileText,
  Calendar,
  Users,
  CheckSquare,
  FileCheck,
  BarChart3,
  ArrowRight,
  ShieldAlert,
} from 'lucide-react';

export const PlatformOverview: React.FC = () => {
  const lifecycleNodes = [
    {
      title: 'Applications',
      role: 'Institutions',
      desc: 'Creation, routing & stage progression',
      icon: FileText,
      color: 'bg-blue-50 text-niyam-primary border-blue-200',
    },
    {
      title: 'Deadlines',
      role: 'System Engine',
      desc: 'Working-day SLAs & automated escalations',
      icon: Calendar,
      color: 'bg-teal-50 text-teal-700 border-teal-200',
    },
    {
      title: 'EVC Visits',
      role: 'Committees & RO',
      desc: 'Inspections, reports & recommendations',
      icon: Users,
      color: 'bg-purple-50 text-purple-700 border-purple-200',
    },
    {
      title: 'Undertakings',
      role: 'Institutions & Officers',
      desc: 'Compliance conditions & evidence signoff',
      icon: CheckSquare,
      color: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    },
    {
      title: 'Documents',
      role: 'Registry',
      desc: 'Validity tracking & versioned renewals',
      icon: FileCheck,
      color: 'bg-sky-50 text-sky-700 border-sky-200',
    },
    {
      title: 'Analytics',
      role: 'Bureau & Apex',
      desc: 'Pendency monitoring & audit exports',
      icon: BarChart3,
      color: 'bg-indigo-50 text-indigo-700 border-indigo-200',
    },
  ];

  return (
    <section className="py-24 bg-white" id="overview">
      <div className="liquid-container">
        {/* Section Header */}
        <div className="max-w-3xl mx-auto text-center mb-16">
          <span className="text-xs font-bold text-niyam-primary uppercase tracking-widest bg-niyam-primary-tint px-3 py-1 rounded-full">
            Platform Overview
          </span>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-niyam-text tracking-tight mt-4">
            One Connected View of the Approval Lifecycle
          </h2>
          <p className="mt-4 text-base sm:text-lg text-niyam-text-muted leading-relaxed">
            AICTE processes require coordination across institutions, scrutiny officers, inspection
            committees, and administrative directorates. NiyamSetu replaces fragmented spreadsheets
            and disparate emails with a single synchronized system of record.
          </p>
        </div>

        {/* Central Interconnected Diagram */}
        <div className="relative rounded-3xl bg-gradient-to-br from-niyam-bg to-white p-6 sm:p-10 border border-niyam-border shadow-lg">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {lifecycleNodes.map((node) => {
              const Icon = node.icon;
              return (
                <div
                  key={node.title}
                  className="relative p-6 rounded-2xl bg-white border border-niyam-border/80 shadow-xs hover:shadow-md transition-all duration-200 group hover:-translate-y-1"
                >
                  <div className="flex items-center justify-between mb-4">
                    <div
                      className={`w-12 h-12 rounded-xl flex items-center justify-center border ${node.color} transition-transform group-hover:scale-105`}
                    >
                      <Icon className="w-6 h-6" />
                    </div>
                    <span className="text-[11px] font-bold text-niyam-text-muted uppercase tracking-wider bg-niyam-surface-alt px-2.5 py-1 rounded-md">
                      {node.role}
                    </span>
                  </div>

                  <h3 className="text-lg font-bold text-niyam-text group-hover:text-niyam-primary transition-colors">
                    {node.title}
                  </h3>
                  <p className="text-xs text-niyam-text-muted mt-1.5 leading-relaxed">
                    {node.desc}
                  </p>

                  <div className="mt-4 pt-3 border-t border-niyam-border/50 flex items-center justify-between text-xs text-niyam-primary font-semibold">
                    <span>Integrated Engine</span>
                    <ArrowRight className="w-3.5 h-3.5 transition-transform group-hover:translate-x-1" />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Core Principle Callout */}
          <div className="mt-8 p-4 rounded-xl bg-amber-50/80 border border-amber-200/80 flex items-start sm:items-center gap-3">
            <ShieldAlert className="w-5 h-5 text-amber-700 shrink-0 mt-0.5 sm:mt-0" />
            <p className="text-xs text-amber-900 leading-relaxed font-medium">
              <strong className="font-bold">Human Governance Principle:</strong> NiyamSetu automates workflow movement, timeline tracking, and reminder dispatches. Statutory scrutiny, institutional inspections, and formal approval decisions are strictly reserved for designated human authorities.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
};
