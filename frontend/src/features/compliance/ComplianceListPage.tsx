import React, { useState, useEffect, useCallback } from 'react';
import {
  ShieldCheck,
  Plus,
  RefreshCw,
  Upload,
  CheckCircle,
  Clock,
  AlertTriangle,
  Download,
  AlertCircle,
  Eye,
} from 'lucide-react';
import { api, downloadFile } from '../../lib/apiClient';
import { ApplicationItem, UndertakingItem } from '../../types';
import { useAuth } from '../../app/AuthContext';
import { Badge } from '../../components/Badge';
import { Button } from '../../components/Button';
import { Card } from '../../components/Card';
import { Input } from '../../components/Input';
import { LoadingState, ErrorState, EmptyState } from '../../components/States';

export const ComplianceListPage: React.FC = () => {
  const { user } = useAuth();
  const [undertakings, setUndertakings] = useState<UndertakingItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const [selectedUndertaking, setSelectedUndertaking] = useState<UndertakingItem | null>(null);

  // Modals
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isSubmitModalOpen, setIsSubmitModalOpen] = useState(false);
  const [isReviewModalOpen, setIsReviewModalOpen] = useState(false);

  // Form states
  const [conditionTitle, setConditionTitle] = useState('');
  const [conditionDescription, setConditionDescription] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [targetInstitutionId, setTargetInstitutionId] = useState('');
  const [targetApplicationId, setTargetApplicationId] = useState('');
  const [availableApps, setAvailableApps] = useState<ApplicationItem[]>([]);

  const [evidenceRemarks, setEvidenceRemarks] = useState('');
  const [evidenceFile, setEvidenceFile] = useState<File | null>(null);

  const [reviewDecision, setReviewDecision] = useState<'accepted' | 'rejected' | 'returned'>('accepted');
  const [reviewComments, setReviewComments] = useState('');

  const [actionError, setActionError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isOfficerOrAdmin =
    user?.role === 'scrutiny_officer' ||
    user?.role === 'regional_officer' ||
    user?.role === 'bureau_officer' ||
    user?.role === 'system_admin' ||
    user?.role === 'admin';

  const isInstitutionUser = user?.role === 'institution_user';

  const fetchUndertakings = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.get<UndertakingItem[]>('/undertakings');
      const safeData = Array.isArray(data) ? data : [];
      setUndertakings(safeData);
      if (selectedUndertaking) {
        const updated = safeData.find((u) => u.id === selectedUndertaking.id);
        if (updated) setSelectedUndertaking(updated);
      }
    } catch (err: unknown) {
      setUndertakings([]);
      const msg = err instanceof Error ? err.message : 'Failed to load undertakings';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }, [selectedUndertaking]);

  useEffect(() => {
    fetchUndertakings();
  }, []);

  // Metrics
  const safeUndertakings = Array.isArray(undertakings) ? undertakings : [];
  const pendingCount = safeUndertakings.filter((u) => u.status === 'pending').length;
  const submittedCount = safeUndertakings.filter((u) => u.status === 'submitted').length;
  const fulfilledCount = safeUndertakings.filter((u) => u.status === 'fulfilled').length;
  const overdueCount = safeUndertakings.filter((u) => u.status === 'overdue').length;

  const filteredUndertakings = safeUndertakings.filter((u) => {
    if (statusFilter !== 'all' && u.status !== statusFilter) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchTitle = (u.condition_title || '').toLowerCase().includes(q);
      const matchInst = u.institution_name?.toLowerCase().includes(q);
      if (!matchTitle && !matchInst) return false;
    }
    return true;
  });

  const handleOpenCreateModal = async () => {
    setConditionTitle('');
    setConditionDescription('');
    setDueDate('');
    setTargetApplicationId('');
    setTargetInstitutionId(user?.institution_id || '');
    setActionError(null);
    setIsCreateModalOpen(true);
    try {
      const res = await api.getPaginated<ApplicationItem>('/applications?page_size=100');
      const apps = Array.isArray(res?.data) ? res.data : [];
      setAvailableApps(apps);
      if (apps.length > 0) {
        setTargetApplicationId(apps[0].id);
        if (apps[0].institution_id) {
          setTargetInstitutionId(apps[0].institution_id);
        }
      }
    } catch {
      // Best effort; backend can still resolve if only 1 app exists
    }
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!conditionTitle.trim()) {
      setActionError('Condition Title is required.');
      return;
    }
    if (!dueDate) {
      setActionError('Compliance Due Date is required.');
      return;
    }
    setIsSubmitting(true);
    setActionError(null);
    try {
      const selectedApp = availableApps.find((a) => a.id === targetApplicationId);
      const chosenInstId = targetInstitutionId || selectedApp?.institution_id || undefined;
      await api.post('/undertakings', {
        application_id: targetApplicationId || undefined,
        title: conditionTitle.trim(),
        description: conditionDescription.trim() || conditionTitle.trim(),
        due_date: dueDate,
        assigned_institution_id: chosenInstId,
        // Dual-compatible aliases
        condition_title: conditionTitle.trim(),
        condition_description: conditionDescription.trim() || conditionTitle.trim(),
        institution_id: chosenInstId,
      });
      setIsCreateModalOpen(false);
      await fetchUndertakings();
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : 'Failed to create undertaking');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOpenSubmitModal = (u: UndertakingItem) => {
    setSelectedUndertaking(u);
    setEvidenceRemarks('');
    setEvidenceFile(null);
    setActionError(null);
    setIsSubmitModalOpen(true);
  };

  const handleSubmitEvidence = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUndertaking) return;
    setIsSubmitting(true);
    setActionError(null);
    try {
      const formData = new FormData();
      if (evidenceRemarks.trim()) {
        formData.append('remarks', evidenceRemarks.trim());
      }
      if (evidenceFile) {
        formData.append('file', evidenceFile);
      }
      await api.postForm(`/undertakings/${selectedUndertaking.id}/submit`, formData);
      setIsSubmitModalOpen(false);
      await fetchUndertakings();
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : 'Failed to submit compliance evidence');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOpenReviewModal = (u: UndertakingItem) => {
    setSelectedUndertaking(u);
    setReviewDecision('accepted');
    setReviewComments('');
    setActionError(null);
    setIsReviewModalOpen(true);
  };

  const handleReviewSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUndertaking || !selectedUndertaking.submissions.length) return;
    const latestSubmission = selectedUndertaking.submissions[selectedUndertaking.submissions.length - 1];
    setIsSubmitting(true);
    setActionError(null);
    try {
      await api.post(`/undertakings/submissions/${latestSubmission.id}/review`, {
        decision: reviewDecision,
        review_comments: reviewComments.trim() ? reviewComments.trim() : undefined,
      });
      setIsReviewModalOpen(false);
      await fetchUndertakings();
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : 'Failed to review undertaking submission');
    } finally {
      setIsSubmitting(false);
    }
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'fulfilled':
        return 'success';
      case 'submitted':
        return 'info';
      case 'overdue':
      case 'returned':
        return 'danger';
      case 'pending':
        return 'warning';
      default:
        return 'neutral';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-niyam-border">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-niyam-text">
            Time-Bound Undertakings & Compliance Conditions
          </h2>
          <p className="text-sm text-niyam-text-muted mt-1">
            Track statutory conditions precedent, evidence submissions, dual-control officer reviews, and compliance deadlines.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {isOfficerOrAdmin && (
            <Button size="sm" variant="primary" onClick={handleOpenCreateModal}>
              <Plus className="w-4 h-4 mr-1" />
              Issue Undertaking
            </Button>
          )}
          <Button variant="outline" size="sm" onClick={fetchUndertakings} disabled={isLoading}>
            <RefreshCw className={`w-4 h-4 mr-1 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="border-l-4 border-l-amber-500">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-amber-50 text-niyam-status-warning flex items-center justify-center">
              <Clock className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-niyam-text-muted font-medium">Pending Evidence</p>
              <p className="text-xl font-bold text-niyam-text">{pendingCount} Conditions</p>
            </div>
          </div>
        </Card>

        <Card className="border-l-4 border-l-blue-500">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-blue-50 text-niyam-primary flex items-center justify-center">
              <Upload className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-niyam-text-muted font-medium">Submitted (Under Review)</p>
              <p className="text-xl font-bold text-niyam-text">{submittedCount} Submissions</p>
            </div>
          </div>
        </Card>

        <Card className="border-l-4 border-l-emerald-500">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-emerald-50 text-niyam-status-success flex items-center justify-center">
              <CheckCircle className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-niyam-text-muted font-medium">Fulfilled & Verified</p>
              <p className="text-xl font-bold text-niyam-text">{fulfilledCount} Conditions</p>
            </div>
          </div>
        </Card>

        <Card className="border-l-4 border-l-rose-500">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-rose-50 text-niyam-status-danger flex items-center justify-center">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-niyam-text-muted font-medium">Overdue / Non-Compliant</p>
              <p className="text-xl font-bold text-rose-700">{overdueCount} Critical</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Guidelines Notice */}
      <div className="flex items-start gap-3 p-3 rounded-lg bg-blue-50/60 border border-blue-200">
        <ShieldCheck className="w-5 h-5 text-niyam-primary shrink-0 mt-0.5" />
        <div className="text-xs text-niyam-text space-y-0.5">
          <p className="font-semibold text-niyam-primary">Strict Dual-Control Verification</p>
          <p className="text-niyam-text-muted">
            Institutional users upload compliance evidence. Only authorized scrutiny or regional officers may verify, accept, or return submissions. Institutions cannot verify their own submissions.
          </p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between bg-niyam-surface p-3 rounded-lg border border-niyam-border">
        <div className="flex-1 w-full sm:max-w-xs">
          <Input
            placeholder="Search by condition title or institution..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full text-sm"
          />
        </div>
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <span className="text-xs text-niyam-text-muted font-medium">Filter:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs border border-niyam-border rounded px-2.5 py-1.5 bg-white text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary"
          >
            <option value="all">All Conditions</option>
            <option value="pending">Pending</option>
            <option value="submitted">Submitted</option>
            <option value="fulfilled">Fulfilled</option>
            <option value="overdue">Overdue</option>
            <option value="returned">Returned</option>
          </select>
        </div>
      </div>

      {/* Main List */}
      {isLoading ? (
        <LoadingState message="Loading compliance undertakings..." />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchUndertakings} />
      ) : filteredUndertakings.length === 0 ? (
        <EmptyState
          title="No undertakings found"
          description={
            searchQuery || statusFilter !== 'all'
              ? 'No undertakings match your current search and filter settings.'
              : 'There are currently no active time-bound compliance undertakings.'
          }
        />
      ) : (
        <div className="space-y-4">
          {filteredUndertakings.map((u) => {
            const hasSubmissions = u.submissions && u.submissions.length > 0;
            const latestSub = hasSubmissions ? u.submissions[u.submissions.length - 1] : null;

            return (
              <Card key={u.id} className="hover:border-niyam-border-focus transition-colors">
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                  <div className="space-y-1.5 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-semibold text-niyam-text text-base">
                        {u.condition_title}
                      </span>
                      <Badge variant={getStatusBadgeVariant(u.status)}>
                        {u.status.toUpperCase()}
                      </Badge>
                      {u.application_number && (
                        <Badge variant="neutral">App: {u.application_number}</Badge>
                      )}
                    </div>

                    <p className="text-sm text-niyam-text font-medium">
                      {u.institution_name || 'Institution Name Unavailable'}
                    </p>

                    {u.condition_description && (
                      <p className="text-xs text-niyam-text-muted">
                        {u.condition_description}
                      </p>
                    )}

                    <div className="flex items-center gap-4 text-xs text-niyam-text-muted flex-wrap">
                      <span>
                        <strong>Due Date:</strong>{' '}
                        <span className={u.status === 'overdue' ? 'text-rose-700 font-semibold' : ''}>
                          {u.due_date}
                        </span>
                      </span>
                      {u.fulfilled_date && (
                        <span className="text-emerald-700">
                          <strong>Fulfilled On:</strong> {u.fulfilled_date}
                        </span>
                      )}
                      <span>
                        <strong>Submissions:</strong> {u.submissions?.length || 0}
                      </span>
                    </div>

                    {latestSub && (
                      <div className="text-xs bg-slate-50 p-2 rounded border border-niyam-border flex items-center justify-between gap-2 mt-1">
                        <div>
                          <strong>Latest Submission ({latestSub.status.toUpperCase()}):</strong>{' '}
                          {latestSub.remarks || 'No remarks provided'}
                        </div>
                        {latestSub.file_id && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => downloadFile(`/files/${latestSub.file_id}/download`, 'compliance_evidence.pdf')}
                          >
                            <Download className="w-3.5 h-3.5 mr-1" />
                            Evidence Doc
                          </Button>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 flex-wrap lg:self-center">
                    {/* Submit Evidence (Institution Users or Admin) */}
                    {(isInstitutionUser || isOfficerOrAdmin) &&
                      (u.status === 'pending' || u.status === 'overdue' || u.status === 'returned') && (
                        <Button
                          size="sm"
                          variant="primary"
                          onClick={() => handleOpenSubmitModal(u)}
                        >
                          <Upload className="w-3.5 h-3.5 mr-1" />
                          Submit Evidence
                        </Button>
                      )}

                    {/* Review Evidence (Officers only - Dual Control) */}
                    {isOfficerOrAdmin && latestSub && latestSub.status === 'submitted' && (
                      <Button
                        size="sm"
                        variant="primary"
                        onClick={() => handleOpenReviewModal(u)}
                      >
                        <ShieldCheck className="w-3.5 h-3.5 mr-1" />
                        Verify Submission
                      </Button>
                    )}

                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() =>
                        setSelectedUndertaking(selectedUndertaking?.id === u.id ? null : u)
                      }
                    >
                      <Eye className="w-3.5 h-3.5 mr-1" />
                      {selectedUndertaking?.id === u.id ? 'Hide Details' : 'Details'}
                    </Button>
                  </div>
                </div>

                {/* Submissions History */}
                {selectedUndertaking?.id === u.id && (
                  <div className="mt-4 pt-4 border-t border-niyam-border space-y-3">
                    <h4 className="text-xs font-semibold text-niyam-text uppercase tracking-wider">
                      Compliance Submission History
                    </h4>
                    {u.submissions && u.submissions.length > 0 ? (
                      <div className="space-y-2">
                        {u.submissions.map((sub, idx) => (
                          <div
                            key={sub.id}
                            className="p-3 rounded bg-niyam-surface-alt border border-niyam-border text-xs space-y-1.5"
                          >
                            <div className="flex items-center justify-between">
                              <span className="font-semibold text-niyam-text">
                                Submission #{idx + 1} — {new Date(sub.submitted_at).toLocaleString()}
                              </span>
                              <Badge
                                variant={
                                  sub.status === 'accepted'
                                    ? 'success'
                                    : sub.status === 'rejected' || sub.status === 'returned_for_correction'
                                    ? 'danger'
                                    : 'info'
                                }
                              >
                                {sub.status.replace(/_/g, ' ').toUpperCase()}
                              </Badge>
                            </div>
                            {sub.remarks && (
                              <p className="text-niyam-text">
                                <strong>Remarks:</strong> {sub.remarks}
                              </p>
                            )}
                            {sub.review_comments && (
                              <p className="text-amber-800 bg-amber-50 p-2 rounded border border-amber-200">
                                <strong>Officer Review Comments:</strong> {sub.review_comments}
                              </p>
                            )}
                            {sub.file_id && (
                              <div className="pt-1">
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => downloadFile(`/files/${sub.file_id}/download`, `evidence_${sub.id}.pdf`)}
                                >
                                  <Download className="w-3 h-3 mr-1" />
                                  Download Attached Evidence
                                </Button>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-niyam-text-muted italic">
                        No submissions recorded for this undertaking condition.
                      </p>
                    )}
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}

      {/* MODAL 1: Create Undertaking (Officers only) */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6 space-y-4 border border-niyam-border">
            <h3 className="text-lg font-bold text-niyam-text">Issue Time-Bound Undertaking</h3>
            <p className="text-xs text-niyam-text-muted">
              Define a statutory compliance condition precedent and strict deadline.
            </p>

            {actionError && (
              <div className="p-3 rounded bg-red-50 text-red-700 text-xs flex items-center gap-2 border border-red-200">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{actionError}</span>
              </div>
            )}

            <form onSubmit={handleCreateSubmit} className="space-y-4">
              {availableApps.length > 0 && (
                <div>
                  <label className="block text-xs font-medium text-niyam-text mb-1">
                    Target Application *
                  </label>
                  <select
                    value={targetApplicationId}
                    onChange={(e) => {
                      setTargetApplicationId(e.target.value);
                      const app = availableApps.find((a) => a.id === e.target.value);
                      if (app?.institution_id) {
                        setTargetInstitutionId(app.institution_id);
                      }
                    }}
                    className="w-full text-xs border border-niyam-border rounded px-3 py-2 bg-white text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary"
                  >
                    {availableApps.map((app) => (
                      <option key={app.id} value={app.id}>
                        {app.reference_no} — {app.institution_name || 'Institution'}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div>
                <label className="block text-xs font-medium text-niyam-text mb-1">
                  Condition Title *
                </label>
                <Input
                  required
                  placeholder="e.g. Fire Safety Certificate Submission"
                  value={conditionTitle}
                  onChange={(e) => setConditionTitle(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-niyam-text mb-1">
                  Detailed Condition Description
                </label>
                <textarea
                  rows={3}
                  placeholder="State statutory clauses, required certified evidence, and rectifications..."
                  value={conditionDescription}
                  onChange={(e) => setConditionDescription(e.target.value)}
                  className="w-full text-xs border border-niyam-border rounded p-2 bg-white text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-niyam-text mb-1">
                  Compliance Due Date *
                </label>
                <input
                  type="date"
                  required
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  className="w-full text-xs border border-niyam-border rounded px-3 py-2 bg-white text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setIsCreateModalOpen(false)}
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
                <Button type="submit" size="sm" variant="primary" disabled={isSubmitting}>
                  {isSubmitting ? 'Creating...' : 'Issue Undertaking'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: Submit Compliance Evidence */}
      {isSubmitModalOpen && selectedUndertaking && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6 space-y-4 border border-niyam-border">
            <h3 className="text-lg font-bold text-niyam-text">Submit Compliance Evidence</h3>
            <p className="text-xs text-niyam-text-muted">
              Upload documentary proof of compliance for "{selectedUndertaking.condition_title}".
            </p>

            {actionError && (
              <div className="p-3 rounded bg-red-50 text-red-700 text-xs flex items-center gap-2 border border-red-200">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{actionError}</span>
              </div>
            )}

            <form onSubmit={handleSubmitEvidence} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-niyam-text mb-1">
                  Evidence Document (PDF, PNG, JPEG &le; 10MB)
                </label>
                <input
                  type="file"
                  accept=".pdf,.png,.jpg,.jpeg"
                  onChange={(e) => setEvidenceFile(e.target.files?.[0] || null)}
                  className="w-full text-xs border border-niyam-border rounded p-1.5 bg-white text-niyam-text file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:bg-slate-100 file:text-niyam-text"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-niyam-text mb-1">
                  Submission Remarks / Rectification Notes
                </label>
                <textarea
                  rows={3}
                  placeholder="Detail rectification steps taken, certificate numbers, validity period..."
                  value={evidenceRemarks}
                  onChange={(e) => setEvidenceRemarks(e.target.value)}
                  className="w-full text-xs border border-niyam-border rounded p-2 bg-white text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setIsSubmitModalOpen(false)}
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
                <Button type="submit" size="sm" variant="primary" disabled={isSubmitting}>
                  {isSubmitting ? 'Uploading...' : 'Submit Evidence'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 3: Review Evidence (Dual Control) */}
      {isReviewModalOpen && selectedUndertaking && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6 space-y-4 border border-niyam-border">
            <h3 className="text-lg font-bold text-niyam-text">Review Evidence (Dual-Control)</h3>
            <p className="text-xs text-niyam-text-muted">
              Verify compliance submission for "{selectedUndertaking.condition_title}".
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
                  Verification Determination *
                </label>
                <select
                  value={reviewDecision}
                  onChange={(e) =>
                    setReviewDecision(e.target.value as 'accepted' | 'rejected' | 'returned')
                  }
                  className="w-full text-xs border border-niyam-border rounded px-3 py-2 bg-white text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary"
                >
                  <option value="accepted">Accept & Mark Condition Fulfilled</option>
                  <option value="returned">Return for Clarification / Resubmission</option>
                  <option value="rejected">Reject Submission</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-niyam-text mb-1">
                  Review Comments / Justification *
                </label>
                <textarea
                  required
                  rows={3}
                  placeholder="Record verification findings and basis for determination..."
                  value={reviewComments}
                  onChange={(e) => setReviewComments(e.target.value)}
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
                  {isSubmitting ? 'Submitting...' : 'Confirm Verification'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
