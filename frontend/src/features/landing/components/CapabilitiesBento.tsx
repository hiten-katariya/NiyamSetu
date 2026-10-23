import React from 'react';
import {
  GitPullRequest,
  Clock,
  CalendarDays,
  CheckCircle,
  FileCheck2,
  BarChart,
  ShieldCheck,
  Settings,
} from 'lucide-react';

export const CapabilitiesBento: React.FC = () => {
  return (
    <section className="py-24 bg-niyam-bg border-t border-niyam-border/70" id="capabilities">
      <div className="liquid-container">
        {/* Section Header */}
        <div className="max-w-3xl mx-auto text-center mb-16">
          <span className="text-xs font-bold text-niyam-primary uppercase tracking-widest bg-niyam-primary-tint px-3 py-1 rounded-full">
            Core Capabilities
          </span>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-niyam-text tracking-tight mt-4">
            Everything Connected. Every Stage Visible.
          </h2>
          <p className="mt-4 text-base sm:text-lg text-niyam-text-muted leading-relaxed">
            Engineered specifically to solve the operational bottlenecks of large-scale statutory approvals with configurable logic, transparent oversight, and tamper-resistant security.
          </p>
        </div>

        {/* Bento Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Card 1: Application Workflow (Spans 2 columns on lg) */}
          <div className="lg:col-span-2 p-8 rounded-3xl bg-white border border-niyam-border shadow-xs hover:shadow-md transition-all duration-300 relative overflow-hidden group">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 rounded-2xl bg-blue-50 border border-blue-200 flex items-center justify-center text-niyam-primary">
                <GitPullRequest className="w-6 h-6" />
              </div>
              <span className="text-xs font-bold text-niyam-primary bg-niyam-primary-tint px-3 py-1 rounded-full">
                Workflow Orchestration
              </span>
            </div>
            <h3 className="text-2xl font-bold text-niyam-text group-hover:text-niyam-primary transition-colors">
              Configurable Workflow Routing
            </h3>
            <p className="text-sm text-niyam-text-muted mt-2 max-w-xl leading-relaxed">
              Track applications through configured stages, assignments, returns, holds, and stage history. In-flight applications remain pinned to their initial route version even when administrators update rules.
            </p>

            {/* Illustrative Stage Progression Preview */}
            <div className="mt-6 p-4 rounded-2xl bg-niyam-bg/80 border border-niyam-border/70">
              <div className="grid grid-cols-3 gap-3">
                <div className="p-3 rounded-xl bg-white border border-emerald-200 text-center">
                  <span className="text-[11px] font-bold text-emerald-800">Drafting</span>
                  <div className="text-[10px] text-emerald-600 mt-0.5">Completed</div>
                </div>
                <div className="p-3 rounded-xl bg-blue-50 border border-niyam-focus text-center shadow-xs">
                  <span className="text-[11px] font-bold text-niyam-primary">Scrutiny</span>
                  <div className="text-[10px] text-niyam-focus font-semibold mt-0.5">Under Review</div>
                </div>
                <div className="p-3 rounded-xl bg-white border border-niyam-border text-center opacity-70">
                  <span className="text-[11px] font-bold text-niyam-text-muted">Approval</span>
                  <div className="text-[10px] text-niyam-text-muted mt-0.5">Final Signoff</div>
                </div>
              </div>
            </div>
          </div>

          {/* Card 2: Deadline Intelligence */}
          <div className="p-8 rounded-3xl bg-white border border-niyam-border shadow-xs hover:shadow-md transition-all duration-300 relative overflow-hidden group">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 rounded-2xl bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-700">
                <Clock className="w-6 h-6" />
              </div>
              <span className="text-xs font-bold text-teal-800 bg-teal-100 px-3 py-1 rounded-full">
                SLA Intelligence
              </span>
            </div>
            <h3 className="text-xl font-bold text-niyam-text group-hover:text-teal-700 transition-colors">
              Calendar-Aware Deadlines
            </h3>
            <p className="text-sm text-niyam-text-muted mt-2 leading-relaxed">
              Calculates business working days skipping weekends and gazetted regional holidays. Pauses SLA clocks on formal regulatory holds.
            </p>
            <div className="mt-6 p-4 rounded-2xl bg-teal-50/50 border border-teal-100 flex items-center justify-between">
              <div>
                <span className="text-xs font-semibold text-teal-900">Configured Reminders</span>
                <p className="text-sm font-bold text-teal-700">T-3, T-1, T-0 Days</p>
              </div>
              <span className="px-2.5 py-1 rounded bg-teal-200/60 text-teal-900 text-xs font-bold">
                Auto Escalation
              </span>
            </div>
          </div>

          {/* Card 3: EVC Management */}
          <div className="p-8 rounded-3xl bg-white border border-niyam-border shadow-xs hover:shadow-md transition-all duration-300 relative overflow-hidden group">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 rounded-2xl bg-purple-50 border border-purple-200 flex items-center justify-center text-purple-700">
                <CalendarDays className="w-6 h-6" />
              </div>
              <span className="text-xs font-bold text-purple-800 bg-purple-100 px-3 py-1 rounded-full">
                On-Site Visits
              </span>
            </div>
            <h3 className="text-xl font-bold text-niyam-text group-hover:text-purple-700 transition-colors">
              EVC Inspection Portal
            </h3>
            <p className="text-sm text-niyam-text-muted mt-2 leading-relaxed">
              Schedule visits, assign expert committee members with conflict-of-interest scoping, record on-site audit checklists, and upload verification reports.
            </p>
            <div className="mt-6 p-3 rounded-xl bg-purple-50/60 border border-purple-100 text-xs text-purple-900 font-medium">
              &bull; Dual-control regional officer review before report finalization
            </div>
          </div>

          {/* Card 4: Compliance Undertakings */}
          <div className="p-8 rounded-3xl bg-white border border-niyam-border shadow-xs hover:shadow-md transition-all duration-300 relative overflow-hidden group">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 rounded-2xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-700">
                <CheckCircle className="w-6 h-6" />
              </div>
              <span className="text-xs font-bold text-emerald-800 bg-emerald-100 px-3 py-1 rounded-full">
                Compliance
              </span>
            </div>
            <h3 className="text-xl font-bold text-niyam-text group-hover:text-emerald-700 transition-colors">
              Time-Bound Undertakings
            </h3>
            <p className="text-sm text-niyam-text-muted mt-2 leading-relaxed">
              Track conditional obligations, upload evidence documentation, enforce target dates, and require authorized human officer verification for formal closure.
            </p>
            <div className="mt-6 p-3 rounded-xl bg-emerald-50/60 border border-emerald-100 text-xs text-emerald-900 font-medium">
              &bull; Auto-detects overdue conditions and triggers administrative alerts
            </div>
          </div>

          {/* Card 5: Document Validity & Renewals */}
          <div className="p-8 rounded-3xl bg-white border border-niyam-border shadow-xs hover:shadow-md transition-all duration-300 relative overflow-hidden group">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 rounded-2xl bg-sky-50 border border-sky-200 flex items-center justify-center text-sky-700">
                <FileCheck2 className="w-6 h-6" />
              </div>
              <span className="text-xs font-bold text-sky-800 bg-sky-100 px-3 py-1 rounded-full">
                Document Vault
              </span>
            </div>
            <h3 className="text-xl font-bold text-niyam-text group-hover:text-sky-700 transition-colors">
              Document Governance
            </h3>
            <p className="text-sm text-niyam-text-muted mt-2 leading-relaxed">
              Maintains institutional document records, registers validity dates, alerts on approaching expirations, and links renewed versions to historical audit records.
            </p>
            <div className="mt-6 p-3 rounded-xl bg-sky-50/60 border border-sky-100 text-xs text-sky-900 font-medium">
              &bull; Magic-byte inspection &bull; SHA-256 integrity checksums
            </div>
          </div>

          {/* Card 6: Analytics & Reporting */}
          <div className="p-8 rounded-3xl bg-white border border-niyam-border shadow-xs hover:shadow-md transition-all duration-300 relative overflow-hidden group">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 rounded-2xl bg-indigo-50 border border-indigo-200 flex items-center justify-center text-indigo-700">
                <BarChart className="w-6 h-6" />
              </div>
              <span className="text-xs font-bold text-indigo-800 bg-indigo-100 px-3 py-1 rounded-full">
                Operational BI
              </span>
            </div>
            <h3 className="text-xl font-bold text-niyam-text group-hover:text-indigo-700 transition-colors">
              Analytics &amp; Scoped Reports
            </h3>
            <p className="text-sm text-niyam-text-muted mt-2 leading-relaxed">
              Role-scoped executive dashboards, pendency ageing analysis, regional comparisons, and sanitized CSV exports protected against spreadsheet formula injection.
            </p>
            <div className="mt-6 p-3 rounded-xl bg-indigo-50/60 border border-indigo-100 text-xs text-indigo-900 font-medium">
              &bull; UTF-8 BOM encoding &bull; Macro operator character escaping
            </div>
          </div>

          {/* Card 7: Audit Transparency */}
          <div className="p-8 rounded-3xl bg-white border border-niyam-border shadow-xs hover:shadow-md transition-all duration-300 relative overflow-hidden group">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 rounded-2xl bg-slate-100 border border-slate-300 flex items-center justify-center text-slate-800">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <span className="text-xs font-bold text-slate-800 bg-slate-200 px-3 py-1 rounded-full">
                Cryptographic
              </span>
            </div>
            <h3 className="text-xl font-bold text-niyam-text group-hover:text-niyam-primary transition-colors">
              SHA-256 Audit Chain
            </h3>
            <p className="text-sm text-niyam-text-muted mt-2 leading-relaxed">
              Every status advance, return, hold, EVC report, and configuration change is linked cryptographically in an append-only ledger with automated tamper detection.
            </p>
            <div className="mt-6 p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs text-slate-800 font-medium">
              &bull; Public audit verification API detects unauthorized row edits
            </div>
          </div>

          {/* Card 8: Configurable Administration (Spans 2 columns on lg) */}
          <div className="lg:col-span-2 p-8 rounded-3xl bg-white border border-niyam-border shadow-xs hover:shadow-md transition-all duration-300 relative overflow-hidden group">
            <div className="flex items-center justify-between mb-4">
              <div className="w-12 h-12 rounded-2xl bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-700">
                <Settings className="w-6 h-6" />
              </div>
              <span className="text-xs font-bold text-amber-800 bg-amber-100 px-3 py-1 rounded-full">
                Zero Code Deployments
              </span>
            </div>
            <h3 className="text-2xl font-bold text-niyam-text group-hover:text-amber-800 transition-colors">
              Rules in Data, Not Code
            </h3>
            <p className="text-sm text-niyam-text-muted mt-2 max-w-xl leading-relaxed">
              Stage timelines, reminder offsets, escalation tiers, message templates, and gazetted regional holidays are stored as database records. Modifying approval parameters requires mandatory justification and creates an immutable version snapshot.
            </p>
            <div className="mt-6 flex flex-wrap items-center gap-3">
              <span className="px-3 py-1.5 rounded-lg bg-niyam-bg border border-niyam-border text-xs font-semibold text-niyam-text">
                Mandatory Change Reasons
              </span>
              <span className="px-3 py-1.5 rounded-lg bg-niyam-bg border border-niyam-border text-xs font-semibold text-niyam-text">
                Historical Version Rollbacks
              </span>
              <span className="px-3 py-1.5 rounded-lg bg-niyam-bg border border-niyam-border text-xs font-semibold text-niyam-text">
                Isolated Regional Holidays
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
