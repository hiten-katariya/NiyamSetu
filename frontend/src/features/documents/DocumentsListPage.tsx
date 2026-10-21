import React from 'react';
import { AlertTriangle, FileText } from 'lucide-react';
import { Badge } from '../../components/Badge';
import { Card } from '../../components/Card';

export const DocumentsListPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-niyam-border">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-niyam-text">
            Institutional Document Validity & Lease Renewal
          </h2>
          <p className="text-sm text-niyam-text-muted mt-1">
            Validity tracking for land leases, building completion certificates, and statutory approvals.
          </p>
        </div>
        <Badge variant="warning">1 Expired Document</Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="border-l-4 border-l-emerald-500">
          <p className="text-xs text-niyam-text-muted font-medium">Valid Documents</p>
          <p className="text-xl font-bold text-niyam-text mt-1">42 Registered</p>
          <p className="text-[11px] text-emerald-700 mt-2">Within validity period</p>
        </Card>
        <Card className="border-l-4 border-l-amber-500">
          <p className="text-xs text-niyam-text-muted font-medium">Expiring Soon (30 Days)</p>
          <p className="text-xl font-bold text-niyam-status-warning mt-1">3 Documents</p>
          <p className="text-[11px] text-amber-700 mt-2">Renewal alerts dispatched</p>
        </Card>
        <Card className="border-l-4 border-l-rose-500">
          <p className="text-xs text-niyam-text-muted font-medium">Expired Leases</p>
          <p className="text-xl font-bold text-niyam-status-danger mt-1">1 Document</p>
          <p className="text-[11px] text-rose-700 mt-2">Immediate notice issued</p>
        </Card>
      </div>

      <Card title="Document Registry (Demo Snapshot)">
        <div className="divide-y divide-niyam-border text-sm">
          <div className="py-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <FileText className="w-4 h-4 text-niyam-text-muted" />
              <div>
                <p className="font-semibold text-niyam-text">Registered Land Lease Agreement (30 Years)</p>
                <p className="text-xs text-niyam-text-muted">Apex Institute of Technology • Valid till 2045-06-30</p>
              </div>
            </div>
            <Badge variant="success">Valid</Badge>
          </div>
          <div className="py-3 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-4 h-4 text-niyam-status-danger" />
              <div>
                <p className="font-semibold text-niyam-text">Occupancy & Building Safety Certificate</p>
                <p className="text-xs text-niyam-text-muted">Vanguard Engineering College • Expired on 2026-10-15</p>
              </div>
            </div>
            <Badge variant="danger">Expired</Badge>
          </div>
        </div>
      </Card>
    </div>
  );
};
