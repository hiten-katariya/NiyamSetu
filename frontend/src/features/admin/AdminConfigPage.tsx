import React from 'react';
import { Badge } from '../../components/Badge';
import { Button } from '../../components/Button';
import { Card } from '../../components/Card';

export const AdminConfigPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-niyam-border">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-niyam-text">
            Admin System Configuration
          </h2>
          <p className="text-sm text-niyam-text-muted mt-1">
            Configure approval routes, stage timelines, reminder offsets, and escalation tiers without code deployment.
          </p>
        </div>
        <Badge variant="warning">Rules Stored In Database</Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card title="Configurable Route Types" subtitle="Ordered sequence of approval stages">
          <div className="p-3 rounded bg-niyam-surface-alt border border-niyam-border mb-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-niyam-text">Sample Scrutiny + EVC Route</span>
              <Badge variant="success">Active (v1)</Badge>
            </div>
            <p className="text-xs text-niyam-text-muted mt-1">
              6 stages: Scrutiny (7d) → Re-Scrutiny (5d) → EVC Scheduling (10d) → EVC Conduct (7d) → Report Review (5d) → Decision (7d)
            </p>
          </div>
          <Button size="sm" variant="outline">
            + Configure New Route Type
          </Button>
        </Card>

        <Card title="Automated Escalation Chains" subtitle="Tiered SLA breaches and recipient matrix">
          <div className="p-3 rounded bg-niyam-surface-alt border border-niyam-border mb-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-niyam-text">Level 1 Escalation: Stage Overdue (+1 Day)</span>
              <Badge variant="danger">Escalates to RO</Badge>
            </div>
            <p className="text-xs text-niyam-text-muted mt-1">
              Triggered 1 day past stage deadline. Notifies Regional Officer and flags application red.
            </p>
          </div>
          <Button size="sm" variant="outline">
            + Add Escalation Rule
          </Button>
        </Card>
      </div>
    </div>
  );
};
