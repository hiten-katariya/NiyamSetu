import React from 'react';
import { Calendar, Users, FileCheck } from 'lucide-react';
import { Badge } from '../../components/Badge';
import { Button } from '../../components/Button';
import { Card } from '../../components/Card';

export const EVCListPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-niyam-border">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-niyam-text">
            Expert Visit Committee (EVC) Queue
          </h2>
          <p className="text-sm text-niyam-text-muted mt-1">
            Schedule visits, assign committee members, track inspection conduct, and review reports.
          </p>
        </div>
        <Badge variant="info">EVC Queue Active</Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-blue-50 text-niyam-primary flex items-center justify-center">
              <Calendar className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-niyam-text-muted font-medium">To Be Scheduled</p>
              <p className="text-xl font-bold text-niyam-text">3 Visits</p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-amber-50 text-niyam-status-warning flex items-center justify-center">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-niyam-text-muted font-medium">Conducted (Pending Report)</p>
              <p className="text-xl font-bold text-niyam-text">2 Reports</p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-emerald-50 text-niyam-status-success flex items-center justify-center">
              <FileCheck className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-niyam-text-muted font-medium">Reports Reviewed & Closed</p>
              <p className="text-xl font-bold text-niyam-text">8 Completed</p>
            </div>
          </div>
        </Card>
      </div>

      <Card title="EVC Scheduling Queue (Demonstration)">
        <div className="p-4 rounded-lg bg-niyam-surface-alt border border-niyam-border text-center py-12">
          <Calendar className="w-8 h-8 text-niyam-text-muted mx-auto mb-2" />
          <h4 className="text-sm font-semibold text-niyam-text">EVC Workflow Pipeline</h4>
          <p className="text-xs text-niyam-text-muted max-w-md mx-auto mt-1 mb-4">
            EVC visits are queued automatically once preliminary scrutiny stages are passed.
            Committee assignment and calendar date locking will be enabled in Phase 5.
          </p>
          <Button size="sm" variant="outline">
            View Regional EVC Calendar
          </Button>
        </div>
      </Card>
    </div>
  );
};
