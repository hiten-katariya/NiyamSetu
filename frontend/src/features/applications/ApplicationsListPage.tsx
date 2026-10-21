import React, { useState } from 'react';
import { Badge } from '../../components/Badge';
import { Button } from '../../components/Button';
import { Table, Column } from '../../components/Table';
import { ApplicationItem } from '../../types';

export const ApplicationsListPage: React.FC = () => {
  const [filter, setFilter] = useState('all');

  // Demonstration seed data representation
  const sampleApplications: ApplicationItem[] = [
    {
      id: 'app-001',
      reference_no: 'NS-DEMO-2026-0001',
      institution_id: 'Apex Institute of Technology & Management',
      route_type_id: 'Sample Scrutiny + EVC Route',
      route_version: 1,
      current_stage_id: 'Document Scrutiny',
      status: 'in_progress',
      submitted_at: '2026-10-18T10:00:00Z',
    },
    {
      id: 'app-002',
      reference_no: 'NS-DEMO-2026-0002',
      institution_id: 'Vanguard Engineering College',
      route_type_id: 'Sample Scrutiny + EVC Route',
      route_version: 1,
      current_stage_id: 'EVC Committee Scheduling',
      status: 'in_progress',
      submitted_at: '2026-10-12T14:30:00Z',
    },
    {
      id: 'app-003',
      reference_no: 'NS-DEMO-2026-0003',
      institution_id: 'National Polytechnic College',
      route_type_id: 'Sample Scrutiny + EVC Route',
      route_version: 1,
      current_stage_id: 'Competent Authority Decision Review',
      status: 'pending_review',
      submitted_at: '2026-10-05T09:15:00Z',
    },
  ];

  const columns: Column<ApplicationItem>[] = [
    {
      header: 'Reference No.',
      cell: (item) => (
        <span className="font-semibold text-niyam-primary hover:underline cursor-pointer">
          {item.reference_no}
        </span>
      ),
    },
    {
      header: 'Institution',
      accessorKey: 'institution_id',
    },
    {
      header: 'Workflow Route',
      cell: (item) => (
        <span className="text-xs text-niyam-text-muted">
          {item.route_type_id} (v{item.route_version})
        </span>
      ),
    },
    {
      header: 'Current Stage',
      cell: (item) => (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-niyam-surface-alt border border-niyam-border">
          {item.current_stage_id}
        </span>
      ),
    },
    {
      header: 'Status',
      cell: (item) => (
        <Badge variant={item.status === 'in_progress' ? 'info' : 'warning'}>
          {item.status.replace('_', ' ')}
        </Badge>
      ),
    },
    {
      header: 'Actions',
      cell: () => (
        <div className="flex items-center gap-2">
          <Button size="sm" variant="outline">
            Review
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-niyam-border">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-niyam-text">
            Approval Applications
          </h2>
          <p className="text-sm text-niyam-text-muted mt-1">
            Browse and process institutional approval applications across configurable workflow stages.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button size="sm">
            + New Application
          </Button>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-niyam-border pb-3">
        {['all', 'in_progress', 'evc_scheduled', 'overdue'].map((tab) => (
          <button
            key={tab}
            onClick={() => setFilter(tab)}
            className={`px-3 py-1.5 rounded-md text-xs font-semibold uppercase tracking-wider transition-colors cursor-pointer ${
              filter === tab
                ? 'bg-niyam-primary text-white'
                : 'text-niyam-text-muted hover:bg-niyam-surface-alt hover:text-niyam-text'
            }`}
          >
            {tab.replace('_', ' ')}
          </button>
        ))}
      </div>

      {/* Table */}
      <Table
        columns={columns}
        data={sampleApplications}
        keyExtractor={(item) => item.id}
      />
    </div>
  );
};
