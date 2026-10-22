import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  CheckCircle2,
  Clock,
  AlertTriangle,
  PlayCircle,
  PauseCircle,
  RotateCcw,
  UserCheck,
  Shield,
} from 'lucide-react';
import { Badge } from '../../components/Badge';
import { Button } from '../../components/Button';
import { Card } from '../../components/Card';
import { api, ApiClientError } from '../../lib/apiClient';
import { ApplicationDetail } from '../../types';

export const ApplicationDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [application, setApplication] = useState<ApplicationDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Action dialog states
  const [activeModal, setActiveModal] = useState<'advance' | 'return' | 'hold' | 'resume' | 'assign' | null>(null);
  const [advanceComments, setAdvanceComments] = useState('');
  const [returnReason, setReturnReason] = useState('');
  const [holdReason, setHoldReason] = useState('');
  const [resumeComments, setResumeComments] = useState('');
  const [assignUserId, setAssignUserId] = useState('');
  const [assignNotes, setAssignNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);

  const fetchApplicationDetails = useCallback(async () => {
    if (!id) return;
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.get<ApplicationDetail>(`/applications/${id}`);
      setApplication(data);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.message);
      } else {
        setError('Failed to load application details.');
      }
    } finally {
      setIsLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchApplicationDetails();
  }, [fetchApplicationDetails]);

  const handleAction = async (actionType: 'advance' | 'return' | 'hold' | 'resume' | 'assign') => {
    if (!id) return;
    setIsSubmitting(true);
    setModalError(null);
    setActionSuccess(null);

    try {
      if (actionType === 'advance') {
        await api.post(`/applications/${id}/advance`, {
          comments: advanceComments || undefined,
        });
        setActionSuccess('Application successfully advanced to the next workflow stage.');
      } else if (actionType === 'return') {
        if (!returnReason.trim()) {
          setModalError('A non-empty return reason is mandatory.');
          setIsSubmitting(false);
          return;
        }
        await api.post(`/applications/${id}/return`, {
          reason: returnReason.trim(),
        });
        setActionSuccess('Application returned for deficiency rectification.');
      } else if (actionType === 'hold') {
        if (!holdReason.trim()) {
          setModalError('A mandatory reason is required to place an application on hold.');
          setIsSubmitting(false);
          return;
        }
        await api.post(`/applications/${id}/hold`, {
          reason: holdReason.trim(),
        });
        setActionSuccess('Application has been placed on hold.');
      } else if (actionType === 'resume') {
        await api.post(`/applications/${id}/resume`, {
          comments: resumeComments || undefined,
        });
        setActionSuccess('Application resumed from hold.');
      } else if (actionType === 'assign') {
        if (!assignUserId.trim()) {
          setModalError('Please specify the reviewer user UUID.');
          setIsSubmitting(false);
          return;
        }
        await api.post(`/applications/${id}/assign`, {
          target_user_id: assignUserId.trim(),
          notes: assignNotes || undefined,
        });
        setActionSuccess('Application successfully assigned to reviewer desk.');
      }

      setActiveModal(null);
      // Reset inputs
      setAdvanceComments('');
      setReturnReason('');
      setHoldReason('');
      setResumeComments('');
      setAssignUserId('');
      setAssignNotes('');
      // Reload fresh state
      await fetchApplicationDetails();
    } catch (err) {
      if (err instanceof ApiClientError) {
        setModalError(err.message);
      } else {
        setModalError('Workflow action failed. Verify parameters.');
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
        return <Badge variant="warning">Returned (Deficiency)</Badge>;
      case 'on_hold':
        return <Badge variant="danger">On Hold</Badge>;
      case 'completed':
        return <Badge variant="success">Completed</Badge>;
      default:
        return <Badge variant="neutral">{status.replace(/_/g, ' ')}</Badge>;
    }
  };

  const getActionBadge = (action: string) => {
    switch (action) {
      case 'advance':
        return <Badge variant="success">Stage Advanced</Badge>;
      case 'return':
        return <Badge variant="warning">Returned</Badge>;
      case 'hold':
        return <Badge variant="danger">Placed On Hold</Badge>;
      case 'resume':
        return <Badge variant="info">Resumed</Badge>;
      case 'assigned':
        return <Badge variant="neutral">Assigned</Badge>;
      case 'created':
        return <Badge variant="neutral">Initiated</Badge>;
      default:
        return <Badge variant="neutral">{action}</Badge>;
    }
  };

  if (isLoading && !application) {
    return (
      <div className="min-h-[50vh] flex flex-col items-center justify-center gap-3">
        <div className="w-8 h-8 border-3 border-niyam-primary border-t-transparent rounded-full animate-spin" />
        <p className="text-xs font-semibold text-niyam-text-muted">Loading application dossier...</p>
      </div>
    );
  }

  if (error || !application) {
    return (
      <div className="p-6 bg-niyam-surface rounded-lg border border-niyam-border text-center max-w-lg mx-auto mt-8">
        <AlertTriangle className="w-10 h-10 text-niyam-status-danger mx-auto mb-3" />
        <h3 className="text-base font-bold text-niyam-text mb-1">Application Access Denied or Not Found</h3>
        <p className="text-xs text-niyam-text-muted mb-4">
          {error || 'The requested application does not exist or falls outside your authorised regional/institutional scope.'}
        </p>
        <Button variant="primary" onClick={() => navigate('/applications')} className="gap-1.5">
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Applications</span>
        </Button>
      </div>
    );
  }

  const currentSeq = application.current_stage_sequence || 1;
  const availableActions = application.available_actions || [];

  return (
    <div className="space-y-6">
      {/* Back button and Header */}
      <div className="flex flex-col gap-3 pb-2 border-b border-niyam-border">
        <button
          onClick={() => navigate('/applications')}
          className="flex items-center gap-1.5 text-xs font-medium text-niyam-text-muted hover:text-niyam-primary transition-colors w-fit"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Applications</span>
        </button>

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex flex-wrap items-center gap-2.5">
              <h2 className="text-xl sm:text-2xl font-bold font-mono text-niyam-primary">
                {application.reference_no}
              </h2>
              {getStatusBadge(application.status)}
              <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-amber-100 text-amber-800 border border-amber-200">
                Demo Record
              </span>
            </div>
            <p className="text-sm text-niyam-text-muted mt-1">
              {application.institution_name} &bull; Route: {application.route_name} (Pinned v{application.route_version})
            </p>
          </div>

          {/* Action buttons */}
          <div className="flex flex-wrap items-center gap-2">
            {availableActions.includes('advance') && (
              <Button
                variant="primary"
                onClick={() => {
                  setModalError(null);
                  setActiveModal('advance');
                }}
                className="gap-1.5 text-xs py-2"
              >
                <PlayCircle className="w-4 h-4" />
                <span>Advance Stage</span>
              </Button>
            )}

            {availableActions.includes('return') && (
              <Button
                variant="outline"
                onClick={() => {
                  setModalError(null);
                  setActiveModal('return');
                }}
                className="gap-1.5 text-xs py-2 border-amber-300 text-amber-800 hover:bg-amber-50"
              >
                <RotateCcw className="w-4 h-4 text-amber-600" />
                <span>Return for Deficiency</span>
              </Button>
            )}

            {availableActions.includes('hold') && (
              <Button
                variant="outline"
                onClick={() => {
                  setModalError(null);
                  setActiveModal('hold');
                }}
                className="gap-1.5 text-xs py-2 border-red-300 text-red-700 hover:bg-red-50"
              >
                <PauseCircle className="w-4 h-4 text-red-600" />
                <span>Place on Hold</span>
              </Button>
            )}

            {availableActions.includes('resume') && (
              <Button
                variant="primary"
                onClick={() => {
                  setModalError(null);
                  setActiveModal('resume');
                }}
                className="gap-1.5 text-xs py-2 bg-emerald-600 hover:bg-emerald-700 text-white"
              >
                <PlayCircle className="w-4 h-4" />
                <span>Resume from Hold</span>
              </Button>
            )}

            {availableActions.includes('assign') && (
              <Button
                variant="outline"
                onClick={() => {
                  setModalError(null);
                  setActiveModal('assign');
                }}
                className="gap-1.5 text-xs py-2"
              >
                <UserCheck className="w-4 h-4 text-niyam-primary" />
                <span>Assign Reviewer</span>
              </Button>
            )}
          </div>
        </div>
      </div>

      {actionSuccess && (
        <div className="p-3 rounded-md bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-medium flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{actionSuccess}</span>
          </div>
          <button onClick={() => setActionSuccess(null)} className="text-emerald-700 hover:text-emerald-900">
            ✕
          </button>
        </div>
      )}

      {/* Visual Workflow Progression Stepper */}
      <Card
        title="Workflow Progression Stepper"
        subtitle={`Permanently pinned to route configuration: ${application.route_name} (Version ${application.route_version})`}
      >
        <div className="pt-2 pb-4 overflow-x-auto">
          <div className="flex items-center min-w-[650px] relative">
            {application.stages.map((stage, idx) => {
              const isPast = stage.sequence < currentSeq;
              const isCurrent = stage.sequence === currentSeq;

              return (
                <div key={stage.id} className="flex-1 flex flex-col items-center relative text-center px-1">
                  {/* Connecting Line */}
                  {idx > 0 && (
                    <div
                      className={`absolute top-4 -left-1/2 right-1/2 h-0.5 -z-0 ${
                        isPast ? 'bg-niyam-primary' : isCurrent ? 'bg-niyam-primary-tint' : 'bg-niyam-border'
                      }`}
                    />
                  )}

                  {/* Stage Number / Check Icon */}
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs relative z-10 transition-colors shadow-xs ${
                      isPast
                        ? 'bg-niyam-primary text-white'
                        : isCurrent
                        ? 'bg-amber-500 text-white ring-4 ring-amber-100'
                        : 'bg-niyam-surface-alt border border-niyam-border text-niyam-text-muted'
                    }`}
                  >
                    {isPast ? <CheckCircle2 className="w-4 h-4" /> : stage.sequence}
                  </div>

                  {/* Stage Label */}
                  <p
                    className={`mt-2 text-xs font-semibold leading-tight ${
                      isCurrent ? 'text-amber-900 font-bold' : isPast ? 'text-niyam-text' : 'text-niyam-text-muted'
                    }`}
                  >
                    {stage.stage_name}
                  </p>

                  <span className="text-[10px] text-niyam-text-muted mt-0.5 font-medium">
                    {stage.required_role.replace(/_/g, ' ')}
                  </span>
                  <span className="text-[10px] text-slate-500 mt-0.5">
                    {stage.timeline_days} {stage.day_type} days
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </Card>

      {/* Two Column Summary & Timeline */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Dossier Summary */}
        <div className="lg:col-span-1 space-y-6">
          <Card title="Application Dossier" subtitle="System metadata and jurisdictional bounds">
            <div className="space-y-3.5 text-xs">
              <div>
                <span className="text-niyam-text-muted block text-[11px]">Reference Number</span>
                <span className="font-mono font-bold text-niyam-text text-sm">{application.reference_no}</span>
              </div>

              <div>
                <span className="text-niyam-text-muted block text-[11px]">Applicant Institution</span>
                <p className="font-semibold text-niyam-text">{application.institution_name}</p>
                <p className="text-[11px] text-niyam-text-muted font-mono">{application.institution_code}</p>
              </div>

              <div>
                <span className="text-niyam-text-muted block text-[11px]">Assigned Reviewer</span>
                <p className="font-semibold text-niyam-text">
                  {application.assigned_to_name ? (
                    <span className="flex items-center gap-1.5 text-niyam-primary">
                      <UserCheck className="w-3.5 h-3.5" />
                      <span>{application.assigned_to_name}</span>
                    </span>
                  ) : (
                    <span className="italic text-niyam-text-muted">Unassigned Scrutiny Pool</span>
                  )}
                </p>
              </div>

              <div>
                <span className="text-niyam-text-muted block text-[11px]">Current Stage Details</span>
                <p className="font-semibold text-niyam-text">
                  Stage {application.current_stage_sequence}: {application.current_stage_name}
                </p>
                <p className="text-[11px] text-niyam-text-muted">
                  Required Role: <code className="bg-slate-100 px-1 rounded">{application.current_stage_role}</code>
                </p>
              </div>

              <div>
                <span className="text-niyam-text-muted block text-[11px]">Timestamps</span>
                <div className="space-y-1 text-[11px] text-niyam-text-muted mt-1">
                  <p>
                    Submitted:{' '}
                    <span className="text-niyam-text font-medium">
                      {application.submitted_at ? new Date(application.submitted_at).toLocaleString() : '—'}
                    </span>
                  </p>
                  <p>
                    Entered Stage:{' '}
                    <span className="text-niyam-text font-medium">
                      {application.stage_entered_at ? new Date(application.stage_entered_at).toLocaleString() : '—'}
                    </span>
                  </p>
                </div>
              </div>

              <div className="pt-2 border-t border-niyam-border">
                <div className="p-2.5 rounded bg-niyam-surface-alt border border-niyam-border text-[11px] text-niyam-text-muted flex items-start gap-1.5">
                  <Shield className="w-3.5 h-3.5 text-niyam-primary shrink-0 mt-0.5" />
                  <span>
                    Auditable Workflow: Every transition is hashed into the cryptographic SHA-256 audit log.
                  </span>
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* Right Column: Chronological Stage History */}
        <div className="lg:col-span-2">
          <Card
            title="Chronological Stage History"
            subtitle={`${application.history.length} auditable lifecycle events recorded for this application`}
          >
            {application.history.length === 0 ? (
              <p className="text-xs text-niyam-text-muted py-4">No stage history recorded yet.</p>
            ) : (
              <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-niyam-border">
                {application.history.map((h) => (
                  <div key={h.id} className="relative">
                    {/* Timeline dot */}
                    <div className="absolute -left-6 top-1 w-3.5 h-3.5 rounded-full bg-niyam-primary border-2 border-white shadow-xs" />

                    <div className="bg-niyam-surface-alt/70 border border-niyam-border rounded-lg p-3.5 text-xs">
                      <div className="flex flex-wrap items-center justify-between gap-2 mb-1.5">
                        <div className="flex items-center gap-2">
                          {getActionBadge(h.action)}
                          <span className="font-semibold text-niyam-text">
                            {h.to_stage_name ? `To: ${h.to_stage_name}` : 'Application Initialized'}
                          </span>
                        </div>
                        <span className="text-[11px] text-niyam-text-muted flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          <span>{new Date(h.performed_at).toLocaleString()}</span>
                        </span>
                      </div>

                      {h.reason && (
                        <div
                          className={`mt-2 p-2.5 rounded text-xs ${
                            h.action === 'return'
                              ? 'bg-amber-50 border border-amber-200 text-amber-900 font-medium'
                              : h.action === 'hold'
                              ? 'bg-red-50 border border-red-200 text-red-900 font-medium'
                              : 'bg-niyam-surface border border-niyam-border text-niyam-text'
                          }`}
                        >
                          <span className="font-semibold block mb-0.5">
                            {h.action === 'return' ? 'Deficiency Reason:' : h.action === 'hold' ? 'Hold Reason:' : 'Notes / Remarks:'}
                          </span>
                          <span>{h.reason}</span>
                        </div>
                      )}

                      <div className="mt-2 text-[11px] text-niyam-text-muted flex items-center justify-between">
                        <span>
                          Action Performed By:{' '}
                          <span className="font-semibold text-niyam-text">
                            {h.performed_by_name || 'System Officer'}
                          </span>
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>

      {/* Advance Modal */}
      {activeModal === 'advance' && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-niyam-surface rounded-lg border border-niyam-border max-w-md w-full p-6 shadow-xl">
            <h3 className="text-base font-bold text-niyam-text mb-2 flex items-center gap-2">
              <PlayCircle className="w-5 h-5 text-niyam-primary" />
              <span>Confirm Stage Advance</span>
            </h3>
            <p className="text-xs text-niyam-text-muted mb-4">
              Advance application <span className="font-mono font-semibold">{application.reference_no}</span> to the next sequential stage in its workflow route.
            </p>

            {modalError && (
              <div className="mb-3 p-2.5 rounded bg-red-50 border border-red-200 text-niyam-status-danger text-xs font-medium">
                {modalError}
              </div>
            )}

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-niyam-text mb-1">
                  Remarks / Review Comments (Optional)
                </label>
                <textarea
                  value={advanceComments}
                  onChange={(e) => setAdvanceComments(e.target.value)}
                  placeholder="Enter any scrutiny or review notes..."
                  className="w-full text-xs bg-niyam-surface border border-niyam-border rounded-md p-2.5 text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary h-20"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-4 border-t border-niyam-border mt-4">
              <Button variant="outline" onClick={() => setActiveModal(null)} disabled={isSubmitting}>
                Cancel
              </Button>
              <Button variant="primary" onClick={() => handleAction('advance')} isLoading={isSubmitting}>
                Confirm & Advance
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Return Modal (Mandatory Reason) */}
      {activeModal === 'return' && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-niyam-surface rounded-lg border border-niyam-border max-w-md w-full p-6 shadow-xl">
            <h3 className="text-base font-bold text-amber-900 mb-2 flex items-center gap-2">
              <RotateCcw className="w-5 h-5 text-amber-600" />
              <span>Return Application for Deficiency</span>
            </h3>
            <p className="text-xs text-niyam-text-muted mb-4">
              Returns the application for document re-upload or clarification. A clear, specific justification reason is mandatory.
            </p>

            {modalError && (
              <div className="mb-3 p-2.5 rounded bg-red-50 border border-red-200 text-niyam-status-danger text-xs font-medium">
                {modalError}
              </div>
            )}

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-niyam-text mb-1">
                  Mandatory Return Reason *
                </label>
                <textarea
                  value={returnReason}
                  onChange={(e) => setReturnReason(e.target.value)}
                  placeholder="State the missing documents, regulatory deficiencies, or discrepancies..."
                  className="w-full text-xs bg-niyam-surface border border-niyam-border rounded-md p-2.5 text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary h-24"
                  required
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-4 border-t border-niyam-border mt-4">
              <Button variant="outline" onClick={() => setActiveModal(null)} disabled={isSubmitting}>
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={() => handleAction('return')}
                isLoading={isSubmitting}
                className="bg-amber-600 hover:bg-amber-700 text-white"
              >
                Submit Return Action
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Hold Modal (Mandatory Reason) */}
      {activeModal === 'hold' && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-niyam-surface rounded-lg border border-niyam-border max-w-md w-full p-6 shadow-xl">
            <h3 className="text-base font-bold text-red-900 mb-2 flex items-center gap-2">
              <PauseCircle className="w-5 h-5 text-red-600" />
              <span>Place Application on Hold</span>
            </h3>
            <p className="text-xs text-niyam-text-muted mb-4">
              Freezes application stage progress until explicitly resumed. A documented statutory or operational justification is required.
            </p>

            {modalError && (
              <div className="mb-3 p-2.5 rounded bg-red-50 border border-red-200 text-niyam-status-danger text-xs font-medium">
                {modalError}
              </div>
            )}

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-niyam-text mb-1">
                  Reason for Hold *
                </label>
                <textarea
                  value={holdReason}
                  onChange={(e) => setHoldReason(e.target.value)}
                  placeholder="Provide statutory justification or pending court / regulatory inquiry context..."
                  className="w-full text-xs bg-niyam-surface border border-niyam-border rounded-md p-2.5 text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary h-24"
                  required
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-4 border-t border-niyam-border mt-4">
              <Button variant="outline" onClick={() => setActiveModal(null)} disabled={isSubmitting}>
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={() => handleAction('hold')}
                isLoading={isSubmitting}
                className="bg-red-600 hover:bg-red-700 text-white"
              >
                Place on Hold
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Resume Modal */}
      {activeModal === 'resume' && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-niyam-surface rounded-lg border border-niyam-border max-w-md w-full p-6 shadow-xl">
            <h3 className="text-base font-bold text-emerald-900 mb-2 flex items-center gap-2">
              <PlayCircle className="w-5 h-5 text-emerald-600" />
              <span>Resume Application from Hold</span>
            </h3>
            <p className="text-xs text-niyam-text-muted mb-4">
              Restores application to active review status and allows subsequent stage advances.
            </p>

            {modalError && (
              <div className="mb-3 p-2.5 rounded bg-red-50 border border-red-200 text-niyam-status-danger text-xs font-medium">
                {modalError}
              </div>
            )}

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-niyam-text mb-1">
                  Resume Remarks (Optional)
                </label>
                <textarea
                  value={resumeComments}
                  onChange={(e) => setResumeComments(e.target.value)}
                  placeholder="Note the resolution of the hold condition..."
                  className="w-full text-xs bg-niyam-surface border border-niyam-border rounded-md p-2.5 text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary h-20"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-4 border-t border-niyam-border mt-4">
              <Button variant="outline" onClick={() => setActiveModal(null)} disabled={isSubmitting}>
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={() => handleAction('resume')}
                isLoading={isSubmitting}
                className="bg-emerald-600 hover:bg-emerald-700 text-white"
              >
                Confirm Resume
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Assign Reviewer Modal */}
      {activeModal === 'assign' && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-niyam-surface rounded-lg border border-niyam-border max-w-md w-full p-6 shadow-xl">
            <h3 className="text-base font-bold text-niyam-text mb-2 flex items-center gap-2">
              <UserCheck className="w-5 h-5 text-niyam-primary" />
              <span>Assign Application Reviewer</span>
            </h3>
            <p className="text-xs text-niyam-text-muted mb-4">
              Assign this application to an active officer within the appropriate regional jurisdiction.
            </p>

            {modalError && (
              <div className="mb-3 p-2.5 rounded bg-red-50 border border-red-200 text-niyam-status-danger text-xs font-medium">
                {modalError}
              </div>
            )}

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-niyam-text mb-1">
                  Target Reviewer User UUID *
                </label>
                <input
                  type="text"
                  value={assignUserId}
                  onChange={(e) => setAssignUserId(e.target.value)}
                  placeholder="e.g. 550e8400-e29b-41d4-a716-446655440000"
                  className="w-full text-xs bg-niyam-surface border border-niyam-border rounded-md p-2.5 text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary font-mono"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-niyam-text mb-1">
                  Assignment Notes (Optional)
                </label>
                <textarea
                  value={assignNotes}
                  onChange={(e) => setAssignNotes(e.target.value)}
                  placeholder="Specific desk scrutiny instructions..."
                  className="w-full text-xs bg-niyam-surface border border-niyam-border rounded-md p-2.5 text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary h-20"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-4 border-t border-niyam-border mt-4">
              <Button variant="outline" onClick={() => setActiveModal(null)} disabled={isSubmitting}>
                Cancel
              </Button>
              <Button variant="primary" onClick={() => handleAction('assign')} isLoading={isSubmitting}>
                Confirm Assignment
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
