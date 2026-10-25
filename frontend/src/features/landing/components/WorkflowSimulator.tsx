import React, { useState } from 'react';
import {
  FileSpreadsheet,
  CheckCircle2,
  CalendarCheck,
  Building2,
  Award,
  ArrowRight,
  Sparkles,
  Hash,
  User,
} from 'lucide-react';

interface StageConfig {
  id: string;
  name: string;
  role: string;
  roleColor: string;
  icon: React.ElementType;
  description: string;
  checklist: string[];
  mockHash: string;
  statusBadge: string;
}

const STAGES: StageConfig[] = [
  {
    id: 'draft',
    name: '1. Drafting & Upload',
    role: 'Institution Administrator',
    roleColor: 'bg-blue-50 text-blue-700 border-blue-200',
    icon: FileSpreadsheet,
    description: 'The participating college uploads infrastructure records, faculty headcount, and mandatory state affidavits.',
    checklist: [
      'Land Ownership Title Deed & Registration',
      'AICTE Approved Building Safety Certificate',
      'Faculty Cadre Ratio & Qualification Verification',
      'AICTE Approved Corpus Fund Bank Guarantee',
    ],
    mockHash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    statusBadge: 'Draft Submitted',
  },
  {
    id: 'scrutiny',
    name: '2. Scrutiny Verification',
    role: 'Scrutiny Officer Desk',
    roleColor: 'bg-amber-50 text-amber-800 border-amber-200',
    icon: CheckCircle2,
    description: 'Assigned scrutiny desk officer examines documents against regulatory norms with clear return deficiency logs.',
    checklist: [
      'Municipal Master Plan Consistency Check',
      'AICTE Norms Compliance for Laboratories',
      'Fire & Life Safety NOC Validity Window',
      'Anti-Ragging Committee Formation Affidavit',
    ],
    mockHash: '19a28bf450de7e2e8316dfc68b248a391a8ff4a371c6f93ab2374e2a8751fbc9',
    statusBadge: 'Deficiencies Cleared',
  },
  {
    id: 'evc',
    name: '3. Committee Inspection',
    role: 'Expert Visit Committee',
    roleColor: 'bg-purple-50 text-purple-700 border-purple-200',
    icon: Building2,
    description: 'A 3-member panel of subject matter experts conducts an on-site or virtual infrastructure audit with timestamped video.',
    checklist: [
      'Campus Physical Boundary & Geolocation Match',
      'Computer Center & High-Speed Bandwidth Test',
      'Library Book Bank & Digital Journal Subscription',
      'Student Welfare & Barrier-Free Access Facilities',
    ],
    mockHash: '4a6b29f0e1379c13e3be851392683fb9c869c9b1392f5d96f923c8e472a159e8',
    statusBadge: 'Recommendation Filed',
  },
  {
    id: 'undertaking',
    name: '4. Compliance Clearance',
    role: 'Regional Officer Verification',
    roleColor: 'bg-teal-50 text-teal-800 border-teal-200',
    icon: CalendarCheck,
    description: 'Institution provides time-bound legal undertakings for any minor conditional observations with dual-officer signoff.',
    checklist: [
      'Time-Bound Legal Affidavit with Stamp Seal',
      'Escrow Account Deposit Slip Verification',
      'Regional Directorate Scrutiny Concurrence',
      'Zero Outstanding Deficiency Certificate',
    ],
    mockHash: '7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069',
    statusBadge: 'Undertakings Validated',
  },
  {
    id: 'decision',
    name: '5. Council Determination',
    role: 'Senior Authority & Bureau',
    roleColor: 'bg-emerald-50 text-emerald-800 border-emerald-200',
    icon: Award,
    description: 'Final human decision-maker evaluates combined recommendations and executes authorized statutory approval or denial.',
    checklist: [
      'Full End-to-End Audit Hash Chain Recomputed',
      'Dual-Key Bureau Officer Digital Countersign',
      'Formal AICTE Extension of Approval (EoA) Grant',
      'Statutory Human Decision Log Permanently Sealed',
    ],
    mockHash: '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8',
    statusBadge: 'Final Approval Issued',
  },
];

export const WorkflowSimulator: React.FC = () => {
  const [activeStageIdx, setActiveStageIdx] = useState(0);
  const [checkedItems, setCheckedItems] = useState<Record<string, boolean>>({
    '0-0': true,
    '0-1': true,
    '1-0': true,
  });

  const stage = STAGES[activeStageIdx];
  const Icon = stage.icon;

  const toggleCheck = (id: string) => {
    setCheckedItems((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  return (
    <section className="py-20 bg-gradient-to-b from-white via-niyam-bg/50 to-white border-t border-niyam-border/70">
      <div className="liquid-container">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-14">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-niyam-primary-tint border border-niyam-primary/20 text-niyam-primary text-xs font-bold uppercase tracking-wider mb-3">
            <Sparkles className="w-3.5 h-3.5 text-amber-500" />
            <span>Interactive Lifecycle Simulator</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-niyam-text tracking-tight">
            Experience the 5-Stage Approval Architecture
          </h2>
          <p className="mt-3 text-base sm:text-lg text-niyam-text-muted">
            Click through the regulatory milestones below to inspect how role permissions, scrutiny checklists, and cryptographic SHA-256 blocks connect at every transition.
          </p>
        </div>

        {/* Step Selector Pills */}
        <div className="flex flex-wrap items-center justify-center gap-2 mb-8">
          {STAGES.map((s, idx) => {
            const isActive = idx === activeStageIdx;
            return (
              <button
                key={s.id}
                onClick={() => setActiveStageIdx(idx)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs sm:text-sm font-bold transition-all ${
                  isActive
                    ? 'bg-niyam-primary text-white shadow-md scale-105'
                    : 'bg-white border border-niyam-border text-niyam-text hover:bg-niyam-surface-alt'
                }`}
              >
                <span>{s.name}</span>
                {idx < activeStageIdx && (
                  <CheckCircle2 className="w-4 h-4 text-emerald-300" />
                )}
              </button>
            );
          })}
        </div>

        {/* Interactive Simulator Stage Card */}
        <div className="max-w-4xl mx-auto rounded-3xl bg-white border border-niyam-border shadow-xl p-6 sm:p-10 relative overflow-hidden">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-8">
            {/* Left 3 cols: Stage Details & Checklist */}
            <div className="md:col-span-3 space-y-6">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <span className={`px-3 py-1 rounded-full text-xs font-bold border ${stage.roleColor}`}>
                  <User className="w-3.5 h-3.5 inline mr-1 -mt-0.5" />
                  {stage.role}
                </span>
                <span className="px-3 py-1 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-bold">
                  {stage.statusBadge}
                </span>
              </div>

              <div>
                <h3 className="text-2xl font-black text-niyam-text flex items-center gap-2.5">
                  <div className="w-9 h-9 rounded-xl bg-niyam-primary-tint flex items-center justify-center text-niyam-primary">
                    <Icon className="w-5 h-5" />
                  </div>
                  <span>{stage.name}</span>
                </h3>
                <p className="mt-2 text-sm text-niyam-text-muted leading-relaxed">
                  {stage.description}
                </p>
              </div>

              {/* Interactive Scrutiny Checklist */}
              <div>
                <h4 className="text-xs font-extrabold text-niyam-text uppercase tracking-wider mb-3">
                  Verification Protocol &bull; Click to Check
                </h4>
                <div className="space-y-2.5">
                  {stage.checklist.map((item, idx) => {
                    const key = `${activeStageIdx}-${idx}`;
                    const isChecked = Boolean(checkedItems[key]);
                    return (
                      <div
                        key={idx}
                        onClick={() => toggleCheck(key)}
                        className={`flex items-start gap-3 p-3 rounded-xl border transition-all cursor-pointer ${
                          isChecked
                            ? 'bg-emerald-50/60 border-emerald-200 text-emerald-900 shadow-xs'
                            : 'bg-slate-50 border-slate-200 text-slate-700 hover:bg-slate-100'
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => toggleCheck(key)}
                          className="mt-0.5 rounded text-niyam-primary focus:ring-niyam-focus cursor-pointer"
                        />
                        <span className="text-xs font-semibold">{item}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Right 2 cols: Cryptographic Block Inspector */}
            <div className="md:col-span-2 rounded-2xl bg-slate-900 text-white p-6 flex flex-col justify-between shadow-inner">
              <div className="space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                  <div className="flex items-center gap-1.5 text-xs font-mono text-purple-300">
                    <Hash className="w-3.5 h-3.5" />
                    <span>LEDGER BLOCK #{100 + activeStageIdx * 4}</span>
                  </div>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                    VERIFIED
                  </span>
                </div>

                <div>
                  <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                    SHA-256 State Transition Hash
                  </span>
                  <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 font-mono text-[11px] text-amber-300 break-all leading-tight">
                    {stage.mockHash}
                  </div>
                </div>

                <div className="space-y-2 text-xs">
                  <div className="flex justify-between text-slate-400">
                    <span>Actor Role:</span>
                    <span className="font-semibold text-white">{stage.role}</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Chain Integrity:</span>
                    <span className="font-semibold text-emerald-400">Linked to Block #{99 + activeStageIdx * 4}</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Statutory AICTE Prerogative:</span>
                    <span className="font-semibold text-white">Preserved Human Signoff</span>
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-800">
                <button
                  onClick={() => setActiveStageIdx((prev) => (prev + 1) % STAGES.length)}
                  className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-niyam-primary text-white text-xs font-bold hover:bg-niyam-primary-hover transition-colors shadow-xs"
                >
                  <span>Advance to Next Stage</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
