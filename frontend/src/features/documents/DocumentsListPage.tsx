import React, { useState, useEffect, useCallback } from 'react';
import {
  AlertTriangle,
  CheckCircle,
  Clock,
  Plus,
  RefreshCw,
  Download,
  ShieldCheck,
  RotateCcw,
  Eye,
  AlertCircle,
  FileCheck,
} from 'lucide-react';
import { api, downloadFile } from '../../lib/apiClient';
import { DocumentItem } from '../../types';
import { useAuth } from '../../app/AuthContext';
import { Badge } from '../../components/Badge';
import { Button } from '../../components/Button';
import { Card } from '../../components/Card';
import { Input } from '../../components/Input';
import { LoadingState, ErrorState, EmptyState } from '../../components/States';

export const DocumentsListPage: React.FC = () => {
  const { user } = useAuth();
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const [selectedDoc, setSelectedDoc] = useState<DocumentItem | null>(null);

  // Modals
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [isVerifyModalOpen, setIsVerifyModalOpen] = useState(false);
  const [isReplaceModalOpen, setIsReplaceModalOpen] = useState(false);

  // Form states - Upload Document
  const [docType, setDocType] = useState('land_lease');
  const [title, setTitle] = useState('');
  const [docNumber, setDocNumber] = useState('');
  const [issuingAuthority, setIssuingAuthority] = useState('');
  const [validFrom, setValidFrom] = useState('');
  const [validTo, setValidTo] = useState('');
  const [targetInstitutionId, setTargetInstitutionId] = useState('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);

  // Form states - Verify Document
  const [verifyStatus, setVerifyStatus] = useState<'verified' | 'rejected'>('verified');
  const [verificationNotes, setVerificationNotes] = useState('');

  // Form states - Replace Renewal Document
  const [replaceTitle, setReplaceTitle] = useState('');
  const [replaceDocNumber, setReplaceDocNumber] = useState('');
  const [replaceIssuingAuthority, setReplaceIssuingAuthority] = useState('');
  const [replaceValidFrom, setReplaceValidFrom] = useState('');
  const [replaceValidTo, setReplaceValidTo] = useState('');
  const [replaceRemarks, setReplaceRemarks] = useState('');
  const [replaceFile, setReplaceFile] = useState<File | null>(null);

  const [actionError, setActionError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isOfficerOrAdmin =
    user?.role === 'scrutiny_officer' ||
    user?.role === 'regional_officer' ||
    user?.role === 'bureau_officer' ||
    user?.role === 'system_admin' ||
    user?.role === 'admin';

  const fetchDocuments = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.get<DocumentItem[]>('/documents');
      setDocuments(data);
      if (selectedDoc) {
        const updated = data.find((d) => d.id === selectedDoc.id);
        if (updated) setSelectedDoc(updated);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load documents';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }, [selectedDoc]);

  useEffect(() => {
    fetchDocuments();
  }, []);

  // Metrics
  const validCount = documents.filter((d) => !d.is_expired && !d.is_expiring_soon && d.status === 'verified').length;
  const expiringCount = documents.filter((d) => d.is_expiring_soon).length;
  const expiredCount = documents.filter((d) => d.is_expired).length;
  const pendingVerifyCount = documents.filter((d) => d.status === 'pending_verification').length;

  const filteredDocuments = documents.filter((d) => {
    if (typeFilter !== 'all' && d.document_type !== typeFilter) return false;
    if (statusFilter === 'valid' && (d.is_expired || d.is_expiring_soon || d.status !== 'verified')) return false;
    if (statusFilter === 'expiring_soon' && !d.is_expiring_soon) return false;
    if (statusFilter === 'expired' && !d.is_expired) return false;
    if (statusFilter === 'pending_verification' && d.status !== 'pending_verification') return false;

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchTitle = d.title.toLowerCase().includes(q);
      const matchInst = d.institution_name?.toLowerCase().includes(q);
      const matchNum = d.document_number?.toLowerCase().includes(q);
      if (!matchTitle && !matchInst && !matchNum) return false;
    }
    return true;
  });

  const handleOpenUploadModal = () => {
    setDocType('land_lease');
    setTitle('');
    setDocNumber('');
    setIssuingAuthority('');
    setValidFrom('');
    setValidTo('');
    setTargetInstitutionId(user?.institution_id || '');
    setUploadFile(null);
    setActionError(null);
    setIsUploadModalOpen(true);
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) {
      setActionError('Please select a valid PDF, PNG, or JPEG file');
      return;
    }
    if (validFrom && validTo && new Date(validFrom) > new Date(validTo)) {
      setActionError('Valid From date cannot be later than Valid To date');
      return;
    }
    setIsSubmitting(true);
    setActionError(null);
    try {
      const formData = new FormData();
      formData.append('document_type', docType);
      formData.append('title', title);
      if (docNumber.trim()) formData.append('document_number', docNumber.trim());
      if (issuingAuthority.trim()) formData.append('issuing_authority', issuingAuthority.trim());
      if (validFrom) formData.append('valid_from', validFrom);
      if (validTo) formData.append('valid_to', validTo);
      if (targetInstitutionId) formData.append('institution_id', targetInstitutionId);
      formData.append('file', uploadFile);

      await api.postForm('/documents', formData);
      setIsUploadModalOpen(false);
      await fetchDocuments();
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : 'Failed to register document');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOpenVerifyModal = (doc: DocumentItem) => {
    setSelectedDoc(doc);
    setVerifyStatus('verified');
    setVerificationNotes('');
    setActionError(null);
    setIsVerifyModalOpen(true);
  };

  const handleVerifySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDoc) return;
    setIsSubmitting(true);
    setActionError(null);
    try {
      await api.post(`/documents/${selectedDoc.id}/verify`, {
        status: verifyStatus,
        verification_notes: verificationNotes.trim() ? verificationNotes.trim() : undefined,
      });
      setIsVerifyModalOpen(false);
      await fetchDocuments();
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : 'Failed to verify document');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleInitiateRenewal = async (doc: DocumentItem) => {
    if (!window.confirm(`Initiate formal renewal workflow for "${doc.title}"?`)) return;
    setIsSubmitting(true);
    try {
      await api.post(`/documents/${doc.id}/renew`);
      await fetchDocuments();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to initiate renewal');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOpenReplaceModal = (doc: DocumentItem) => {
    setSelectedDoc(doc);
    setReplaceTitle(`Renewed ${doc.title}`);
    setReplaceDocNumber('');
    setReplaceIssuingAuthority(doc.issuing_authority || '');
    setReplaceValidFrom(new Date().toISOString().split('T')[0]);
    setReplaceValidTo('');
    setReplaceRemarks('Replacement certificate submitted pursuant to renewal');
    setReplaceFile(null);
    setActionError(null);
    setIsReplaceModalOpen(true);
  };

  const handleReplaceSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDoc) return;
    const activeRenewal = selectedDoc.renewals.find(
      (r) => r.renewal_status === 'initiated' || r.renewal_status === 'in_progress'
    );
    if (!activeRenewal) {
      setActionError('No active renewal cycle found for this document');
      return;
    }
    if (!replaceFile) {
      setActionError('Replacement certificate document is mandatory');
      return;
    }
    if (replaceValidFrom && replaceValidTo && new Date(replaceValidFrom) > new Date(replaceValidTo)) {
      setActionError('Valid From date cannot be later than Valid To date');
      return;
    }

    setIsSubmitting(true);
    setActionError(null);
    try {
      const formData = new FormData();
      formData.append('title', replaceTitle);
      if (replaceDocNumber.trim()) formData.append('document_number', replaceDocNumber.trim());
      if (replaceIssuingAuthority.trim()) formData.append('issuing_authority', replaceIssuingAuthority.trim());
      if (replaceValidFrom) formData.append('valid_from', replaceValidFrom);
      if (replaceValidTo) formData.append('valid_to', replaceValidTo);
      if (replaceRemarks.trim()) formData.append('remarks', replaceRemarks.trim());
      formData.append('file', replaceFile);

      await api.postForm(`/documents/renewals/${activeRenewal.id}/replace`, formData);
      setIsReplaceModalOpen(false);
      await fetchDocuments();
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : 'Failed to submit replacement document');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-niyam-border">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-niyam-text">
            Institutional Document Validity & Lease Renewal
          </h2>
          <p className="text-sm text-niyam-text-muted mt-1">
            Validity tracking for land title leases, building safety certificates, fire NOCs, and seamless renewal chains.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button size="sm" variant="primary" onClick={handleOpenUploadModal}>
            <Plus className="w-4 h-4 mr-1" />
            Register Document
          </Button>
          <Button variant="outline" size="sm" onClick={fetchDocuments} disabled={isLoading}>
            <RefreshCw className={`w-4 h-4 mr-1 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="border-l-4 border-l-emerald-500">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-emerald-50 text-niyam-status-success flex items-center justify-center">
              <CheckCircle className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-niyam-text-muted font-medium">Valid Documents</p>
              <p className="text-xl font-bold text-niyam-text">{validCount} Compliant</p>
            </div>
          </div>
        </Card>

        <Card className="border-l-4 border-l-amber-500">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-amber-50 text-niyam-status-warning flex items-center justify-center">
              <Clock className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-niyam-text-muted font-medium">Expiring Soon (30 Days)</p>
              <p className="text-xl font-bold text-niyam-status-warning">{expiringCount} Notice</p>
            </div>
          </div>
        </Card>

        <Card className="border-l-4 border-l-rose-500">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-rose-50 text-niyam-status-danger flex items-center justify-center">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-niyam-text-muted font-medium">Expired Documents</p>
              <p className="text-xl font-bold text-rose-700">{expiredCount} Non-Compliant</p>
            </div>
          </div>
        </Card>

        <Card className="border-l-4 border-l-blue-500">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-blue-50 text-niyam-primary flex items-center justify-center">
              <FileCheck className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs text-niyam-text-muted font-medium">Pending Verification</p>
              <p className="text-xl font-bold text-niyam-text">{pendingVerifyCount} Pending</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between bg-niyam-surface p-3 rounded-lg border border-niyam-border">
        <div className="flex-1 w-full sm:max-w-xs">
          <Input
            placeholder="Search by title, number, or institution..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full text-sm"
          />
        </div>
        <div className="flex items-center gap-2 flex-wrap w-full sm:w-auto">
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="text-xs border border-niyam-border rounded px-2.5 py-1.5 bg-white text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary"
          >
            <option value="all">All Document Types</option>
            <option value="land_lease">Land Lease / Title Deed</option>
            <option value="occupancy_certificate">Occupancy Certificate</option>
            <option value="fire_noc">Fire Safety NOC</option>
            <option value="building_plan">Building Plan Approval</option>
            <option value="structural_stability">Structural Stability</option>
            <option value="financial_audit">Audit / Fixed Deposit</option>
            <option value="other">Other Statutory</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs border border-niyam-border rounded px-2.5 py-1.5 bg-white text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary"
          >
            <option value="all">All Validity Statuses</option>
            <option value="valid">Valid & Verified</option>
            <option value="expiring_soon">Expiring Soon</option>
            <option value="expired">Expired</option>
            <option value="pending_verification">Pending Verification</option>
          </select>
        </div>
      </div>

      {/* Document List */}
      {isLoading ? (
        <LoadingState message="Loading documents register..." />
      ) : error ? (
        <ErrorState message={error} onRetry={fetchDocuments} />
      ) : filteredDocuments.length === 0 ? (
        <EmptyState
          title="No documents found"
          description={
            searchQuery || typeFilter !== 'all' || statusFilter !== 'all'
              ? 'No documents match your specified filters.'
              : 'No statutory documents are registered yet.'
          }
        />
      ) : (
        <div className="space-y-4">
          {filteredDocuments.map((doc) => {
            const hasActiveRenewal = doc.renewals.some(
              (r) => r.renewal_status === 'initiated' || r.renewal_status === 'in_progress'
            );

            return (
              <Card key={doc.id} className="hover:border-niyam-border-focus transition-colors">
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                  <div className="space-y-1.5 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-semibold text-niyam-text text-base">
                        {doc.title}
                      </span>
                      {doc.is_expired ? (
                        <Badge variant="danger">EXPIRED</Badge>
                      ) : doc.is_expiring_soon ? (
                        <Badge variant="warning">EXPIRING SOON</Badge>
                      ) : doc.status === 'verified' ? (
                        <Badge variant="success">VERIFIED & VALID</Badge>
                      ) : (
                        <Badge variant="neutral">{doc.status.replace(/_/g, ' ').toUpperCase()}</Badge>
                      )}
                      <Badge variant="neutral">{doc.document_type.replace(/_/g, ' ').toUpperCase()}</Badge>
                      {hasActiveRenewal && <Badge variant="warning">RENEWAL IN PROGRESS</Badge>}
                    </div>

                    <p className="text-sm text-niyam-text font-medium">
                      {doc.institution_name || 'Institution Name Unavailable'}
                      {doc.document_number && ` • Ref: ${doc.document_number}`}
                    </p>

                    <div className="flex items-center gap-4 text-xs text-niyam-text-muted flex-wrap">
                      {doc.issuing_authority && (
                        <span>
                          <strong>Issuer:</strong> {doc.issuing_authority}
                        </span>
                      )}
                      {doc.valid_from && (
                        <span>
                          <strong>From:</strong> {doc.valid_from}
                        </span>
                      )}
                      {doc.valid_to && (
                        <span>
                          <strong>Valid Till:</strong>{' '}
                          <span
                            className={
                              doc.is_expired
                                ? 'text-rose-700 font-bold'
                                : doc.is_expiring_soon
                                ? 'text-amber-700 font-bold'
                                : ''
                            }
                          >
                            {doc.valid_to}
                          </span>
                        </span>
                      )}
                      {doc.original_filename && (
                        <span>
                          <strong>File:</strong> {doc.original_filename} (
                          {doc.file_size_bytes ? `${Math.round(doc.file_size_bytes / 1024)} KB` : ''})
                        </span>
                      )}
                    </div>

                    {doc.verification_notes && (
                      <p className="text-xs bg-slate-50 text-niyam-text p-2 rounded border border-niyam-border mt-1">
                        <strong>Verification Notes:</strong> {doc.verification_notes}
                      </p>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 flex-wrap lg:self-center">
                    {/* Authorized Download */}
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() =>
                        downloadFile(
                          `/documents/${doc.id}/download`,
                          doc.original_filename || `${doc.title}.pdf`
                        )
                      }
                    >
                      <Download className="w-3.5 h-3.5 mr-1" />
                      Download
                    </Button>

                    {/* Verify Document (Officers only - Dual Control) */}
                    {isOfficerOrAdmin && doc.status === 'pending_verification' && (
                      <Button
                        size="sm"
                        variant="primary"
                        onClick={() => handleOpenVerifyModal(doc)}
                      >
                        <ShieldCheck className="w-3.5 h-3.5 mr-1" />
                        Verify
                      </Button>
                    )}

                    {/* Initiate Renewal */}
                    {!hasActiveRenewal && (doc.is_expired || doc.is_expiring_soon || doc.status === 'verified') && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleInitiateRenewal(doc)}
                        disabled={isSubmitting}
                      >
                        <RotateCcw className="w-3.5 h-3.5 mr-1" />
                        Renew
                      </Button>
                    )}

                    {/* Submit Replacement Document (if renewal active) */}
                    {hasActiveRenewal && (
                      <Button
                        size="sm"
                        variant="primary"
                        onClick={() => handleOpenReplaceModal(doc)}
                      >
                        <FileCheck className="w-3.5 h-3.5 mr-1" />
                        Upload Replacement
                      </Button>
                    )}

                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setSelectedDoc(selectedDoc?.id === doc.id ? null : doc)}
                    >
                      <Eye className="w-3.5 h-3.5 mr-1" />
                      {selectedDoc?.id === doc.id ? 'Hide Details' : 'Details'}
                    </Button>
                  </div>
                </div>

                {/* Renewal and Version History */}
                {selectedDoc?.id === doc.id && (
                  <div className="mt-4 pt-4 border-t border-niyam-border space-y-3">
                    <h4 className="text-xs font-semibold text-niyam-text uppercase tracking-wider">
                      Renewal & Version Continuity Log
                    </h4>
                    {doc.renewals && doc.renewals.length > 0 ? (
                      <div className="space-y-2">
                        {doc.renewals.map((ren, idx) => (
                          <div
                            key={ren.id}
                            className="p-3 rounded bg-niyam-surface-alt border border-niyam-border text-xs space-y-1.5"
                          >
                            <div className="flex items-center justify-between">
                              <span className="font-semibold text-niyam-text">
                                Renewal Cycle #{idx + 1} — Initiated {new Date(ren.initiated_at).toLocaleDateString()}
                              </span>
                              <Badge
                                variant={
                                  ren.renewal_status === 'completed'
                                    ? 'success'
                                    : ren.renewal_status === 'cancelled'
                                    ? 'danger'
                                    : 'warning'
                                }
                              >
                                {ren.renewal_status.replace(/_/g, ' ').toUpperCase()}
                              </Badge>
                            </div>
                            {ren.completed_at && (
                              <p className="text-niyam-text-muted">
                                <strong>Completed At:</strong> {new Date(ren.completed_at).toLocaleString()}
                              </p>
                            )}
                            {ren.replacement_document_id && (
                              <p className="text-emerald-700">
                                <strong>Replacement Document ID:</strong> {ren.replacement_document_id} (Full continuity preserved)
                              </p>
                            )}
                            {ren.remarks && (
                              <p className="text-niyam-text">
                                <strong>Remarks:</strong> {ren.remarks}
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-niyam-text-muted italic">
                        No previous renewal cycles recorded for this document. Original baseline active.
                      </p>
                    )}
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}

      {/* MODAL 1: Register & Upload Document */}
      {isUploadModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6 space-y-4 border border-niyam-border">
            <h3 className="text-lg font-bold text-niyam-text">Register Statutory Document</h3>
            <p className="text-xs text-niyam-text-muted">
              Upload institutional land title, building approval, or NOC with validity timeline.
            </p>

            {actionError && (
              <div className="p-3 rounded bg-red-50 text-red-700 text-xs flex items-center gap-2 border border-red-200">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{actionError}</span>
              </div>
            )}

            <form onSubmit={handleUploadSubmit} className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-niyam-text mb-1">
                  Document Type *
                </label>
                <select
                  value={docType}
                  onChange={(e) => setDocType(e.target.value)}
                  className="w-full text-xs border border-niyam-border rounded px-3 py-2 bg-white text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary"
                >
                  <option value="land_lease">Land Lease / Title Deed (Long-Term)</option>
                  <option value="occupancy_certificate">Occupancy & Completion Certificate</option>
                  <option value="fire_noc">Fire Safety NOC</option>
                  <option value="building_plan">Sanctioned Building Plan</option>
                  <option value="structural_stability">Structural Stability Certificate</option>
                  <option value="financial_audit">Audit / Fixed Deposit Receipt</option>
                  <option value="other">Other Regulatory Document</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-niyam-text mb-1">
                  Document Title *
                </label>
                <Input
                  required
                  placeholder="e.g. Registered Land Lease (30 Years)"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs font-medium text-niyam-text mb-1">
                    Document Ref No.
                  </label>
                  <Input
                    placeholder="Reg / Deed #"
                    value={docNumber}
                    onChange={(e) => setDocNumber(e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-niyam-text mb-1">
                    Issuing Authority
                  </label>
                  <Input
                    placeholder="e.g. Sub-Registrar / Fire Dept."
                    value={issuingAuthority}
                    onChange={(e) => setIssuingAuthority(e.target.value)}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs font-medium text-niyam-text mb-1">
                    Valid From Date
                  </label>
                  <input
                    type="date"
                    value={validFrom}
                    onChange={(e) => setValidFrom(e.target.value)}
                    className="w-full text-xs border border-niyam-border rounded px-2.5 py-1.5 bg-white text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-niyam-text mb-1">
                    Valid Till Date
                  </label>
                  <input
                    type="date"
                    value={validTo}
                    onChange={(e) => setValidTo(e.target.value)}
                    className="w-full text-xs border border-niyam-border rounded px-2.5 py-1.5 bg-white text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-niyam-text mb-1">
                  Document File (PDF, PNG, JPEG &le; 10MB) *
                </label>
                <input
                  type="file"
                  required
                  accept=".pdf,.png,.jpg,.jpeg"
                  onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                  className="w-full text-xs border border-niyam-border rounded p-1.5 bg-white text-niyam-text file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:bg-slate-100 file:text-niyam-text"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setIsUploadModalOpen(false)}
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
                <Button type="submit" size="sm" variant="primary" disabled={isSubmitting}>
                  {isSubmitting ? 'Uploading...' : 'Register Document'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: Verify Document (Officers only - Dual Control) */}
      {isVerifyModalOpen && selectedDoc && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6 space-y-4 border border-niyam-border">
            <h3 className="text-lg font-bold text-niyam-text">Verify Statutory Document (Dual-Control)</h3>
            <p className="text-xs text-niyam-text-muted">
              Authorized officer determination for "{selectedDoc.title}".
            </p>

            {actionError && (
              <div className="p-3 rounded bg-red-50 text-red-700 text-xs flex items-center gap-2 border border-red-200">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{actionError}</span>
              </div>
            )}

            <form onSubmit={handleVerifySubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-niyam-text mb-1">
                  Verification Status *
                </label>
                <select
                  value={verifyStatus}
                  onChange={(e) => setVerifyStatus(e.target.value as 'verified' | 'rejected')}
                  className="w-full text-xs border border-niyam-border rounded px-3 py-2 bg-white text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary"
                >
                  <option value="verified">Verified (Approved & Authentic)</option>
                  <option value="rejected">Rejected (Deficient / Invalid)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-niyam-text mb-1">
                  Verification Notes *
                </label>
                <textarea
                  required
                  rows={3}
                  placeholder="Record verification remarks, stamp checks, or reasons for rejection..."
                  value={verificationNotes}
                  onChange={(e) => setVerificationNotes(e.target.value)}
                  className="w-full text-xs border border-niyam-border rounded p-2 bg-white text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setIsVerifyModalOpen(false)}
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

      {/* MODAL 3: Submit Replacement Document for Renewal */}
      {isReplaceModalOpen && selectedDoc && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6 space-y-4 border border-niyam-border">
            <h3 className="text-lg font-bold text-niyam-text">Upload Replacement Certificate</h3>
            <p className="text-xs text-niyam-text-muted">
              Submit renewed certificate. The original document will be preserved in the audit trail.
            </p>

            {actionError && (
              <div className="p-3 rounded bg-red-50 text-red-700 text-xs flex items-center gap-2 border border-red-200">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{actionError}</span>
              </div>
            )}

            <form onSubmit={handleReplaceSubmit} className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-niyam-text mb-1">
                  Replacement Title *
                </label>
                <Input
                  required
                  value={replaceTitle}
                  onChange={(e) => setReplaceTitle(e.target.value)}
                />
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs font-medium text-niyam-text mb-1">
                    New Ref / Deed No.
                  </label>
                  <Input
                    placeholder="Reg #"
                    value={replaceDocNumber}
                    onChange={(e) => setReplaceDocNumber(e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-niyam-text mb-1">
                    Issuing Authority
                  </label>
                  <Input
                    value={replaceIssuingAuthority}
                    onChange={(e) => setReplaceIssuingAuthority(e.target.value)}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs font-medium text-niyam-text mb-1">
                    New Valid From
                  </label>
                  <input
                    type="date"
                    value={replaceValidFrom}
                    onChange={(e) => setReplaceValidFrom(e.target.value)}
                    className="w-full text-xs border border-niyam-border rounded px-2.5 py-1.5 bg-white text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-niyam-text mb-1">
                    New Valid Till
                  </label>
                  <input
                    type="date"
                    value={replaceValidTo}
                    onChange={(e) => setReplaceValidTo(e.target.value)}
                    className="w-full text-xs border border-niyam-border rounded px-2.5 py-1.5 bg-white text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-niyam-text mb-1">
                  Renewal Remarks
                </label>
                <textarea
                  rows={2}
                  value={replaceRemarks}
                  onChange={(e) => setReplaceRemarks(e.target.value)}
                  className="w-full text-xs border border-niyam-border rounded p-2 bg-white text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-niyam-text mb-1">
                  Replacement Document File (PDF, PNG, JPEG &le; 10MB) *
                </label>
                <input
                  type="file"
                  required
                  accept=".pdf,.png,.jpg,.jpeg"
                  onChange={(e) => setReplaceFile(e.target.files?.[0] || null)}
                  className="w-full text-xs border border-niyam-border rounded p-1.5 bg-white text-niyam-text file:mr-2 file:py-1 file:px-2 file:rounded file:border-0 file:text-xs file:bg-slate-100 file:text-niyam-text"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setIsReplaceModalOpen(false)}
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
                <Button type="submit" size="sm" variant="primary" disabled={isSubmitting}>
                  {isSubmitting ? 'Saving...' : 'Submit Replacement'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
