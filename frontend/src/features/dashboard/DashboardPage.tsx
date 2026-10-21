import React, { useEffect, useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import {
  FileText,
  Clock,
  CalendarCheck,
  AlertTriangle,
  ArrowRight,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { Badge } from '../../components/Badge';
import { Card } from '../../components/Card';
import { LoadingState } from '../../components/States';
import { api } from '../../lib/apiClient';
import { DashboardMetrics } from '../../types';

interface AgeingItem {
  stage_name: string;
  under_7_days: number;
  between_7_14_days: number;
  over_14_days: number;
}

export const DashboardPage: React.FC = () => {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [ageingData, setAgeingData] = useState<AgeingItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get<DashboardMetrics>('/dashboard/summary'),
      api.get<AgeingItem[]>('/dashboard/ageing'),
    ])
      .then(([m, a]) => {
        setMetrics(m);
        setAgeingData(a);
      })
      .catch((err) => {
        console.error('Failed to load dashboard metrics', err);
        // Safe fallback for offline/development inspection
        setMetrics({
          total_applications: 14,
          in_progress: 9,
          pending_scrutiny: 4,
          pending_evc: 3,
          pending_undertakings: 5,
          overdue_items: 1,
          completed_this_cycle: 2,
          is_demo_data: true,
        });
      })
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) {
    return <LoadingState message="Loading dashboard metrics..." />;
  }

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-niyam-border">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-niyam-text">
            Workflow & Pendency Overview
          </h2>
          <p className="text-sm text-niyam-text-muted mt-1">
            Real-time monitoring across scrutiny, EVC queues, and institutional compliance.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="warning">Demonstration Data</Badge>
          <span className="text-xs text-niyam-text-muted font-medium">Cycle 2026-27</span>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="liquid-tile-grid">
        <Card className="border-l-4 border-l-niyam-primary">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-niyam-text-muted uppercase tracking-wider">
                Total Applications
              </p>
              <p className="text-2xl font-bold text-niyam-text mt-1">
                {metrics?.total_applications ?? 0}
              </p>
            </div>
            <div className="w-10 h-10 rounded-full bg-niyam-primary-tint text-niyam-primary flex items-center justify-center">
              <FileText className="w-5 h-5" />
            </div>
          </div>
          <p className="text-xs text-niyam-text-muted mt-3">Active approval cycles</p>
        </Card>

        <Card className="border-l-4 border-l-blue-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-niyam-text-muted uppercase tracking-wider">
                In Progress
              </p>
              <p className="text-2xl font-bold text-niyam-text mt-1">
                {metrics?.in_progress ?? 0}
              </p>
            </div>
            <div className="w-10 h-10 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center">
              <Clock className="w-5 h-5" />
            </div>
          </div>
          <p className="text-xs text-niyam-text-muted mt-3">Under scrutiny or committee review</p>
        </Card>

        <Card className="border-l-4 border-l-amber-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-niyam-text-muted uppercase tracking-wider">
                Pending EVC
              </p>
              <p className="text-2xl font-bold text-niyam-status-warning mt-1">
                {metrics?.pending_evc ?? 0}
              </p>
            </div>
            <div className="w-10 h-10 rounded-full bg-amber-50 text-amber-600 flex items-center justify-center">
              <CalendarCheck className="w-5 h-5" />
            </div>
          </div>
          <p className="text-xs text-niyam-text-muted mt-3">Awaiting visit scheduling</p>
        </Card>

        <Card className="border-l-4 border-l-niyam-status-danger">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold text-niyam-text-muted uppercase tracking-wider">
                Overdue / Escalated
              </p>
              <p className="text-2xl font-bold text-niyam-status-danger mt-1">
                {metrics?.overdue_items ?? 0}
              </p>
            </div>
            <div className="w-10 h-10 rounded-full bg-rose-50 text-rose-600 flex items-center justify-center">
              <AlertTriangle className="w-5 h-5" />
            </div>
          </div>
          <p className="text-xs text-niyam-text-muted mt-3">Exceeded prescribed SLA</p>
        </Card>
      </div>

      {/* Chart Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card
          className="lg:col-span-2"
          title="Stage Ageing Distribution"
          subtitle="Application count segmented by days elapsed in current workflow stage"
        >
          <div className="h-72 w-full pt-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={ageingData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <XAxis dataKey="stage_name" tick={{ fontSize: 11 }} interval={0} angle={-15} textAnchor="end" />
                <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                <Tooltip contentStyle={{ fontSize: '12px', borderRadius: '6px' }} />
                <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
                <Bar dataKey="under_7_days" name="< 7 Days" fill="#1E6B3A" radius={[4, 4, 0, 0]} />
                <Bar dataKey="between_7_14_days" name="7 - 14 Days" fill="#8A5A00" radius={[4, 4, 0, 0]} />
                <Bar dataKey="over_14_days" name="> 14 Days" fill="#B42318" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card
          title="Priority Action Items"
          subtitle="Items requiring immediate officer attention"
        >
          <div className="space-y-3 pt-2">
            <div className="p-3 rounded border border-amber-200 bg-amber-50/60">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-amber-900">EVC Report Due</span>
                <Badge variant="warning">2 Days Left</Badge>
              </div>
              <p className="text-xs text-amber-800 mt-1 font-medium">Apex Institute of Technology</p>
              <p className="text-[11px] text-amber-700">Ref: NS-DEMO-2026-0001 (NRO)</p>
            </div>

            <div className="p-3 rounded border border-rose-200 bg-rose-50/60">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-rose-900">Lease Renewal Expired</span>
                <Badge variant="danger">Escalation L1</Badge>
              </div>
              <p className="text-xs text-rose-800 mt-1 font-medium">Vanguard Engineering College</p>
              <p className="text-[11px] text-rose-700">Land Lease Expired on 2026-10-15</p>
            </div>

            <div className="pt-2">
              <Link
                to="/applications"
                className="inline-flex items-center justify-center gap-1.5 w-full py-2 text-xs font-semibold text-niyam-primary bg-niyam-primary-tint hover:bg-niyam-primary hover:text-white rounded transition-colors"
              >
                <span>View Full Application Work Queue</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};
