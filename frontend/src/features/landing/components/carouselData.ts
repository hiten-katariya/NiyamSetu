import { CarouselItem } from '../../../components/CircularCarousel/CircularCarousel';

const createCardSvg = (
  moduleNumber: string,
  title: string,
  subtitle: string,
  badgeText: string,
  badgeColor: string,
  badgeBg: string,
  accentColor: string,
  steps: Array<{ num: string; name: string; desc: string; status: string; statusColor: string; statusBg: string }>
) => {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FFFFFF" />
      <stop offset="100%" stop-color="#F1F5F9" />
    </linearGradient>
    <filter id="shadow" x="-5%" y="-5%" width="110%" height="110%">
      <feDropShadow dx="0" dy="4" stdDeviation="8" flood-color="#0F172A" flood-opacity="0.06" />
    </filter>
  </defs>

  <rect width="600" height="600" rx="28" fill="url(#bgGrad)" />
  <rect x="12" y="12" width="576" height="576" rx="24" fill="none" stroke="#CBD5E1" stroke-width="2" />

  <!-- Badge -->
  <rect x="40" y="40" width="160" height="32" rx="16" fill="${badgeBg}" />
  <text x="120" y="61" font-family="Inter, system-ui, sans-serif" font-size="12" font-weight="800" fill="${badgeColor}" text-anchor="middle" letter-spacing="0.5">${moduleNumber}</text>

  <!-- Title -->
  <text x="40" y="112" font-family="Inter, system-ui, sans-serif" font-size="28" font-weight="900" fill="#0F172A">${title}</text>
  <text x="40" y="140" font-family="Inter, system-ui, sans-serif" font-size="14" font-weight="600" fill="#475569">${subtitle}</text>

  <!-- Process Steps -->
  <g transform="translate(40, 168)">
    ${steps
      .map(
        (s, idx) => `
    <g transform="translate(0, ${idx * 82})" filter="url(#shadow)">
      <rect width="520" height="68" rx="12" fill="#FFFFFF" stroke="${idx === 1 ? accentColor : '#E2E8F0'}" stroke-width="${idx === 1 ? '2' : '1.5'}" />
      <circle cx="36" cy="34" r="16" fill="${idx === 1 ? accentColor : '#F1F5F9'}" />
      <text x="36" y="39" font-family="Inter, sans-serif" font-size="13" font-weight="800" fill="${idx === 1 ? '#FFFFFF' : '#475569'}" text-anchor="middle">${s.num}</text>
      <text x="70" y="30" font-family="Inter, sans-serif" font-size="14" font-weight="800" fill="#0F172A">${s.name}</text>
      <text x="70" y="50" font-family="Inter, sans-serif" font-size="11" font-weight="500" fill="#64748B">${s.desc}</text>
      <rect x="410" y="22" width="90" height="24" rx="12" fill="${s.statusBg}" />
      <text x="455" y="38" font-family="Inter, sans-serif" font-size="11" font-weight="700" fill="${s.statusColor}" text-anchor="middle">${s.status}</text>
    </g>
    ${idx < steps.length - 1 ? `<line x1="36" y1="${idx * 82 + 68}" x2="36" y2="${(idx + 1) * 82}" stroke="#CBD5E1" stroke-width="2" stroke-dasharray="3 3" />` : ''}
    `
      )
      .join('')}
  </g>

  <!-- Bottom Metric Bar -->
  <g transform="translate(40, 520)">
    <rect width="520" height="42" rx="10" fill="${accentColor}" />
    <text x="260" y="26" font-family="Inter, sans-serif" font-size="12" font-weight="700" fill="#FFFFFF" text-anchor="middle" letter-spacing="0.3">${badgeText}</text>
  </g>
</svg>`;

  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
};

export const CAROUSEL_MODULES: CarouselItem[] = [
  {
    src: createCardSvg(
      'CORE MODULE 01',
      'Workflow Engine',
      'Dynamic Stage Progression & Pinned Routes',
      'PINNED ROUTE VERSIONS • ROLE-BASED ACCESS CONTROL',
      '#0369A1',
      '#E0F2FE',
      '#0284C7',
      [
        { num: '1', name: 'Institutional Drafting', desc: 'Application preparation & document bundling', status: 'Completed', statusColor: '#16A34A', statusBg: '#DCFCE7' },
        { num: '2', name: 'Scrutiny Officer Desk', desc: 'Verification, return flags & deficiency notices', status: 'In Review', statusColor: '#D97706', statusBg: '#FEF3C7' },
        { num: '3', name: 'Council Signoff', desc: 'Dual-authorized regulatory determination', status: 'Pending', statusColor: '#64748B', statusBg: '#F1F5F9' },
      ]
    ),
    alt: 'Configurable Application Workflow Routing Engine',
    title: 'Workflow Engine',
    subtitle: 'Dynamic Stage Progression & Pinned Route Versions',
  },
  {
    src: createCardSvg(
      'CORE MODULE 02',
      'Deadline Intelligence',
      'Working-Day SLAs & Automatic Escalation',
      'WORKING-DAY CALENDAR • MULTI-LEVEL NOTIFICATIONS',
      '#0D9488',
      '#CCFBF1',
      '#0F766E',
      [
        { num: '1', name: 'SLA Engine Clock', desc: 'Strict regulatory calendar day calculation', status: 'Active', statusColor: '#16A34A', statusBg: '#DCFCE7' },
        { num: '2', name: 'Automated Reminders', desc: 'Email dispatch at T-7, T-3 and T-1 days', status: 'Scheduled', statusColor: '#0284C7', statusBg: '#E0F2FE' },
        { num: '3', name: 'Breach Escalation', desc: 'Hierarchical notify to Regional Directorate', status: 'Guarded', statusColor: '#64748B', statusBg: '#F1F5F9' },
      ]
    ),
    alt: 'Deadline Intelligence and Working-Day Calendar Calculations',
    title: 'Deadline Intelligence',
    subtitle: 'Working-Day SLAs, Reminders & Escalations',
  },
  {
    src: createCardSvg(
      'CORE MODULE 03',
      'EVC Management',
      'Expert Visit Committee Dispatch & Audits',
      'EXPERTISE SCOPING • TAMPER-FREE REPORT REPOSITORIES',
      '#7C3AED',
      '#EDE9FE',
      '#6D28D9',
      [
        { num: '1', name: 'Committee Formation', desc: 'Subject expert allocation & conflict checks', status: 'Assigned', statusColor: '#16A34A', statusBg: '#DCFCE7' },
        { num: '2', name: 'Inspection Verification', desc: 'Campus geo-tagged findings & video log', status: 'Underway', statusColor: '#D97706', statusBg: '#FEF3C7' },
        { num: '3', name: 'Outcome Submission', desc: 'Official recommendations to Regional Officer', status: 'Pending', statusColor: '#64748B', statusBg: '#F1F5F9' },
      ]
    ),
    alt: 'Expert Visit Committee Scheduling and Audit Verification',
    title: 'EVC Management',
    subtitle: 'Committee Scoping & Inspection Review',
  },
  {
    src: createCardSvg(
      'CORE MODULE 04',
      'Compliance Undertakings',
      'Time-Bound Regulatory Commitments',
      'DUAL-CONTROL EVIDENCE VERIFICATION • DEFICIENCY TRACKING',
      '#B45309',
      '#FEF3C7',
      '#D97706',
      [
        { num: '1', name: 'Undertaking Submission', desc: 'Legal institutional affidavit attachment', status: 'Submitted', statusColor: '#16A34A', statusBg: '#DCFCE7' },
        { num: '2', name: 'Evidence Verification', desc: 'Documentary proof cross-examination', status: 'Verifying', statusColor: '#0284C7', statusBg: '#E0F2FE' },
        { num: '3', name: 'Statutory Clearance', desc: 'Clearance certification or hold status', status: 'Pending', statusColor: '#64748B', statusBg: '#F1F5F9' },
      ]
    ),
    alt: 'Time-Bound Undertakings and Dual-Control Evidence Verification',
    title: 'Compliance Undertakings',
    subtitle: 'Time-Bound Conditions & Approval',
  },
  {
    src: createCardSvg(
      'CORE MODULE 05',
      'Document Governance',
      'Validity Timelines, Renewals & Checksums',
      'MAGIC-BYTE MIME VALIDATION • TAMPER-FREE VAULT',
      '#1E40AF',
      '#DBEAFE',
      '#1D4ED8',
      [
        { num: '1', name: 'Payload Sanitization', desc: 'MIME validation & path-traversal prevention', status: 'Secure', statusColor: '#16A34A', statusBg: '#DCFCE7' },
        { num: '2', name: 'Lifecycle Tracking', desc: 'Annual renewal triggers and expiry alarms', status: 'Monitoring', statusColor: '#0284C7', statusBg: '#E0F2FE' },
        { num: '3', name: 'Secure Document Vault', desc: 'Role-scoped retrieval & audit signatures', status: 'Protected', statusColor: '#16A34A', statusBg: '#DCFCE7' },
      ]
    ),
    alt: 'Document Expiry Tracking and Versioned Renewal History',
    title: 'Document Governance',
    subtitle: 'Validity Timelines & Checksums',
  },
  {
    src: createCardSvg(
      'CORE MODULE 06',
      'Audit Hash Chain',
      'SHA-256 Tamper-Evident Ledger',
      'CRYPTOGRAPHIC HASH CHAINS • ZERO SILENT MUTATIONS',
      '#047857',
      '#D1FAE5',
      '#059669',
      [
        { num: '1', name: 'Action Event Ingestion', desc: 'State change captures with actor signature', status: 'Hashed', statusColor: '#16A34A', statusBg: '#DCFCE7' },
        { num: '2', name: 'Block Linkage', desc: 'Previous block hash linked via SHA-256', status: 'Linked', statusColor: '#16A34A', statusBg: '#DCFCE7' },
        { num: '3', name: 'Ledger Audit API', desc: 'Automated tampering verification tool', status: 'Verified', statusColor: '#16A34A', statusBg: '#DCFCE7' },
      ]
    ),
    alt: 'Cryptographic SHA-256 Chained Audit Trail and Tamper Alarms',
    title: 'Audit Hash Chain',
    subtitle: 'Immutable Ledger & Verification',
  },
];
