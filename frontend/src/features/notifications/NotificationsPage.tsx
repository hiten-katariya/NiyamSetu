import React from 'react';
import { BellRing, AlertOctagon } from 'lucide-react';
import { Badge } from '../../components/Badge';
import { Card } from '../../components/Card';

export const NotificationsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-niyam-border">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-niyam-text">
            Notifications & Escalation Alerts
          </h2>
          <p className="text-sm text-niyam-text-muted mt-1">
            Automated deadline reminders, institutional notifications, and SLA escalations.
          </p>
        </div>
        <Badge variant="info">Deduplicated Pipeline</Badge>
      </div>

      <div className="space-y-3">
        <Card className="border-l-4 border-l-niyam-status-danger">
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-3">
              <AlertOctagon className="w-5 h-5 text-niyam-status-danger shrink-0 mt-0.5" />
              <div>
                <div className="flex items-center gap-2">
                  <h4 className="text-sm font-semibold text-niyam-text">
                    Escalation Level 1: Document Scrutiny SLA Exceeded
                  </h4>
                  <Badge variant="danger">Escalation L1</Badge>
                </div>
                <p className="text-xs text-niyam-text-muted mt-1">
                  Application NS-DEMO-2026-0001 has been in Document Scrutiny for 8 days (Target SLA: 7 working days).
                  Escalated to Regional Officer (NRO) as per Escalation Rule #ESC-01.
                </p>
                <p className="text-[11px] text-niyam-text-muted mt-2">Triggered: Today at 00:00 UTC</p>
              </div>
            </div>
            <button className="text-xs font-semibold text-niyam-primary hover:underline cursor-pointer">
              View Case
            </button>
          </div>
        </Card>

        <Card className="border-l-4 border-l-amber-500">
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-3">
              <BellRing className="w-5 h-5 text-niyam-status-warning shrink-0 mt-0.5" />
              <div>
                <div className="flex items-center gap-2">
                  <h4 className="text-sm font-semibold text-niyam-text">
                    Reminder: EVC Committee Scheduling Approaching Due Date
                  </h4>
                  <Badge variant="warning">Due in 3 Days</Badge>
                </div>
                <p className="text-xs text-niyam-text-muted mt-1">
                  Application NS-DEMO-2026-0002 requires committee member assignment and inspection date locking.
                </p>
                <p className="text-[11px] text-niyam-text-muted mt-2">Triggered: Yesterday at 00:00 UTC</p>
              </div>
            </div>
            <button className="text-xs font-semibold text-niyam-primary hover:underline cursor-pointer">
              Schedule Now
            </button>
          </div>
        </Card>
      </div>
    </div>
  );
};
