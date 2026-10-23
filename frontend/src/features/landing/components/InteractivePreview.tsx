import React, { useState } from 'react';
import {
  Building2,
  UserCheck,
  Calendar,
  BarChart3,
  CheckCircle2,
  Clock,
  FileText,
  Shield,
} from 'lucide-react';

export const InteractivePreview: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'institution' | 'scrutiny' | 'committee' | 'bureau'>('institution');

  return (
    <section className="py-24 bg-white border-t border-niyam-border/70" id="preview">
      <div className="liquid-container">
        {/* Section Header */}
        <div className="max-w-3xl mx-auto text-center mb-12">
          <span className="text-xs font-bold text-niyam-primary uppercase tracking-widest bg-niyam-primary-tint px-3 py-1 rounded-full">
            Product Experience Preview
          </span>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-niyam-text tracking-tight mt-4">
            Experience the Role-Adapted Interface
          </h2>
          <p className="mt-4 text-base sm:text-lg text-niyam-text-muted leading-relaxed">
            NiyamSetu adapts its presentation to each user's statutory responsibilities. Switch tabs below to preview how different stakeholders interact with their dedicated dashboards.
          </p>
        </div>

        {/* Tab Buttons */}
        <div className="flex flex-wrap items-center justify-center gap-2 mb-8">
          <button
            onClick={() => setActiveTab('institution')}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold transition-all ${
              activeTab === 'institution'
                ? 'bg-niyam-primary text-white shadow-sm'
                : 'bg-niyam-bg text-niyam-text-muted hover:bg-niyam-surface-alt hover:text-niyam-text border border-niyam-border'
            }`}
          >
            <Building2 className="w-4 h-4" />
            <span>Institution Portal</span>
          </button>

          <button
            onClick={() => setActiveTab('scrutiny')}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold transition-all ${
              activeTab === 'scrutiny'
                ? 'bg-niyam-primary text-white shadow-sm'
                : 'bg-niyam-bg text-niyam-text-muted hover:bg-niyam-surface-alt hover:text-niyam-text border border-niyam-border'
            }`}
          >
            <UserCheck className="w-4 h-4" />
            <span>Scrutiny &amp; Regional Officer</span>
          </button>

          <button
            onClick={() => setActiveTab('committee')}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold transition-all ${
              activeTab === 'committee'
                ? 'bg-niyam-primary text-white shadow-sm'
                : 'bg-niyam-bg text-niyam-text-muted hover:bg-niyam-surface-alt hover:text-niyam-text border border-niyam-border'
            }`}
          >
            <Calendar className="w-4 h-4" />
            <span>Committee Member</span>
          </button>

          <button
            onClick={() => setActiveTab('bureau')}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-bold transition-all ${
              activeTab === 'bureau'
                ? 'bg-niyam-primary text-white shadow-sm'
                : 'bg-niyam-bg text-niyam-text-muted hover:bg-niyam-surface-alt hover:text-niyam-text border border-niyam-border'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            <span>Executive Bureau &amp; Apex</span>
          </button>
        </div>

        {/* Tab Content Display */}
        <div className="max-w-5xl mx-auto rounded-3xl bg-niyam-bg border border-niyam-border shadow-xl p-5 sm:p-8 transition-all">
          {activeTab === 'institution' && (
            <div className="space-y-6">
              <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-niyam-border">
                <div>
                  <span className="text-xs font-bold text-niyam-text-muted">INSTITUTION WORKSPACE</span>
                  <h3 className="text-xl font-bold text-niyam-text mt-0.5">Institute of Technology &amp; Science (North)</h3>
                </div>
                <div className="flex items-center gap-2">
                  <span className="px-3 py-1 rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold">
                    3 Active Applications
                  </span>
                </div>
              </div>

              {/* Application Row Card */}
              <div className="p-4 sm:p-5 rounded-2xl bg-white border border-niyam-border shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="flex items-start gap-3.5">
                  <div className="w-10 h-10 rounded-xl bg-blue-50 text-niyam-primary flex items-center justify-center shrink-0 mt-0.5">
                    <FileText className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-niyam-primary">APP-2026-N092</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800">
                        In Progress
                      </span>
                    </div>
                    <h4 className="text-base font-bold text-niyam-text mt-0.5">
                      Extension of Approval (EoA) 2026–27
                    </h4>
                    <p className="text-xs text-niyam-text-muted mt-1">
                      Current Stage: <strong>Document Scrutiny</strong> &bull; Assigned to Northern Regional Office
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-4 self-end md:self-center">
                  <div className="text-right">
                    <span className="text-[11px] text-niyam-text-muted block">Target SLA</span>
                    <span className="text-xs font-bold text-niyam-focus">Due in 3 working days</span>
                  </div>
                  <span className="px-3 py-1.5 rounded-lg bg-niyam-bg border border-niyam-border text-xs font-bold text-niyam-primary">
                    View Progress
                  </span>
                </div>
              </div>

              {/* Compliance & Document Alert */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-white border border-emerald-200 shadow-xs">
                  <div className="flex items-center gap-2 text-emerald-700 text-xs font-bold mb-1">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Compliance Undertakings (2/2 Fulfilled)</span>
                  </div>
                  <p className="text-xs text-niyam-text-muted">
                    Cadre rectification evidence verified by Regional Officer on 18 Oct 2026.
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-white border border-amber-200 shadow-xs">
                  <div className="flex items-center gap-2 text-amber-700 text-xs font-bold mb-1">
                    <Clock className="w-4 h-4" />
                    <span>Document Expiry Alert (1 Action Required)</span>
                  </div>
                  <p className="text-xs text-niyam-text-muted">
                    Building Safety Certificate expires in 28 days. Renewal submission active.
                  </p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'scrutiny' && (
            <div className="space-y-6">
              <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-niyam-border">
                <div>
                  <span className="text-xs font-bold text-niyam-text-muted">REGIONAL OFFICER QUEUE</span>
                  <h3 className="text-xl font-bold text-niyam-text mt-0.5">Northern Regional Jurisdiction (Kanpur)</h3>
                </div>
                <div className="flex items-center gap-2">
                  <span className="px-3 py-1 rounded-full bg-blue-100 text-niyam-primary text-xs font-bold">
                    12 Applications Pending Scrutiny
                  </span>
                </div>
              </div>

              {/* Scrutiny Queue Table */}
              <div className="rounded-xl bg-white border border-niyam-border overflow-hidden">
                <table className="w-full text-left text-xs">
                  <thead className="bg-niyam-surface-alt border-b border-niyam-border text-niyam-text-muted uppercase font-bold text-[10px]">
                    <tr>
                      <th className="p-3">Application Ref</th>
                      <th className="p-3">Institution</th>
                      <th className="p-3">Stage &amp; SLA</th>
                      <th className="p-3">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-niyam-border/60">
                    <tr>
                      <td className="p-3 font-mono font-bold text-niyam-primary">APP-2026-N092</td>
                      <td className="p-3 font-semibold text-niyam-text">Inst of Tech &amp; Science</td>
                      <td className="p-3 text-amber-700 font-semibold">Scrutiny (3 days left)</td>
                      <td className="p-3">
                        <span className="px-2 py-1 rounded bg-niyam-primary text-white font-bold text-[10px]">
                          Verify Checklist
                        </span>
                      </td>
                    </tr>
                    <tr>
                      <td className="p-3 font-mono font-bold text-niyam-primary">APP-2026-N104</td>
                      <td className="p-3 font-semibold text-niyam-text">City Polytechnic Academy</td>
                      <td className="p-3 text-emerald-700 font-semibold">Scrutiny (5 days left)</td>
                      <td className="p-3">
                        <span className="px-2 py-1 rounded bg-niyam-surface-alt text-niyam-text-muted font-bold text-[10px]">
                          In Queue
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <div className="p-3.5 rounded-xl bg-blue-50/70 border border-blue-200 text-xs text-niyam-primary flex items-center justify-between">
                <span>&bull; Dual-control return mechanism requires recorded justification for every deficiency noted.</span>
                <span className="font-bold text-[11px] underline">View Escalation SLA Matrix</span>
              </div>
            </div>
          )}

          {activeTab === 'committee' && (
            <div className="space-y-6">
              <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-niyam-border">
                <div>
                  <span className="text-xs font-bold text-niyam-text-muted">EXPERT COMMITTEE WORKSPACE</span>
                  <h3 className="text-xl font-bold text-niyam-text mt-0.5">Assigned Inspections: Prof. A. Kumar</h3>
                </div>
                <div className="flex items-center gap-2">
                  <span className="px-3 py-1 rounded-full bg-purple-100 text-purple-800 text-xs font-bold">
                    1 Upcoming Visit Scheduled
                  </span>
                </div>
              </div>

              {/* Committee Schedule Card */}
              <div className="p-5 rounded-2xl bg-white border border-niyam-border shadow-xs">
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-xs font-mono font-bold text-purple-700">EVC-2026-0881</span>
                    <h4 className="text-base font-bold text-niyam-text mt-0.5">
                      Physical Inspection: Institute of Technology Alpha
                    </h4>
                    <p className="text-xs text-niyam-text-muted mt-1">
                      Scheduled Date: <strong>29 Oct 2026</strong> &bull; Visit Mode: On-Site Physical Inspection
                    </p>
                  </div>
                  <span className="px-3 py-1 rounded-full bg-purple-50 text-purple-800 text-xs font-bold border border-purple-200">
                    Committee Chairman
                  </span>
                </div>

                <div className="mt-4 pt-4 border-t border-niyam-border/60 flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2 text-xs text-niyam-text-muted">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    <span>Conflict-of-interest disclosure verified</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="px-3 py-1 rounded-lg bg-niyam-bg border border-niyam-border text-xs font-bold text-niyam-text">
                      Download Kit
                    </span>
                    <span className="px-3 py-1 rounded-lg bg-purple-700 text-white text-xs font-bold shadow-xs">
                      Submit Inspection Report
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'bureau' && (
            <div className="space-y-6">
              <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-niyam-border">
                <div>
                  <span className="text-xs font-bold text-niyam-text-muted">EXECUTIVE OVERSIGHT &amp; ANALYTICS</span>
                  <h3 className="text-xl font-bold text-niyam-text mt-0.5">National Approval Cycle Overview (2026–27)</h3>
                </div>
                <div className="flex items-center gap-2">
                  <span className="px-3 py-1 rounded-full bg-indigo-100 text-indigo-800 text-xs font-bold">
                    All 8 Regional Offices Connected
                  </span>
                </div>
              </div>

              {/* Regional Progress Matrix Preview */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="p-3.5 rounded-xl bg-white border border-niyam-border text-center">
                  <span className="text-xs text-niyam-text-muted">Total Applications</span>
                  <p className="text-xl font-black text-niyam-text mt-1">1,248</p>
                </div>
                <div className="p-3.5 rounded-xl bg-white border border-niyam-border text-center">
                  <span className="text-xs text-niyam-text-muted">In Scrutiny</span>
                  <p className="text-xl font-black text-niyam-focus mt-1">342</p>
                </div>
                <div className="p-3.5 rounded-xl bg-white border border-niyam-border text-center">
                  <span className="text-xs text-niyam-text-muted">EVC Scheduled</span>
                  <p className="text-xl font-black text-purple-700 mt-1">189</p>
                </div>
                <div className="p-3.5 rounded-xl bg-white border border-niyam-border text-center">
                  <span className="text-xs text-niyam-text-muted">Council Decisions</span>
                  <p className="text-xl font-black text-emerald-700 mt-1">717</p>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-white border border-niyam-border flex items-center justify-between text-xs">
                <div className="flex items-center gap-2 text-niyam-text font-semibold">
                  <Shield className="w-4 h-4 text-emerald-600" />
                  <span>Audit Chain Integrity: 100% verified across 4,892 recorded events</span>
                </div>
                <span className="text-niyam-primary font-bold">Export Regulatory Report (CSV) &rarr;</span>
              </div>
            </div>
          )}

          <div className="pt-3 text-center border-t border-niyam-border/50">
            <span className="text-[11px] text-niyam-text-muted italic">
              Illustrative simulation for product demonstration purposes. Actual privileged data is protected behind authenticated login.
            </span>
          </div>
        </div>
      </div>
    </section>
  );
};
