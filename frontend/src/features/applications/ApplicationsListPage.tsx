import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FileSpreadsheet,
  PlusCircle,
  Search,
  Filter,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  Shield,
  AlertCircle,
  ArrowRight,
  X,
} from 'lucide-react';
import { Badge } from '../../components/Badge';
import { Button } from '../../components/Button';
import { Card } from '../../components/Card';
import { api, ApiClientError } from '../../lib/apiClient';
import { ApplicationItem, PaginatedResponse, RouteType } from '../../types';
import { useAuth } from '../../app/AuthContext';

export const ApplicationsListPage: React.FC = () => {
  const navigate = useNavigate();
  const { user, hasRole } = useAuth();

  const [applications, setApplications] = useState<ApplicationItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [totalPages, setTotalPages] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Create Application Modal state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [routes, setRoutes] = useState<RouteType[]>([]);
  const [selectedRouteId, setSelectedRouteId] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const canCreate = hasRole(['institution_user', 'admin', 'system_admin']);

  const fetchApplications = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      params.set('page', page.toString());
      params.set('page_size', pageSize.toString());
      if (statusFilter !== 'all') {
        params.set('status', statusFilter);
      }
      if (searchQuery.trim()) {
        params.set('search', searchQuery.trim());
      }

      const res = await api.get<PaginatedResponse<ApplicationItem>>(`/applications?${params.toString()}`);
      setApplications(res.data);
      setTotal(res.meta.total);
      setTotalPages(res.meta.total_pages);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message);
      } else {
        setError('Failed to load applications. Verify backend service is running.');
      }
    } finally {
      setIsLoading(false);
    }
  }, [page, pageSize, statusFilter, searchQuery]);

  useEffect(() => {
    fetchApplications();
  }, [fetchApplications]);

  const loadRoutes = async () => {
    try {
      const res = await api.get<RouteType[]>('/workflow/routes');
      setRoutes(res);
      if (res.length > 0) {
        setSelectedRouteId(res[0].id);
      }
    } catch {
      // Best effort
    }
  };

  const handleOpenCreateModal = () => {
    setCreateError(null);
    loadRoutes();
    setIsCreateModalOpen(true);
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRouteId) {
      setCreateError('Please select a workflow route configuration.');
      return;
    }

    setIsSubmitting(true);
    setCreateError(null);
    try {
      const res = await api.post<ApplicationItem>('/applications', {
        route_type_id: selectedRouteId,
      });
      setIsCreateModalOpen(false);
      navigate(`/applications/${res.id}`);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setCreateError(err.message);
      } else {
        setCreateError('Failed to create application.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'in_progress':
        return <Badge variant="info">In Progress</Badge>;
      case 'returned':
        return <Badge variant="warning">Returned / Deficiency</Badge>;
      case 'on_hold':
        return <Badge variant="danger">On Hold</Badge>;
      case 'completed':
        return <Badge variant="success">Completed</Badge>;
      default:
        return <Badge variant="neutral">{status.replace(/_/g, ' ')}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-niyam-border">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl sm:text-2xl font-bold text-niyam-text">
              Approval Applications
            </h2>
            <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-amber-100 text-amber-800 border border-amber-200">
              Demonstration Environment
            </span>
          </div>
          <p className="text-sm text-niyam-text-muted mt-1">
            Track and process AICTE approval applications across configurable workflow routes and stages.
          </p>
        </div>

        {canCreate && (
          <Button
            variant="primary"
            onClick={handleOpenCreateModal}
            className="gap-1.5 shrink-0"
          >
            <PlusCircle className="w-4 h-4" />
            <span>New Application</span>
          </Button>
        )}
      </div>

      {/* Filters & Search Toolbar */}
      <div className="bg-niyam-surface p-4 rounded-lg border border-niyam-border flex flex-col md:flex-row items-center justify-between gap-3 shadow-xs">
        <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-niyam-text-muted mr-1">
            <Filter className="w-3.5 h-3.5" />
            <span>Filter:</span>
          </div>
          {['all', 'in_progress', 'returned', 'on_hold', 'completed'].map((st) => (
            <button
              key={st}
              onClick={() => {
                setStatusFilter(st);
                setPage(1);
              }}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                statusFilter === st
                  ? 'bg-niyam-primary text-white shadow-xs'
                  : 'bg-niyam-surface-alt border border-niyam-border text-niyam-text-muted hover:text-niyam-text'
              }`}
            >
              {st === 'all' ? 'All Applications' : st.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2 w-full md:w-72">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-niyam-text-muted absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search reference or institution..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setPage(1);
              }}
              className="w-full pl-9 pr-3 py-1.5 text-xs rounded-md bg-niyam-surface-alt border border-niyam-border text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary"
            />
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => fetchApplications()}
            disabled={isLoading}
            title="Refresh Applications"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>

      {/* Error alert */}
      {error && (
        <div className="p-3 rounded-md bg-red-50 border border-red-200 text-niyam-status-danger text-xs font-medium flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Applications Table Card */}
      <Card
        title="Application Records"
        subtitle={`Showing ${applications.length} of ${total} records under current institutional and regional scope`}
      >
        {isLoading && applications.length === 0 ? (
          <div className="text-center py-12 text-xs text-niyam-text-muted flex flex-col items-center gap-2">
            <div className="w-6 h-6 border-2 border-niyam-primary border-t-transparent rounded-full animate-spin" />
            <span>Loading applications from server...</span>
          </div>
        ) : applications.length === 0 ? (
          <div className="text-center py-12 text-xs text-niyam-text-muted">
            <FileSpreadsheet className="w-10 h-10 mx-auto text-niyam-text-muted/50 mb-2" />
            <p className="font-semibold text-niyam-text">No applications found</p>
            <p className="mt-1">
              {statusFilter !== 'all' || searchQuery
                ? 'Try adjusting your search criteria or filter status.'
                : 'No approval applications have been submitted under this jurisdiction.'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-niyam-surface-alt border-y border-niyam-border text-niyam-text-muted font-semibold">
                <tr>
                  <th className="py-2.5 px-3">Reference No.</th>
                  <th className="py-2.5 px-3">Institution</th>
                  <th className="py-2.5 px-3">Workflow Route</th>
                  <th className="py-2.5 px-3">Current Stage</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">Assigned Desk</th>
                  <th className="py-2.5 px-3">Submitted</th>
                  <th className="py-2.5 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-niyam-border">
                {applications.map((app) => (
                  <tr
                    key={app.id}
                    onClick={() => navigate(`/applications/${app.id}`)}
                    className="hover:bg-niyam-surface-alt/60 cursor-pointer transition-colors"
                  >
                    <td className="py-3 px-3">
                      <span className="font-semibold font-mono text-niyam-primary hover:underline">
                        {app.reference_no}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <p className="font-medium text-niyam-text">{app.institution_name || 'Assigned Institution'}</p>
                      {app.institution_code && (
                        <p className="text-[11px] text-niyam-text-muted font-mono">{app.institution_code}</p>
                      )}
                    </td>
                    <td className="py-3 px-3 text-niyam-text-muted">
                      <p className="text-niyam-text font-medium">{app.route_name || 'Standard Route'}</p>
                      <p className="text-[11px]">Pinned v{app.route_version}</p>
                    </td>
                    <td className="py-3 px-3">
                      <div className="flex items-center gap-1.5">
                        <span className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 font-mono text-[10px]">
                          {app.current_stage_sequence || 1}/{app.total_stages || 1}
                        </span>
                        <span className="font-medium text-niyam-text">
                          {app.current_stage_name || 'Under Review'}
                        </span>
                      </div>
                      {app.current_stage_role && (
                        <p className="text-[10px] text-niyam-text-muted mt-0.5">
                          Role: {app.current_stage_role.replace(/_/g, ' ')}
                        </p>
                      )}
                    </td>
                    <td className="py-3 px-3">{getStatusBadge(app.status)}</td>
                    <td className="py-3 px-3 text-niyam-text-muted">
                      {app.assigned_to_name ? (
                        <span className="font-medium text-niyam-text">{app.assigned_to_name}</span>
                      ) : (
                        <span className="italic text-niyam-text-muted/70">Unassigned Pool</span>
                      )}
                    </td>
                    <td className="py-3 px-3 text-niyam-text-muted whitespace-nowrap">
                      {app.submitted_at
                        ? new Date(app.submitted_at).toLocaleDateString(undefined, {
                            month: 'short',
                            day: 'numeric',
                            year: 'numeric',
                          })
                        : '—'}
                    </td>
                    <td className="py-3 px-3 text-right">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/applications/${app.id}`);
                        }}
                        className="text-xs gap-1"
                      >
                        <span>View</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between pt-4 border-t border-niyam-border mt-4 text-xs text-niyam-text-muted">
            <span>
              Page {page} of {totalPages}
            </span>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="gap-1"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
                <span>Previous</span>
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                className="gap-1"
              >
                <span>Next</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </Button>
            </div>
          </div>
        )}
      </Card>

      {/* Create Application Modal */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-niyam-surface rounded-lg border border-niyam-border max-w-lg w-full p-6 shadow-xl">
            <div className="flex items-center justify-between pb-3 border-b border-niyam-border mb-4">
              <div className="flex items-center gap-2">
                <FileSpreadsheet className="w-5 h-5 text-niyam-primary" />
                <h3 className="text-base font-bold text-niyam-text">
                  Initiate New Approval Application
                </h3>
              </div>
              <button
                onClick={() => setIsCreateModalOpen(false)}
                className="p-1 rounded text-niyam-text-muted hover:text-niyam-text"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {createError && (
              <div className="mb-4 p-2.5 rounded bg-red-50 border border-red-200 text-niyam-status-danger text-xs font-medium flex items-center gap-1.5">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{createError}</span>
              </div>
            )}

            <form onSubmit={handleCreateSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-niyam-text mb-1">
                  Applicant Institution
                </label>
                <div className="p-2.5 rounded bg-niyam-surface-alt border border-niyam-border text-xs text-niyam-text">
                  {user?.institution_id ? (
                    <span className="font-semibold text-niyam-primary">
                      Authenticated Institution ID: {user.institution_id}
                    </span>
                  ) : (
                    <span>Default Demonstration Institution</span>
                  )}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-niyam-text mb-1">
                  Select Workflow Route Configuration
                </label>
                <select
                  value={selectedRouteId}
                  onChange={(e) => setSelectedRouteId(e.target.value)}
                  className="w-full text-xs bg-niyam-surface border border-niyam-border rounded-md px-3 py-2 text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary"
                  required
                >
                  {routes.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.name} (v{r.current_version}) — {r.stages.length} configured stages
                    </option>
                  ))}
                </select>
                <p className="text-[11px] text-niyam-text-muted mt-1">
                  The application will permanently pin the chosen route version throughout its lifecycle.
                </p>
              </div>

              <div className="p-3 rounded bg-amber-50 border border-amber-200 text-[11px] text-amber-900 flex items-start gap-1.5">
                <Shield className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
                <span>
                  Statutory Note: Creating an application assigns the initial Document Scrutiny stage. Submissions are subject to authorized officer reviews and never auto-approved.
                </span>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-niyam-border">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setIsCreateModalOpen(false)}
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  isLoading={isSubmitting}
                >
                  Submit Application
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
