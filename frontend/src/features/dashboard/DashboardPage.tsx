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
  PauseCircle,
  CheckCircle2,
  Filter,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { Badge } from '../../components/Badge';
import { Card } from '../../components/Card';
import { LoadingState } from '../../components/States';
import { api } from '../../lib/apiClient';
import {
  AgeingMetric,
  AttentionItem,
  DashboardMetrics,
  PendencyMetrics,
} from '../../types';

export const DashboardPage: React.FC = () => {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [ageingData, setAgeingData] = useState<AgeingMetric[]>([]);
  const [pendency, setPendency] = useState<PendencyMetrics | null>(null);
  const [attentionItems, setAttentionItems] = useState<AttentionItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get<DashboardMetrics>('/dashboard/summary'),
      api.get<AgeingMetric[]>('/dashboard/ageing'),
      api.get<PendencyMetrics>('/dashboard/pendency'),
      api.get<AttentionItem[]>('/dashboard/attention'),
    ])
      .then(([m, a, p, att]) => {
        setMetrics(m);
        setAgeingData(a);
        setPendency(p);
        setAttentionItems(att);
      })
      .catch((err) => {
        console.error('Failed to load dashboard metrics', err);
        setMetrics({
          total_applications: 1,
          in_progress: 1,
          pending_scrutiny: 1,
          pending_evc: 0,
          pending_undertakings: 0,
          overdue_items: 0,
          completed_this_cycle: 0,
          is_demo_data: false,
        });
      })
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) {
    return <LoadingState message="Loading live workflow metrics..." />;
  }

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case 'critical':
        return <Badge variant="danger">Critical SLA</Badge>;
      case 'high':
        return <Badge variant="warning">Due Soon</Badge>;
      case 'medium':
        return <Badge variant="neutral">On Hold</Badge>;
      default:
        return <Badge variant="info">Action Req</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-niyam-border">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-niyam-text">
            Workflow & Pendency Overview
          </h2>
          <p className="text-sm text-niyam-text-muted mt-1">
            Real-time deadline calculation, working-day SLA monitoring, and stage ageing analytics.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {metrics?.is_demo_data ? (
            <Badge variant="warning">Demonstration Data</Badge>
          ) : (
            <Badge variant="success">Live System Data</Badge>
          )}
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
                Due Soon / At Risk
              </p>
              <p className="text-2xl font-bold text-niyam-status-warning mt-1">
                {pendency?.due_soon_count ?? 0}
              </p>
            </div>
            <div className="w-10 h-10 rounded-full bg-amber-50 text-amber-600 flex items-center justify-center">
              <CalendarCheck className="w-5 h-5" />
            </div>
          </div>
          <p className="text-xs text-niyam-text-muted mt-3">Within reminder SLA window</p>
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
          <p className="text-xs text-niyam-text-muted mt-3">Exceeded prescribed SLA timeline</p>
        </Card>
      </div>

      {/* Pendency Summary Strip */}
      {pendency && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="bg-niyam-surface p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-niyam-text-muted uppercase">On Hold Applications</span>
              <PauseCircle className="w-4 h-4 text-amber-500" />
            </div>
            <p className="text-xl font-bold text-niyam-text mt-1">{pendency.on_hold_count}</p>
            <p className="text-[11px] text-niyam-text-muted mt-1">SLA clocks paused under administrative order</p>
          </Card>

          <Card className="bg-niyam-surface p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-niyam-text-muted uppercase">Pending Scrutiny</span>
              <Filter className="w-4 h-4 text-blue-500" />
            </div>
            <p className="text-xl font-bold text-niyam-text mt-1">{metrics?.pending_scrutiny ?? 0}</p>
            <p className="text-[11px] text-niyam-text-muted mt-1">Awaiting desk scrutiny validation</p>
          </Card>

          <Card className="bg-niyam-surface p-4">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-niyam-text-muted uppercase">Completed This Cycle</span>
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            </div>
            <p className="text-xl font-bold text-niyam-text mt-1">{metrics?.completed_this_cycle ?? 0}</p>
            <p className="text-[11px] text-niyam-text-muted mt-1">Full statutory lifecycle finalized</p>
          </Card>
        </div>
      )}

      {/* Chart Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card
          className="lg:col-span-2"
          title="Deterministic Stage Ageing Distribution"
          subtitle="Net active duration per application, excluding verified administrative hold time"
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
          subtitle="Items requiring immediate desk officer attention"
        >
          <div className="space-y-3 pt-2">
            {attentionItems.length === 0 ? (
              <div className="p-4 rounded border border-niyam-border bg-niyam-surface-alt text-center">
                <CheckCircle2 className="w-6 h-6 text-emerald-600 mx-auto mb-1" />
                <p className="text-xs font-semibold text-niyam-text">All SLAs On Track</p>
                <p className="text-[11px] text-niyam-text-muted mt-0.5">
                  No overdue or high-urgency items currently pending action.
                </p>
              </div>
            ) : (
              attentionItems.slice(0, 4).map((item) => (
                <div
                  key={item.id}
                  className={`p-3 rounded border ${
                    item.priority === 'critical'
                      ? 'border-rose-200 bg-rose-50/60'
                      : item.priority === 'high'
                      ? 'border-amber-200 bg-amber-50/60'
                      : 'border-niyam-border bg-niyam-surface-alt'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-niyam-text">
                      {item.application_number}
                    </span>
                    {getPriorityBadge(item.priority)}
                  </div>
                  <p className="text-xs text-niyam-text mt-1 font-medium truncate">
                    {item.institution_name}
                  </p>
                  <div className="flex items-center justify-between text-[11px] text-niyam-text-muted mt-1">
                    <span>Stage: {item.current_stage_name}</span>
                    <span className="font-semibold text-niyam-text">{item.reason}</span>
                  </div>
                  <div className="mt-2 text-right">
                    <Link
                      to={`/applications/${item.id}`}
                      className="text-[11px] font-semibold text-niyam-primary hover:underline inline-flex items-center gap-1"
                    >
                      Open Application <ArrowRight className="w-3 h-3" />
                    </Link>
                  </div>
                </div>
              ))
            )}

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
