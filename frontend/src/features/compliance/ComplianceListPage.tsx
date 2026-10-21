import React from 'react';
import { ShieldCheck } from 'lucide-react';
import { Badge } from '../../components/Badge';
import { Card } from '../../components/Card';

export const ComplianceListPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-niyam-border">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-niyam-text">
            Time-Bound Undertakings & Institutional Compliance
          </h2>
          <p className="text-sm text-niyam-text-muted mt-1">
            Monitor conditions precedent, evidence submissions, and authorized verification.
          </p>
        </div>
        <Badge variant="neutral">Tracking Module</Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card title="Active Undertaking Conditions">
          <div className="space-y-3 pt-2">
            <div className="p-3 rounded border border-niyam-border bg-niyam-surface-alt">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-niyam-text">Fire Safety NOC Submission</span>
                <Badge variant="warning">Due in 5 Days</Badge>
              </div>
              <p className="text-xs text-niyam-text-muted mt-1">Apex Institute of Technology</p>
            </div>
            <div className="p-3 rounded border border-niyam-border bg-niyam-surface-alt">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-niyam-text">Faculty Cadre Ratio Rectification</span>
                <Badge variant="success">Submitted (Under Verification)</Badge>
              </div>
              <p className="text-xs text-niyam-text-muted mt-1">Vanguard Engineering College</p>
            </div>
          </div>
        </Card>

        <Card title="Compliance Verification Guidelines">
          <div className="flex items-start gap-3 p-3 rounded bg-blue-50/50 border border-blue-200">
            <ShieldCheck className="w-5 h-5 text-niyam-primary shrink-0 mt-0.5" />
            <div className="text-xs text-niyam-text space-y-1">
              <p className="font-semibold text-niyam-primary">Strict Dual-Control Verification</p>
              <p className="text-niyam-text-muted">
                Evidence uploaded by institutions must be reviewed and endorsed by an authorized officer.
                The system records tamper-evident audit logs with every decision.
              </p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};
