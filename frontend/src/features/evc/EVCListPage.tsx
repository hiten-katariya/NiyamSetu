import React, { useState, useEffect, useCallback } from 'react';
import {
  Calendar,
  Users,
  FileCheck,
  RefreshCw,
  CheckCircle,
  FileText,
  UserPlus,
  Eye,
  AlertCircle,
  Download,
} from 'lucide-react';
import { api, downloadFile } from '../../lib/apiClient';
import { EVCItem } from '../../types';
import { useAuth } from '../../app/AuthContext';
import { Badge } from '../../components/Badge';
import { Button } from '../../components/Button';
import { Card } from '../../components/Card';
import { Input } from '../../components/Input';
import { LoadingState, ErrorState, EmptyState } from '../../components/States';

export const EVCListPage: React.FC = () => {
  const { user } = useAuth();
  const [evcs, setEvcs] = useState<EVCItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Selected EVC for detail view or modals
  const [selectedEvc, setSelectedEvc] = useState<EVCItem | null>(null);

  // Modals state
  const [isScheduleModalOpen, setIsScheduleModalOpen] = useState(false);
  const [isMemberModalOpen, setIsMemberModalOpen] = useState(false);
  const [isConductModalOpen, setIsConductModalOpen] = useState(false);
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [isReviewModalOpen, setIsReviewModalOpen] = useState(false);

  // Form states
  const [scheduledDate, setScheduledDate] = useState('');
  const [visitMode, setVisitMode] = useState<'physical' | 'hybrid' | 'virtual'>('physical');
  const [rescheduleReason, setRescheduleReason] = useState('');

  const [memberName, setMemberName] = useState('');
  const [memberRole, setMemberRole] = useState('chairman');
  const [memberDesignation, setMemberDesignation] = useState('');

  const [conductedDate, setConductedDate] = useState('');
  const [visitSummary, setVisitSummary] = useState('');

  const [reportNumber, setReportNumber] = useState('');
  const [recommendation, setRecommendation] = useState<'recommended' | 'recommended_with_conditions' | 'not_recommended'>('recommended');
  const [keyObservations, setKeyObservations] = useState('');
  const [reportFile, setReportFile] = useState<File | null>(null);

  const [reviewStatus, setReviewStatus] = useState<'accepted' | 'returned_for_correction'>('accepted');
  const [reviewNotes, setReviewNotes] = useState('');

  const [actionError, setActionError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchEvcs = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.get<EVCItem[]>('/evc');
      setEvcs(data);
      if (selectedEvc) {
        const updated = data.find((e) => e.id === selectedEvc.id);
        if (updated) setSelectedEvc(updated);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load EVC visits';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }, [selectedEvc]);

  useEffect(() => {
    fetchEvcs();
  }, []);

  const isOfficerOrAdmin =
    user?.role === 'scrutiny_officer' ||
    user?.role === 'regional_officer' ||
    user?.role === 'bureau_officer' ||
    user?.role === 'system_admin' ||
    user?.role === 'admin';

  const isCommitteeMember = user?.role === 'committee_member';

  // Metrics
  const queuedCount = evcs.filter((e) => e.status === 'queued').length;
  const scheduledCount = evcs.filter((e) => e.status === 'scheduled' || e.status === 'rescheduled').length;
  const conductedCount = evcs.filter((e) => e.status === 'conducted' || e.status === 'report_submitted').length;
  const completedCount = evcs.filter((e) => e.status === 'completed').length;

  // Filtered
  const filteredEvcs = evcs.filter((evc) => {
    if (statusFilter !== 'all' && evc.status !== statusFilter) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchApp = evc.application_number?.toLowerCase().includes(q);
      const matchInst = evc.institution_name?.toLowerCase().includes(q);
      if (!matchApp && !matchInst) return false;
    }
    return true;
  });

  const handleOpenScheduleModal = (evc: EVCItem) => {
    setSelectedEvc(evc);
    setScheduledDate(evc.scheduled_date || '');
    setVisitMode(evc.visit_mode || 'physical');
    setRescheduleReason('');
    setActionError(null);
    setIsScheduleModalOpen(true);
  };

  const handleScheduleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEvc) return;
    setIsSubmitting(true);
    setActionError(null);
    try {
      await api.post(`/evc/${selectedEvc.id}/schedule`, {
        scheduled_date: scheduledDate,
        visit_mode: visitMode,
        reschedule_reason: rescheduleReason.trim() ? rescheduleReason.trim() : undefined,
      });
      setIsScheduleModalOpen(false);
      await fetchEvcs();
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : 'Failed to schedule visit');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOpenMemberModal = (evc: EVCItem) => {
    setSelectedEvc(evc);
    setMemberName('');
    setMemberRole('member');
    setMemberDesignation('');
    setActionError(null);
    setIsMemberModalOpen(true);
  };

  const handleMemberSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEvc) return;
    setIsSubmitting(true);
    setActionError(null);
    try {
      await api.post(`/evc/${selectedEvc.id}/members`, {
        name: memberName,
        role_in_committee: memberRole,
        designation: memberDesignation.trim() ? memberDesignation.trim() : undefined,
      });
      setIsMemberModalOpen(false);
      await fetchEvcs();
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : 'Failed to assign committee member');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOpenConductModal = (evc: EVCItem) => {
    setSelectedEvc(evc);
    setConductedDate(new Date().toISOString().split('T')[0]);
    setVisitSummary('');
    setActionError(null);
    setIsConductModalOpen(true);
  };

  const handleConductSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEvc) return;
    setIsSubmitting(true);
    setActionError(null);
    try {
      await api.post(`/evc/${selectedEvc.id}/conduct`, {
        conducted_date: conductedDate,
        visit_summary: visitSummary.trim() ? visitSummary.trim() : undefined,
      });
      setIsConductModalOpen(false);
      await fetchEvcs();
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : 'Failed to record visit conduct');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOpenReportModal = (evc: EVCItem) => {
    setSelectedEvc(evc);
    setReportNumber(`EVC-REP-${Date.now().toString().slice(-6)}`);
    setRecommendation('recommended');
    setKeyObservations('');
    setReportFile(null);
    setActionError(null);
    setIsReportModalOpen(true);
  };

  const handleReportSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEvc) return;
    if (!reportFile) {
      setActionError('Inspection report document (PDF, PNG, JPEG) is mandatory');
      return;
    }
    setIsSubmitting(true);
    setActionError(null);
    try {
      const formData = new FormData();
      formData.append('report_number', reportNumber);
      formData.append('recommendation', recommendation);
      if (keyObservations.trim()) {
        formData.append('key_observations', keyObservations.trim());
      }
      formData.append('file', reportFile);

      await api.postForm(`/evc/${selectedEvc.id}/report`, formData);
      setIsReportModalOpen(false);
      await fetchEvcs();
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : 'Failed to submit report');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOpenReviewModal = (evc: EVCItem) => {
    setSelectedEvc(evc);
    setReviewStatus('accepted');
    setReviewNotes('');
    setActionError(null);
    setIsReviewModalOpen(true);
  };

  const handleReviewSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEvc || !selectedEvc.reports.length) return;
    const latestReport = selectedEvc.reports[selectedEvc.reports.length - 1];
    setIsSubmitting(true);
    setActionError(null);
    try {
      await api.post(`/evc/reports/${latestReport.id}/review`, {
        review_status: reviewStatus,
        review_notes: reviewNotes.trim() ? reviewNotes.trim() : undefined,
      });
      setIsReviewModalOpen(false);
      await fetchEvcs();
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : 'Failed to review EVC report');
    } finally {
      setIsSubmitting(false);
    }
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'conducted':
      case 'report_submitted':
        return 'info';
      case 'scheduled':
      case 'rescheduled':
        return 'warning';
      case 'queued':
        return 'neutral';
      case 'cancelled':
        return 'danger';
      default:
        return 'neutral';
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-niyam-border">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-niyam-text">
            Expert Visit Committee (EVC) Management
          </h2>
          <p className="text-sm text-niyam-text-muted mt-1">
            Schedule visits, assign committee experts, record physical/hybrid inspections, and review reports.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={fetchEvcs} disabled={isLoading}>
            <RefreshCw className={`w-4 h-4 mr-1 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-slate-100 text-niyam-text-muted flex items-center justify-center">
              <Calendar className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-niyam-text-muted font-medium">To Be Scheduled</p>
              <p className="text-xl font-bold text-niyam-text">{queuedCount} Queued</p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-blue-50 text-niyam-primary flex items-center justify-center">
              <Calendar className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-niyam-text-muted font-medium">Scheduled Visits</p>
              <p className="text-xl font-bold text-niyam-text">{scheduledCount} Active</p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-amber-50 text-niyam-status-warning flex items-center justify-center">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-niyam-text-muted font-medium">Conducted / Under Review</p>
              <p className="text-xl font-bold text-niyam-text">{conductedCount} Visits</p>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-emerald-50 text-niyam-status-success flex items-center justify-center">
              <FileCheck className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-niyam-text-muted font-medium">Closed / Completed</p>
              <p className="text-xl font-bold text-niyam-text">{completedCount} Completed</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Search & Filters */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between bg-niyam-surface p-3 rounded-lg border border-niyam-border">
        <div className="flex-1 w-full sm:max-w-xs">
          <Input
            placeholder="Search by application or institution..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full text-sm"
          />
        </div>
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <span className="text-xs text-niyam-text-muted font-medium">Status:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs border border-niyam-border rounded px-2.5 py-1.5 bg-white text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary"
          >
            <option value="all">All Statuses</option>
            <option value="queued">Queued</option>
            <option value="scheduled">Scheduled</option>
            <option value="rescheduled">Rescheduled</option>
            <option value="conducted">Conducted</option>
            <option value="report_submitted">Report Submitted</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
      </div>

      {/* Main List */}
      {isLoading ? (
        <LoadingState message="Loading EVC inspections..." />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchEvcs} />
      ) : filteredEvcs.length === 0 ? (
        <EmptyState
          title="No EVC visits found"
          description={
            searchQuery || statusFilter !== 'all'
              ? 'No EVC visits match your current filter criteria.'
              : 'There are no active or scheduled EVC visits currently assigned.'
          }
        />
      ) : (
        <div className="space-y-4">
          {filteredEvcs.map((evc) => {
            const isScheduled = !!evc.scheduled_date;
            const hasReports = evc.reports && evc.reports.length > 0;
            const latestReport = hasReports ? evc.reports[evc.reports.length - 1] : null;

            return (
              <Card key={evc.id} className="hover:border-niyam-border-focus transition-colors">
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                  <div className="space-y-1.5 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-semibold text-niyam-text text-base">
                        {evc.application_number || 'Application Reference'}
                      </span>
                      <Badge variant={getStatusBadgeVariant(evc.status)}>
                        {evc.status.replace(/_/g, ' ').toUpperCase()}
                      </Badge>
                      <Badge variant="neutral">Mode: {evc.visit_mode.toUpperCase()}</Badge>
                    </div>

                    <p className="text-sm text-niyam-text font-medium">
                      {evc.institution_name || 'Institution Name Unavailable'}
                    </p>

                    <div className="flex items-center gap-4 text-xs text-niyam-text-muted flex-wrap">
                      {evc.scheduled_date && (
                        <span>
                          <strong>Visit Date:</strong> {evc.scheduled_date}
                        </span>
                      )}
                      {evc.rescheduled_date && (
                        <span className="text-amber-700">
                          <strong>Rescheduled To:</strong> {evc.rescheduled_date}
                        </span>
                      )}
                      {evc.conducted_date && (
                        <span className="text-emerald-700">
                          <strong>Conducted:</strong> {evc.conducted_date}
                        </span>
                      )}
                      <span>
                        <strong>Committee Members:</strong> {evc.members?.length || 0} assigned
                      </span>
                    </div>

                    {evc.reschedule_reason && (
                      <p className="text-xs bg-amber-50 text-amber-800 p-2 rounded border border-amber-200 mt-1">
                        <strong>Reschedule Reason:</strong> {evc.reschedule_reason}
                      </p>
                    )}

                    {latestReport && (
                      <div className="text-xs bg-slate-50 p-2 rounded border border-niyam-border flex items-center justify-between gap-2 mt-1">
                        <div>
                          <strong>Report {latestReport.report_number}:</strong>{' '}
                          <span className="capitalize">{latestReport.recommendation.replace(/_/g, ' ')}</span> •{' '}
                          Review Status: <strong className="capitalize">{latestReport.review_status.replace(/_/g, ' ')}</strong>
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => downloadFile(`/files/${latestReport.file_id}/download`, `${latestReport.report_number}.pdf`)}
                        >
                          <Download className="w-3.5 h-3.5 mr-1" />
                          Download Report
                        </Button>
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 flex-wrap lg:self-center">
                    {/* Schedule / Reschedule (Officers & Admin) */}
                    {isOfficerOrAdmin && (
                      <Button
                        size="sm"
                        variant={isScheduled ? 'outline' : 'primary'}
                        onClick={() => handleOpenScheduleModal(evc)}
                      >
                        <Calendar className="w-3.5 h-3.5 mr-1" />
                        {isScheduled ? 'Reschedule' : 'Schedule Visit'}
                      </Button>
                    )}

                    {/* Assign Member (Officers & Admin) */}
                    {isOfficerOrAdmin && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleOpenMemberModal(evc)}
                      >
                        <UserPlus className="w-3.5 h-3.5 mr-1" />
                        Assign Expert
                      </Button>
                    )}

                    {/* Mark Conducted (Officers / Committee) */}
                    {(isOfficerOrAdmin || isCommitteeMember) &&
                      (evc.status === 'scheduled' || evc.status === 'rescheduled') && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleOpenConductModal(evc)}
                        >
                          <CheckCircle className="w-3.5 h-3.5 mr-1" />
                          Mark Conducted
                        </Button>
                      )}

                    {/* Upload Report (Officers / Committee Member) */}
                    {(isOfficerOrAdmin || isCommitteeMember) &&
                      (evc.status === 'conducted' || evc.status === 'scheduled' || evc.status === 'rescheduled') && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleOpenReportModal(evc)}
                        >
                          <FileText className="w-3.5 h-3.5 mr-1" />
                          Submit Report
                        </Button>
                      )}

                    {/* Review Report (Officers / Admin only - Dual Control) */}
                    {isOfficerOrAdmin && latestReport && latestReport.review_status === 'pending_review' && (
                      <Button
                        size="sm"
                        variant="primary"
                        onClick={() => handleOpenReviewModal(evc)}
                      >
                        <FileCheck className="w-3.5 h-3.5 mr-1" />
                        Review Report
                      </Button>
                    )}

                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setSelectedEvc(selectedEvc?.id === evc.id ? null : evc)}
                    >
                      <Eye className="w-3.5 h-3.5 mr-1" />
                      {selectedEvc?.id === evc.id ? 'Hide Details' : 'Details'}
                    </Button>
                  </div>
                </div>

                {/* Expandable Member and Report Details */}
                {selectedEvc?.id === evc.id && (
                  <div className="mt-4 pt-4 border-t border-niyam-border space-y-4">
                    <div>
                      <h4 className="text-xs font-semibold text-niyam-text uppercase tracking-wider mb-2">
                        Assigned Committee Experts
                      </h4>
                      {evc.members && evc.members.length > 0 ? (
                        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
                          {evc.members.map((member) => (
                            <div
                              key={member.id}
                              className="p-2.5 rounded bg-niyam-surface-alt border border-niyam-border text-xs"
                            >
                              <p className="font-semibold text-niyam-text">{member.name}</p>
                              <p className="text-niyam-text-muted capitalize">
                                Role: {member.role_in_committee.replace(/_/g, ' ')}
                              </p>
                              {member.designation && (
                                <p className="text-niyam-text-muted text-[11px]">{member.designation}</p>
                              )}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-xs text-niyam-text-muted italic">
                          No committee members assigned yet.
                        </p>
                      )}
                    </div>

                    {evc.reports && evc.reports.length > 0 && (
                      <div>
                        <h4 className="text-xs font-semibold text-niyam-text uppercase tracking-wider mb-2">
                          Inspection Reports & Findings
                        </h4>
                        <div className="space-y-2">
                          {evc.reports.map((rep) => (
                            <div
                              key={rep.id}
                              className="p-3 rounded bg-niyam-surface-alt border border-niyam-border text-xs space-y-1.5"
                            >
                              <div className="flex items-center justify-between">
                                <span className="font-semibold text-niyam-text">
                                  Report No: {rep.report_number}
                                </span>
                                <Badge
                                  variant={
                                    rep.review_status === 'accepted'
                                      ? 'success'
                                      : rep.review_status === 'returned_for_correction'
                                      ? 'danger'
                                      : 'warning'
                                  }
                                >
                                  {rep.review_status.replace(/_/g, ' ').toUpperCase()}
                                </Badge>
                              </div>
                              <p className="text-niyam-text">
                                <strong>Recommendation:</strong>{' '}
                                <span className="capitalize">{rep.recommendation.replace(/_/g, ' ')}</span>
                              </p>
                              {rep.key_observations && (
                                <p className="text-niyam-text-muted">
                                  <strong>Observations:</strong> {rep.key_observations}
                                </p>
                              )}
                              {rep.review_notes && (
                                <p className="text-amber-800 bg-amber-50 p-2 rounded border border-amber-200">
                                  <strong>Officer Review Notes:</strong> {rep.review_notes}
                                </p>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}

      {/* MODAL 1: Schedule / Reschedule Visit */}
      {isScheduleModalOpen && selectedEvc && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6 space-y-4 border border-niyam-border">
            <h3 className="text-lg font-bold text-niyam-text">
              {selectedEvc.scheduled_date ? 'Reschedule EVC Visit' : 'Schedule EVC Visit'}
            </h3>
            <p className="text-xs text-niyam-text-muted">
              Select inspection date and mode for {selectedEvc.application_number}.
            </p>

            {actionError && (
              <div className="p-3 rounded bg-red-50 text-red-700 text-xs flex items-center gap-2 border border-red-200">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{actionError}</span>
              </div>
            )}

            <form onSubmit={handleScheduleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-niyam-text mb-1">
                  Inspection Date *
                </label>
                <input
                  type="date"
                  required
                  value={scheduledDate}
                  onChange={(e) => setScheduledDate(e.target.value)}
                  className="w-full text-xs border border-niyam-border rounded px-3 py-2 bg-white text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-niyam-text mb-1">
                  Visit Mode *
                </label>
                <select
                  value={visitMode}
                  onChange={(e) => setVisitMode(e.target.value as 'physical' | 'hybrid' | 'virtual')}
                  className="w-full text-xs border border-niyam-border rounded px-3 py-2 bg-white text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary"
                >
                  <option value="physical">Physical On-Site Visit</option>
                  <option value="hybrid">Hybrid Verification</option>
                  <option value="virtual">Virtual Verification</option>
                </select>
              </div>

              {selectedEvc.scheduled_date && (
                <div>
                  <label className="block text-xs font-medium text-niyam-text mb-1">
                    Mandatory Reschedule Reason *
                  </label>
                  <textarea
                    required
                    rows={3}
                    placeholder="Provide statutory or logistical justification for rescheduling..."
                    value={rescheduleReason}
                    onChange={(e) => setRescheduleReason(e.target.value)}
                    className="w-full text-xs border border-niyam-border rounded p-2 bg-white text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary"
                  />
                </div>
              )}

              <div className="flex justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setIsScheduleModalOpen(false)}
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
                <Button type="submit" size="sm" variant="primary" disabled={isSubmitting}>
                  {isSubmitting ? 'Saving...' : 'Confirm Date'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: Assign Committee Expert */}
      {isMemberModalOpen && selectedEvc && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6 space-y-4 border border-niyam-border">
            <h3 className="text-lg font-bold text-niyam-text">Assign Committee Expert</h3>
            <p className="text-xs text-niyam-text-muted">
              Add verified expert evaluator to the inspection team.
            </p>

            {actionError && (
              <div className="p-3 rounded bg-red-50 text-red-700 text-xs flex items-center gap-2 border border-red-200">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{actionError}</span>
              </div>
            )}

            <form onSubmit={handleMemberSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-niyam-text mb-1">
                  Expert Full Name *
                </label>
                <Input
                  required
                  placeholder="Prof. / Dr. / Er. Name"
                  value={memberName}
                  onChange={(e) => setMemberName(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-niyam-text mb-1">
                  Role in Committee *
                </label>
                <select
                  value={memberRole}
                  onChange={(e) => setMemberRole(e.target.value)}
                  className="w-full text-xs border border-niyam-border rounded px-3 py-2 bg-white text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary"
                >
                  <option value="chairman">Chairman</option>
                  <option value="member">Expert Member</option>
                  <option value="convener">Convener</option>
                  <option value="architect_expert">Architect Expert</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-niyam-text mb-1">
                  Designation & Affiliation
                </label>
                <Input
                  placeholder="e.g. Professor, Dept. of CS, IIT Delhi"
                  value={memberDesignation}
                  onChange={(e) => setMemberDesignation(e.target.value)}
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setIsMemberModalOpen(false)}
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
                <Button type="submit" size="sm" variant="primary" disabled={isSubmitting}>
                  {isSubmitting ? 'Assigning...' : 'Assign Expert'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 3: Mark Visit Conducted */}
      {isConductModalOpen && selectedEvc && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6 space-y-4 border border-niyam-border">
            <h3 className="text-lg font-bold text-niyam-text">Record Visit Conduct</h3>
            <p className="text-xs text-niyam-text-muted">
              Confirm that the physical or hybrid inspection visit has been executed.
            </p>

            {actionError && (
              <div className="p-3 rounded bg-red-50 text-red-700 text-xs flex items-center gap-2 border border-red-200">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{actionError}</span>
              </div>
            )}

            <form onSubmit={handleConductSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-niyam-text mb-1">
                  Date Conducted *
                </label>
                <input
                  type="date"
                  required
                  value={conductedDate}
                  onChange={(e) => setConductedDate(e.target.value)}
                  className="w-full text-xs border border-niyam-border rounded px-3 py-2 bg-white text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-niyam-text mb-1">
                  Visit Summary & Protocol Remarks
                </label>
                <textarea
                  rows={3}
                  placeholder="Brief notes on proceedings, presence of institutional leadership, etc."
                  value={visitSummary}
                  onChange={(e) => setVisitSummary(e.target.value)}
                  className="w-full text-xs border border-niyam-border rounded p-2 bg-white text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setIsConductModalOpen(false)}
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
                <Button type="submit" size="sm" variant="primary" disabled={isSubmitting}>
                  {isSubmitting ? 'Recording...' : 'Confirm Conducted'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 4: Submit EVC Report */}
      {isReportModalOpen && selectedEvc && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6 space-y-4 border border-niyam-border">
            <h3 className="text-lg font-bold text-niyam-text">Submit EVC Inspection Report</h3>
            <p className="text-xs text-niyam-text-muted">
              Upload signed evaluation report and submit committee recommendation.
            </p>

            {actionError && (
              <div className="p-3 rounded bg-red-50 text-red-700 text-xs flex items-center gap-2 border border-red-200">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{actionError}</span>
              </div>
            )}

            <form onSubmit={handleReportSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-niyam-text mb-1">
                  Report Reference Number *
                </label>
                <Input
                  required
                  value={reportNumber}
                  onChange={(e) => setReportNumber(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-niyam-text mb-1">
                  Recommendation *
                </label>
                <select
                  value={recommendation}
                  onChange={(e) =>
                    setRecommendation(
                      e.target.value as 'recommended' | 'recommended_with_conditions' | 'not_recommended'
                    )
                  }
                  className="w-full text-xs border border-niyam-border rounded px-3 py-2 bg-white text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary"
                >
                  <option value="recommended">Recommended (Full Compliance)</option>
                  <option value="recommended_with_conditions">
                    Recommended With Conditions Precedent
                  </option>
                  <option value="not_recommended">Not Recommended (Critical Deficiencies)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-niyam-text mb-1">
                  Key Observations & Findings
                </label>
                <textarea
                  rows={3}
                  placeholder="Summarise major physical observations, lab facilities, faculty presence..."
                  value={keyObservations}
                  onChange={(e) => setKeyObservations(e.target.value)}
                  className="w-full text-xs border border-niyam-border rounded p-2 bg-white text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-niyam-text mb-1">
                  Signed Report Document (PDF, PNG, JPEG &le; 10MB) *
                </label>
                <input
                  type="file"
                  required
                  accept=".pdf,.png,.jpg,.jpeg"
                  onChange={(e) => setReportFile(e.target.files?.[0] || null)}
                  className="w-full text-xs border border-niyam-border rounded p-1.5 bg-white text-niyam-text file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:bg-slate-100 file:text-niyam-text"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setIsReportModalOpen(false)}
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
                <Button type="submit" size="sm" variant="primary" disabled={isSubmitting}>
                  {isSubmitting ? 'Submitting...' : 'Upload & Submit'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 5: Review EVC Report */}
      {isReviewModalOpen && selectedEvc && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6 space-y-4 border border-niyam-border">
            <h3 className="text-lg font-bold text-niyam-text">Review EVC Report (Dual-Control)</h3>
            <p className="text-xs text-niyam-text-muted">
              Scrutiny or Regional Officer sign-off on the submitted committee report.
            </p>

            {actionError && (
              <div className="p-3 rounded bg-red-50 text-red-700 text-xs flex items-center gap-2 border border-red-200">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{actionError}</span>
              </div>
            )}

            <form onSubmit={handleReviewSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-niyam-text mb-1">
                  Review Determination *
                </label>
                <select
                  value={reviewStatus}
                  onChange={(e) =>
                    setReviewStatus(e.target.value as 'accepted' | 'returned_for_correction')
                  }
                  className="w-full text-xs border border-niyam-border rounded px-3 py-2 bg-white text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary"
                >
                  <option value="accepted">Accept Report & Conclude EVC</option>
                  <option value="returned_for_correction">
                    Return for Correction / Clarification
                  </option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-niyam-text mb-1">
                  Mandatory Review Notes / Remarks *
                </label>
                <textarea
                  required
                  rows={3}
                  placeholder="Record verification notes, clarification requests, or confirmation of compliance..."
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  className="w-full text-xs border border-niyam-border rounded p-2 bg-white text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setIsReviewModalOpen(false)}
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
                <Button type="submit" size="sm" variant="primary" disabled={isSubmitting}>
                  {isSubmitting ? 'Submitting...' : 'Confirm Determination'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
