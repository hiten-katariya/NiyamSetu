import React, { useEffect, useState, useCallback } from 'react';
import {
  BarChart,
  Bar,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  CartesianGrid,
} from 'recharts';
import {
  FileText,
  Clock,
  CalendarCheck,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Filter,
  RefreshCw,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { Badge } from '../../components/Badge';
import { Button } from '../../components/Button';
import { Card } from '../../components/Card';
import { AeroShards } from '../../components/AeroShards';
import { api } from '../../lib/apiClient';
import { useAuth } from '../../app/AuthContext';
import {
  AgeingMetric,
  AttentionItem,
  DashboardMetrics,
  DocumentAnalyticsResponse,
  EVCAnalyticsResponse,
  OperationalSummaryResponse,
  PendencyMetrics,
  RegionalMetricItem,
  RouteType,
  VolumeTrendPoint,
} from '../../types';

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [ageingData, setAgeingData] = useState<AgeingMetric[]>([]);
  const [pendency, setPendency] = useState<PendencyMetrics | null>(null);
  const [attentionItems, setAttentionItems] = useState<AttentionItem[]>([]);
  const [volumeTrends, setVolumeTrends] = useState<VolumeTrendPoint[]>([]);
  const [regionalMetrics, setRegionalMetrics] = useState<RegionalMetricItem[]>([]);
  const [evcAnalytics, setEvcAnalytics] = useState<EVCAnalyticsResponse | null>(null);
  const [undertakingAnalytics, setUndertakingAnalytics] = useState<any | null>(null);
  const [documentAnalytics, setDocumentAnalytics] = useState<DocumentAnalyticsResponse | null>(null);
  const [operationalSummary, setOperationalSummary] = useState<OperationalSummaryResponse | null>(null);
  const [routeTypes, setRouteTypes] = useState<RouteType[]>([]);

  // Filters
  const [daysWindow, setDaysWindow] = useState<number>(30);
  const [selectedRoute, setSelectedRoute] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);

  const canViewRegional = user?.role !== 'institution_user';

  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const queryParams = new URLSearchParams();
      if (selectedRoute) queryParams.set('route_type_id', selectedRoute);
      if (selectedStatus) queryParams.set('status', selectedStatus);

      const qStr = queryParams.toString() ? `?${queryParams.toString()}` : '';

      const promises: Promise<any>[] = [
        api.get<DashboardMetrics>(`/dashboard/summary${qStr}`),
        api.get<AgeingMetric[]>(`/dashboard/ageing${qStr}`),
        api.get<PendencyMetrics>(`/dashboard/pendency${qStr}`),
        api.get<AttentionItem[]>(`/dashboard/attention`),
        api.get<VolumeTrendPoint[]>(`/dashboard/volume-trends?days=${daysWindow}`),
        api.get<EVCAnalyticsResponse>('/dashboard/evc-analytics'),
        api.get<any>('/dashboard/undertaking-analytics'),
        api.get<DocumentAnalyticsResponse>('/dashboard/document-analytics'),
        api.get<OperationalSummaryResponse>('/dashboard/operational-summary'),
      ];

      if (canViewRegional) {
        promises.push(api.get<RegionalMetricItem[]>('/dashboard/regional-comparison'));
      }

      const results = await Promise.allSettled(promises);

      if (results[0].status === 'fulfilled') setMetrics(results[0].value);
      if (results[1].status === 'fulfilled') setAgeingData(results[1].value);
      if (results[2].status === 'fulfilled') setPendency(results[2].value);
      if (results[3].status === 'fulfilled') setAttentionItems(results[3].value);
      if (results[4].status === 'fulfilled') setVolumeTrends(results[4].value);
      if (results[5].status === 'fulfilled') setEvcAnalytics(results[5].value);
      if (results[6].status === 'fulfilled') setUndertakingAnalytics(results[6].value);
      if (results[7].status === 'fulfilled') setDocumentAnalytics(results[7].value);
      if (results[8].status === 'fulfilled') setOperationalSummary(results[8].value);
      if (canViewRegional && results[9]?.status === 'fulfilled') {
        setRegionalMetrics(results[9].value);
      }
    } catch (err) {
      console.error('Failed to load dashboard metrics', err);
    } finally {
      setIsLoading(false);
    }
  }, [daysWindow, selectedRoute, selectedStatus, canViewRegional]);

  useEffect(() => {
    loadData();
    // Load route types once
    api.get<RouteType[]>('/admin/route-types').then(setRouteTypes).catch(() => {});
  }, [loadData]);

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
      {/* Top Banner with AeroShards 3D Background */}
      <div className="relative w-full rounded-2xl overflow-hidden border border-purple-200/80 shadow-md bg-gradient-to-r from-slate-950 via-purple-950 to-slate-900 text-white p-6 sm:p-8 min-h-[200px] flex flex-col justify-between">
        <div className="absolute inset-0 z-0 opacity-75 pointer-events-auto">
          <AeroShards
            shardColor="#896ABD"
            accentColor="#A855F7"
            placement="full"
            material="glass"
            markers="plus"
            count={1300}
            depthOfField={0.75}
            vignette={0.3}
            mouseInteraction
            pulseOnClick
            holdToGather
          />
        </div>
        <div className="relative z-10 max-w-3xl pointer-events-none">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 backdrop-blur-md border border-white/20 text-xs font-semibold text-purple-200 mb-3">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>AICTE Institutional Command &bull; Active Portal Session</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
            Workflow Analytics &amp; Operational Command
          </h2>
          <p className="mt-2 text-xs sm:text-sm text-purple-100/90 leading-relaxed font-normal">
            Welcome, <span className="font-bold text-white">{user?.full_name || user?.email}</span> ({user?.role?.replace('_', ' ').toUpperCase()}). Real-time stage SLA monitoring, volume trend forecasting, compliance health, and background worker status.
          </p>
        </div>
        <div className="relative z-10 flex flex-wrap items-center justify-between gap-3 pt-4 border-t border-white/10 mt-4">
          <div className="flex items-center gap-2">
            {operationalSummary && (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/15 backdrop-blur-md border border-white/20 text-xs font-semibold text-white">
                <span className={`w-2 h-2 rounded-full ${
                  operationalSummary.worker_status === 'operational' ? 'bg-emerald-400' : 'bg-amber-400'
                }`} />
                Worker: {operationalSummary.worker_status.toUpperCase()}
              </span>
            )}
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-purple-500/20 backdrop-blur-md border border-purple-300/30 text-xs text-purple-200 font-medium hidden sm:inline-flex">
              3D Glass Shards Reactive
            </span>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={loadData}
            disabled={isLoading}
            className="bg-white/15 hover:bg-white/25 text-white border-white/30 backdrop-blur-md shadow-xs"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${isLoading ? 'animate-spin' : ''}`} />
            Sync Dashboard
          </Button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between bg-niyam-surface p-3 rounded-lg border border-niyam-border">
        <div className="flex items-center gap-2 flex-wrap w-full sm:w-auto">
          <Filter className="w-4 h-4 text-niyam-text-muted shrink-0" />
          <span className="text-xs text-niyam-text-muted font-medium">Reporting Range:</span>
          <select
            value={daysWindow}
            onChange={(e) => setDaysWindow(Number(e.target.value))}
            className="text-xs border border-niyam-border rounded px-2.5 py-1.5 bg-white text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary"
          >
            <option value={7}>Last 7 Days</option>
            <option value={30}>Last 30 Days</option>
            <option value={60}>Last 60 Days</option>
            <option value={90}>Last 90 Days</option>
          </select>

          {routeTypes.length > 0 && (
            <select
              value={selectedRoute}
              onChange={(e) => setSelectedRoute(e.target.value)}
              className="text-xs border border-niyam-border rounded px-2.5 py-1.5 bg-white text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary"
            >
              <option value="">All Approval Routes</option>
              {routeTypes.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.name}
                </option>
              ))}
            </select>
          )}

          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="text-xs border border-niyam-border rounded px-2.5 py-1.5 bg-white text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary"
          >
            <option value="">All Statuses</option>
            <option value="in_progress">In Progress</option>
            <option value="submitted">Submitted</option>
            <option value="returned">Returned</option>
            <option value="on_hold">On Hold</option>
            <option value="completed">Completed</option>
          </select>
        </div>

        <div className="text-xs text-niyam-text-muted">
          Showing real-time calculations from authorized database records
        </div>
      </div>

      {/* KPI Overview Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-l-4 border-l-blue-600">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-niyam-text-muted font-medium">Total Applications</p>
              <h3 className="text-2xl font-bold text-niyam-text mt-1">
                {metrics?.total_applications ?? 0}
              </h3>
            </div>
            <div className="w-10 h-10 rounded-full bg-blue-50 text-niyam-primary flex items-center justify-center">
              <FileText className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-center justify-between text-xs text-niyam-text-muted">
            <span>In-Progress: {metrics?.in_progress ?? 0}</span>
            <span className="text-emerald-700 font-medium">
              Completed: {metrics?.completed_this_cycle ?? 0}
            </span>
          </div>
        </Card>

        <Card className="border-l-4 border-l-amber-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-niyam-text-muted font-medium">Under Scrutiny / Review</p>
              <h3 className="text-2xl font-bold text-niyam-status-warning mt-1">
                {metrics?.pending_scrutiny ?? 0}
              </h3>
            </div>
            <div className="w-10 h-10 rounded-full bg-amber-50 text-niyam-status-warning flex items-center justify-center">
              <Clock className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-center justify-between text-xs text-niyam-text-muted">
            <span>Stage SLA active</span>
            <span className="text-amber-700 font-medium">Working-Day Calculation</span>
          </div>
        </Card>

        <Card className="border-l-4 border-l-indigo-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-niyam-text-muted font-medium">Active EVC Pipeline</p>
              <h3 className="text-2xl font-bold text-indigo-700 mt-1">
                {metrics?.pending_evc ?? 0}
              </h3>
            </div>
            <div className="w-10 h-10 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center">
              <CalendarCheck className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-center justify-between text-xs text-niyam-text-muted">
            <span>Scheduled & Conducted</span>
            <Link to="/evc" className="text-indigo-600 font-semibold hover:underline">
              View Queue &rarr;
            </Link>
          </div>
        </Card>

        <Card className="border-l-4 border-l-rose-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-niyam-text-muted font-medium">SLA Overdue Items</p>
              <h3 className="text-2xl font-bold text-niyam-status-danger mt-1">
                {metrics?.overdue_items ?? 0}
              </h3>
            </div>
            <div className="w-10 h-10 rounded-full bg-rose-50 text-niyam-status-danger flex items-center justify-center">
              <AlertTriangle className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-3 flex items-center justify-between text-xs text-niyam-text-muted">
            <span>Critical Interventions</span>
            <span className="text-rose-700 font-bold">Escalations Armed</span>
          </div>
        </Card>
      </div>

      {/* CHARTS ROW 1: Volume Trends & Regional Comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Application Volume Trends (AreaChart) */}
        <Card
          title="Application Volume Trends (Submitted vs. Completed)"
          subtitle={`Daily intake and conclusion trajectory over the past ${daysWindow} days`}
        >
          <div className="h-64 w-full pt-4">
            {volumeTrends.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={volumeTrends}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                  <XAxis
                    dataKey="date"
                    tick={{ fontSize: 10, fill: '#64748B' }}
                    tickFormatter={(val) => val.slice(5)}
                  />
                  <YAxis tick={{ fontSize: 10, fill: '#64748B' }} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#FFFFFF',
                      borderColor: '#CBD5E1',
                      fontSize: '12px',
                    }}
                  />
                  <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                  <Area
                    type="monotone"
                    dataKey="submitted"
                    name="Applications Submitted"
                    stroke="#2563EB"
                    fill="#3B82F6"
                    fillOpacity={0.2}
                    strokeWidth={2}
                  />
                  <Area
                    type="monotone"
                    dataKey="completed"
                    name="Applications Completed"
                    stroke="#059669"
                    fill="#10B981"
                    fillOpacity={0.2}
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-xs text-niyam-text-muted">
                No trend volume data recorded in this period.
              </div>
            )}
          </div>
        </Card>

        {/* Regional Performance Comparison (BarChart) - for authorized users */}
        {canViewRegional ? (
          <Card
            title="Regional Volume & Pendency Comparison"
            subtitle="Jurisdictional workload distribution and overdue pendency across regions"
          >
            <div className="h-64 w-full pt-4">
              {regionalMetrics.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={regionalMetrics}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                    <XAxis dataKey="region_name" tick={{ fontSize: 10, fill: '#64748B' }} />
                    <YAxis tick={{ fontSize: 10, fill: '#64748B' }} allowDecimals={false} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#FFFFFF',
                        borderColor: '#CBD5E1',
                        fontSize: '12px',
                      }}
                    />
                    <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                    <Bar
                      dataKey="in_progress"
                      name="In Progress"
                      fill="#3B82F6"
                      radius={[3, 3, 0, 0]}
                    />
                    <Bar
                      dataKey="overdue"
                      name="Overdue Breaches"
                      fill="#EF4444"
                      radius={[3, 3, 0, 0]}
                    />
                    <Bar
                      dataKey="completed"
                      name="Completed"
                      fill="#10B981"
                      radius={[3, 3, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-full text-xs text-niyam-text-muted">
                  No regional comparative metrics available.
                </div>
              )}
            </div>
          </Card>
        ) : (
          <Card
            title="Stage Pendency Breakdown"
            subtitle="Application distribution across workflow stages"
          >
            <div className="h-64 w-full pt-4">
              {pendency && Object.keys(pendency.by_stage).length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={Object.entries(pendency.by_stage).map(([stage, count]) => ({
                      stage,
                      count,
                    }))}
                  >
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                    <XAxis dataKey="stage" tick={{ fontSize: 10, fill: '#64748B' }} />
                    <YAxis tick={{ fontSize: 10, fill: '#64748B' }} allowDecimals={false} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#FFFFFF',
                        borderColor: '#CBD5E1',
                        fontSize: '12px',
                      }}
                    />
                    <Bar dataKey="count" name="Applications" fill="#3B82F6" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-full text-xs text-niyam-text-muted">
                  No stage pendency records available.
                </div>
              )}
            </div>
          </Card>
        )}
      </div>

      {/* CHARTS ROW 2: Stage Ageing Analysis */}
      <Card
        title="Application Stage Ageing Distribution"
        subtitle="Distribution of time spent by applications in their current processing stage"
      >
        <div className="h-64 w-full pt-4">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={ageingData}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
              <XAxis dataKey="stage_name" tick={{ fontSize: 11, fill: '#64748B' }} />
              <YAxis tick={{ fontSize: 11, fill: '#64748B' }} allowDecimals={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#FFFFFF',
                  borderColor: '#CBD5E1',
                  fontSize: '12px',
                }}
              />
              <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '8px' }} />
              <Bar dataKey="under_7_days" name="< 7 Days (Normal)" fill="#10B981" radius={[3, 3, 0, 0]} />
              <Bar dataKey="between_7_14_days" name="7–14 Days (Approaching)" fill="#F59E0B" radius={[3, 3, 0, 0]} />
              <Bar dataKey="over_14_days" name="> 14 Days (Critical)" fill="#EF4444" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>

      {/* DOMAIN HEALTH CARDS: EVC, Undertakings, Documents */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* EVC Inspection Health */}
        <Card title="EVC Inspections Health">
          <div className="space-y-3 pt-2">
            <div className="flex items-center justify-between p-2.5 rounded bg-slate-50 border border-niyam-border text-xs">
              <span className="text-niyam-text font-medium">Scheduled Visits</span>
              <Badge variant="warning">{evcAnalytics?.scheduled_count ?? 0} Active</Badge>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded bg-slate-50 border border-niyam-border text-xs">
              <span className="text-niyam-text font-medium">Conducted Inspections</span>
              <Badge variant="info">{evcAnalytics?.conducted_count ?? 0} Recorded</Badge>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded bg-slate-50 border border-niyam-border text-xs">
              <span className="text-niyam-text font-medium">Reports Pending Review</span>
              <Badge variant="danger">{evcAnalytics?.pending_reports ?? 0} Pending</Badge>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded bg-slate-50 border border-niyam-border text-xs">
              <span className="text-niyam-text font-medium">Completed Determinations</span>
              <Badge variant="success">{evcAnalytics?.reviewed_reports ?? 0} Closed</Badge>
            </div>
            <div className="pt-2">
              <Link to="/evc" className="text-xs text-niyam-primary font-semibold hover:underline flex items-center">
                Manage EVC Inspections &rarr;
              </Link>
            </div>
          </div>
        </Card>

        {/* Undertakings Compliance */}
        <Card title="Undertaking Conditions Health">
          <div className="space-y-3 pt-2">
            <div className="flex items-center justify-between p-2.5 rounded bg-slate-50 border border-niyam-border text-xs">
              <span className="text-niyam-text font-medium">Pending Evidence Upload</span>
              <Badge variant="warning">{undertakingAnalytics?.pending_evidence ?? 0} Due</Badge>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded bg-slate-50 border border-niyam-border text-xs">
              <span className="text-niyam-text font-medium">Submitted (Under Verification)</span>
              <Badge variant="info">{undertakingAnalytics?.submitted_under_review ?? 0} Review</Badge>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded bg-slate-50 border border-niyam-border text-xs">
              <span className="text-niyam-text font-medium">Verified & Fulfilled</span>
              <Badge variant="success">{undertakingAnalytics?.fulfilled ?? 0} Fulfilled</Badge>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded bg-slate-50 border border-niyam-border text-xs">
              <span className="text-niyam-text font-medium">Overdue Breaches</span>
              <Badge variant="danger">{undertakingAnalytics?.overdue ?? 0} Non-Compliant</Badge>
            </div>
            <div className="pt-2">
              <Link to="/compliance" className="text-xs text-niyam-primary font-semibold hover:underline flex items-center">
                Track Compliance Undertakings &rarr;
              </Link>
            </div>
          </div>
        </Card>

        {/* Document Validity */}
        <Card title="Document Validity & Leases">
          <div className="space-y-3 pt-2">
            <div className="flex items-center justify-between p-2.5 rounded bg-slate-50 border border-niyam-border text-xs">
              <span className="text-niyam-text font-medium">Valid & Verified Documents</span>
              <Badge variant="success">{documentAnalytics?.valid_count ?? 0} Compliant</Badge>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded bg-slate-50 border border-niyam-border text-xs">
              <span className="text-niyam-text font-medium">Expiring Soon (&le; 30 Days)</span>
              <Badge variant="warning">{documentAnalytics?.expiring_soon_count ?? 0} Notice</Badge>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded bg-slate-50 border border-niyam-border text-xs">
              <span className="text-niyam-text font-medium">Expired Certificates / Leases</span>
              <Badge variant="danger">{documentAnalytics?.expired_count ?? 0} Expired</Badge>
            </div>
            <div className="flex items-center justify-between p-2.5 rounded bg-slate-50 border border-niyam-border text-xs">
              <span className="text-niyam-text font-medium">Active Renewal Cycles</span>
              <Badge variant="neutral">{documentAnalytics?.renewals_in_progress ?? 0} In Progress</Badge>
            </div>
            <div className="pt-2">
              <Link to="/documents" className="text-xs text-niyam-primary font-semibold hover:underline flex items-center">
                View Documents Register &rarr;
              </Link>
            </div>
          </div>
        </Card>
      </div>

      {/* Action Items Requiring Attention */}
      <Card
        title="Items Requiring Immediate Attention"
        subtitle="Priority-ranked queue of SLA breaches, expiring deadlines, and clarification requests"
      >
        {attentionItems.length === 0 ? (
          <div className="text-center py-8 text-niyam-text-muted">
            <CheckCircle2 className="w-8 h-8 mx-auto mb-2 text-emerald-600" />
            <p className="font-medium text-sm">All operational SLAs are currently healthy.</p>
            <p className="text-xs text-niyam-text-muted mt-1">
              No applications or statutory compliance items breached their deadline windows.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-niyam-border text-sm">
            {attentionItems.map((item) => (
              <div
                key={item.id}
                className="py-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-niyam-text text-sm">
                      {item.application_number}
                    </span>
                    {getPriorityBadge(item.priority)}
                    <span className="text-xs text-niyam-text-muted">
                      ({item.days_in_stage} days in current stage)
                    </span>
                  </div>
                  <p className="text-xs text-niyam-text font-medium">
                    {item.institution_name} •{' '}
                    <span className="text-niyam-text-muted">{item.current_stage_name}</span>
                  </p>
                  <p className="text-xs text-niyam-text-muted">{item.reason}</p>
                </div>

                <div className="flex items-center gap-2 self-end sm:self-center">
                  <Link
                    to={`/applications/${item.id}`}
                    className="inline-flex items-center text-xs font-semibold text-niyam-primary hover:text-niyam-primary-hover border border-niyam-border rounded px-3 py-1.5 bg-white hover:bg-slate-50 transition-colors"
                  >
                    Action Application
                    <ArrowRight className="w-3.5 h-3.5 ml-1" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
};
