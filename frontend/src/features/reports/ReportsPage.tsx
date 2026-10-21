import React from 'react';
import { ShieldCheck, Download } from 'lucide-react';
import { Badge } from '../../components/Badge';
import { Button } from '../../components/Button';
import { Card } from '../../components/Card';

export const ReportsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-niyam-border">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-niyam-text">
            Reports & Tamper-Evident Audit Trail
          </h2>
          <p className="text-sm text-niyam-text-muted mt-1">
            Export regional pendency reports and cryptographically verify the append-only audit trail.
          </p>
        </div>
        <Badge variant="success">SHA-256 Hash Chain Verified</Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card title="Export Statutory Reports">
          <p className="text-xs text-niyam-text-muted mb-4">
            Download consolidated approval cycle data, regional workload metrics, and EVC outcome summaries.
          </p>
          <div className="space-y-2">
            <div className="flex items-center justify-between p-3 rounded bg-niyam-surface-alt border border-niyam-border">
              <span className="text-xs font-semibold text-niyam-text">Regional Pendency Summary (PDF)</span>
              <Button size="sm" variant="outline">
                <Download className="w-3.5 h-3.5 mr-1" />
                Export PDF
              </Button>
            </div>
            <div className="flex items-center justify-between p-3 rounded bg-niyam-surface-alt border border-niyam-border">
              <span className="text-xs font-semibold text-niyam-text">EVC Outcomes & Timelines (CSV)</span>
              <Button size="sm" variant="outline">
                <Download className="w-3.5 h-3.5 mr-1" />
                Export CSV
              </Button>
            </div>
          </div>
        </Card>

        <Card title="Cryptographic Audit Integrity">
          <div className="p-4 rounded-lg bg-emerald-50/50 border border-emerald-200">
            <div className="flex items-start gap-3">
              <ShieldCheck className="w-6 h-6 text-emerald-700 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-sm font-semibold text-emerald-900">Hash-Chain Verification Intact</h4>
                <p className="text-xs text-emerald-800 mt-1">
                  Every state transition, document review, and administrative action is chained using SHA-256 hashes.
                  No record can be modified or deleted without invalidating the audit chain.
                </p>
                <div className="mt-3">
                  <Button size="sm" variant="secondary" className="bg-white border border-emerald-300 text-emerald-900">
                    Run Hash-Chain Integrity Audit
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};
