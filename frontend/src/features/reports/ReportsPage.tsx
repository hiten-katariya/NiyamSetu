import React, { useState, useEffect, useCallback } from 'react';
import {
  Download,
  ShieldCheck,
  Filter,
  RefreshCw,
  CheckCircle,
  FileSpreadsheet,
} from 'lucide-react';
import { api } from '../../lib/apiClient';
import {
  ReportPreviewResponse,
  ReportTypeInfo,
  AuditVerificationResponse,
} from '../../types';
import { Badge } from '../../components/Badge';
import { Button } from '../../components/Button';
import { Card } from '../../components/Card';
import { LoadingState, EmptyState } from '../../components/States';

export const ReportsPage: React.FC = () => {
  const [reportTypes, setReportTypes] = useState<ReportTypeInfo[]>([]);
  const [selectedReportCode, setSelectedReportCode] = useState<string>('application_pendency');
  const [isLoadingTypes, setIsLoadingTypes] = useState(true);

  // Filters
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  // Preview Data
  const [previewData, setPreviewData] = useState<ReportPreviewResponse | null>(null);
  const [isLoadingPreview, setIsLoadingPreview] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);

  // Export state
  const [isExporting, setIsExporting] = useState(false);
  const [exportMessage, setExportMessage] = useState<string | null>(null);

  // Audit integrity state
  const [auditResult, setAuditResult] = useState<AuditVerificationResponse | null>(null);
  const [isVerifyingAudit, setIsVerifyingAudit] = useState(false);
  const [auditError, setAuditError] = useState<string | null>(null);

  // Load available report types
  useEffect(() => {
    api
      .get<ReportTypeInfo[]>('/reports/types')
      .then((types) => {
        setReportTypes(types);
        if (types.length > 0) {
          setSelectedReportCode(types[0].code);
        }
      })
      .catch((err) => console.error('Failed to load report types', err))
      .finally(() => setIsLoadingTypes(false));
  }, []);

  const loadPreview = useCallback(
    async (page = 1) => {
      if (!selectedReportCode) return;
      setIsLoadingPreview(true);
      setPreviewError(null);
      try {
        const data = await api.post<ReportPreviewResponse>('/reports/preview', {
          report_type: selectedReportCode,
          date_from: dateFrom || undefined,
          date_to: dateTo || undefined,
          status: statusFilter || undefined,
          page,
          page_size: 25,
        });
        setPreviewData(data);
        setCurrentPage(page);
      } catch (err: unknown) {
        setPreviewError(err instanceof Error ? err.message : 'Failed to preview report');
      } finally {
        setIsLoadingPreview(false);
      }
    },
    [selectedReportCode, dateFrom, dateTo, statusFilter]
  );

  useEffect(() => {
    if (selectedReportCode) {
      loadPreview(1);
    }
  }, [selectedReportCode, loadPreview]);

  const handleExportCsv = async () => {
    if (isExporting || !selectedReportCode) return;
    setIsExporting(true);
    setExportMessage(null);
    try {
      // Trigger export via fetch blob to download safely
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
      const res = await fetch(`${API_BASE_URL}/reports/export`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          report_type: selectedReportCode,
          date_from: dateFrom || undefined,
          date_to: dateTo || undefined,
          status: statusFilter || undefined,
          export_format: 'csv',
        }),
      });

      if (!res.ok) {
        throw new Error(`Export failed with HTTP ${res.status}`);
      }

      const blob = await res.blob();
      const disposition = res.headers.get('Content-Disposition');
      let filename = `niyamsetu_${selectedReportCode}.csv`;
      if (disposition && disposition.includes('filename=')) {
        const match = disposition.match(/filename="?([^";]+)"?/);
        if (match && match[1]) filename = match[1];
      }

      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(downloadUrl);

      setExportMessage(`Successfully exported ${filename}. Tamper-evident audit log recorded.`);
    } catch (err: unknown) {
      setExportMessage(err instanceof Error ? err.message : 'Export failed');
    } finally {
      setIsExporting(false);
    }
  };

  const handleVerifyAuditChain = async () => {
    setIsVerifyingAudit(true);
    setAuditError(null);
    try {
      const data = await api.get<AuditVerificationResponse>('/audit/verify-integrity');
      setAuditResult(data);
    } catch (err: unknown) {
      setAuditError(err instanceof Error ? err.message : 'Audit chain verification failed');
    } finally {
      setIsVerifyingAudit(false);
    }
  };

  const activeReport = reportTypes.find((r) => r.code === selectedReportCode);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-niyam-border">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-niyam-text">
            Reporting Centre & Cryptographic Audit
          </h2>
          <p className="text-sm text-niyam-text-muted mt-1">
            Generate permission-scoped statutory reports, export formula-safe Excel/CSV files, and verify audit integrity.
          </p>
        </div>
        <div className="flex items-center gap-2">
          {auditResult ? (
            <Badge variant={auditResult.is_valid ? 'success' : 'danger'}>
              {auditResult.is_valid ? `Chain Verified (${auditResult.verified_count} logs)` : 'Chain Compromised'}
            </Badge>
          ) : (
            <Badge variant="neutral">SHA-256 Audit Chaining</Badge>
          )}
        </div>
      </div>

      {/* Top Cards: Report Selection & Audit Integrity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Report Selector Card (2 cols) */}
        <Card className="lg:col-span-2" title="Select Statutory Report">
          <p className="text-xs text-niyam-text-muted mb-3">
            Choose from standard approval workflow reports. Data is computed live and scoped to your jurisdiction.
          </p>

          {isLoadingTypes ? (
            <div className="py-6 text-center text-xs text-niyam-text-muted">Loading available reports...</div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
              {reportTypes.map((rt) => (
                <button
                  key={rt.code}
                  onClick={() => setSelectedReportCode(rt.code)}
                  className={`text-left p-3 rounded-lg border transition-all cursor-pointer ${
                    selectedReportCode === rt.code
                      ? 'border-niyam-primary bg-blue-50/50 ring-1 ring-niyam-primary'
                      : 'border-niyam-border bg-white hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <FileSpreadsheet
                      className={`w-4 h-4 ${
                        selectedReportCode === rt.code ? 'text-niyam-primary' : 'text-niyam-text-muted'
                      }`}
                    />
                    <span className="font-semibold text-xs text-niyam-text">{rt.name}</span>
                  </div>
                  <p className="text-[11px] text-niyam-text-muted mt-1 line-clamp-2">
                    {rt.description}
                  </p>
                </button>
              ))}
            </div>
          )}

          {activeReport && (
            <div className="mt-3 pt-2 border-t border-niyam-border text-[11px] text-niyam-text-muted">
              Current selection: <strong className="text-niyam-text">{activeReport.name}</strong> &mdash; {activeReport.description}
            </div>
          )}
        </Card>

        {/* Cryptographic Audit Verification Card (1 col) */}
        <Card title="Audit Chain Integrity">
          <div className="p-3.5 rounded-lg bg-slate-50 border border-niyam-border space-y-2.5">
            <div className="flex items-start gap-2.5">
              <ShieldCheck className="w-5 h-5 text-niyam-primary shrink-0 mt-0.5" />
              <div className="text-xs text-niyam-text space-y-1">
                <p className="font-semibold text-niyam-text">SHA-256 Append-Only Chain</p>
                <p className="text-niyam-text-muted text-[11px]">
                  All state transitions, report determinations, and export actions are chained to previous hashes.
                </p>
              </div>
            </div>

            {auditResult && (
              <div
                className={`p-2.5 rounded text-xs flex items-center gap-2 ${
                  auditResult.is_valid
                    ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                    : 'bg-rose-50 text-rose-800 border border-rose-200'
                }`}
              >
                <CheckCircle className="w-4 h-4 shrink-0" />
                <span>
                  <strong>Integrity Verified:</strong> {auditResult.verified_count} entries verified intact.
                </span>
              </div>
            )}

            {auditError && (
              <div className="p-2 rounded bg-rose-50 text-rose-700 text-xs">
                {auditError}
              </div>
            )}

            <Button
              size="sm"
              variant="outline"
              className="w-full"
              onClick={handleVerifyAuditChain}
              disabled={isVerifyingAudit}
            >
              <RefreshCw className={`w-3.5 h-3.5 mr-1 ${isVerifyingAudit ? 'animate-spin' : ''}`} />
              {isVerifyingAudit ? 'Verifying Hashes...' : 'Run Cryptographic Audit'}
            </Button>
          </div>
        </Card>
      </div>

      {/* Filter and Action Bar */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between bg-niyam-surface p-3.5 rounded-lg border border-niyam-border">
        <div className="flex items-center gap-2 flex-wrap w-full sm:w-auto">
          <Filter className="w-4 h-4 text-niyam-text-muted shrink-0" />
          <span className="text-xs text-niyam-text-muted font-medium">Filter Dates:</span>

          <input
            type="date"
            placeholder="From Date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            className="text-xs border border-niyam-border rounded px-2.5 py-1.5 bg-white text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary"
          />
          <span className="text-xs text-niyam-text-muted">to</span>
          <input
            type="date"
            placeholder="To Date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            className="text-xs border border-niyam-border rounded px-2.5 py-1.5 bg-white text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary"
          />

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs border border-niyam-border rounded px-2.5 py-1.5 bg-white text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary"
          >
            <option value="">All Statuses</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
            <option value="scheduled">Scheduled</option>
            <option value="conducted">Conducted</option>
            <option value="pending">Pending</option>
            <option value="overdue">Overdue</option>
          </select>

          <Button size="sm" variant="outline" onClick={() => loadPreview(1)} disabled={isLoadingPreview}>
            <RefreshCw className={`w-3.5 h-3.5 mr-1 ${isLoadingPreview ? 'animate-spin' : ''}`} />
            Apply Filters
          </Button>
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
          <Button
            size="sm"
            variant="primary"
            onClick={handleExportCsv}
            disabled={isExporting || isLoadingPreview}
          >
            <Download className="w-3.5 h-3.5 mr-1" />
            {isExporting ? 'Generating...' : 'Export to CSV'}
          </Button>
        </div>
      </div>

      {exportMessage && (
        <div className="p-3 rounded-lg bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs flex items-center justify-between">
          <span>{exportMessage}</span>
          <button onClick={() => setExportMessage(null)} className="font-bold cursor-pointer text-emerald-900 ml-2">
            &times;
          </button>
        </div>
      )}

      {/* Security Notice: Spreadsheet Formula Injection Mitigation */}
      <div className="flex items-start gap-2.5 p-3 rounded-lg bg-slate-50 border border-niyam-border text-[11px] text-niyam-text-muted">
        <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
        <div>
          <strong className="text-niyam-text">Safe Export Protection:</strong> All generated CSV files are sanitized
          against spreadsheet formula injection (cells beginning with =, +, -, @ are escaped with a leading quote). Files
          are delivered with UTF-8 BOM encoding for seamless Microsoft Excel compatibility.
        </div>
      </div>

      {/* Live Data Preview Table */}
      <Card
        title={previewData ? `${previewData.report_title} (Preview)` : 'Report Data Preview'}
        subtitle={
          previewData
            ? `Displaying page ${previewData.page} of ${Math.ceil(previewData.total_rows / previewData.page_size) || 1} (${previewData.total_rows} total matching records)`
            : 'Live tabular preview'
        }
      >
        {isLoadingPreview ? (
          <LoadingState message="Generating live report preview..." />
        ) : previewError ? (
          <div className="p-4 rounded bg-rose-50 text-rose-700 text-xs">{previewError}</div>
        ) : !previewData || previewData.rows.length === 0 ? (
          <EmptyState
            title="No records found"
            description="No matching records found for the selected report type and applied filters."
          />
        ) : (
          <div className="space-y-4 pt-2">
            <div className="overflow-x-auto border border-niyam-border rounded-lg">
              <table className="min-w-full divide-y divide-niyam-border text-xs">
                <thead className="bg-slate-50 text-niyam-text font-semibold">
                  <tr>
                    {previewData.columns.map((col) => (
                      <th key={col.key} className="px-3 py-2.5 text-left whitespace-nowrap">
                        {col.label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-niyam-border bg-white text-niyam-text">
                  {previewData.rows.map((row, rowIdx) => (
                    <tr key={rowIdx} className="hover:bg-slate-50/80 transition-colors">
                      {previewData.columns.map((col) => {
                        const val = row[col.key];
                        return (
                          <td key={col.key} className="px-3 py-2 whitespace-nowrap">
                            {val === 'YES' || val === 'Breached' || val === 'Expired' || val === 'Overdue' ? (
                              <Badge variant="danger">{String(val)}</Badge>
                            ) : val === 'Due Soon' || val === 'Expiring Soon' ? (
                              <Badge variant="warning">{String(val)}</Badge>
                            ) : val === 'COMPLETED' || val === 'VERIFIED' || val === 'On Track' || val === 'Valid' ? (
                              <Badge variant="success">{String(val)}</Badge>
                            ) : val !== null && val !== undefined ? (
                              String(val)
                            ) : (
                              '—'
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            <div className="flex items-center justify-between text-xs text-niyam-text-muted pt-2">
              <span>
                Showing {(previewData.page - 1) * previewData.page_size + 1} to{' '}
                {Math.min(previewData.page * previewData.page_size, previewData.total_rows)} of{' '}
                {previewData.total_rows} entries
              </span>

              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => loadPreview(currentPage - 1)}
                  disabled={currentPage <= 1 || isLoadingPreview}
                >
                  Previous
                </Button>
                <span className="font-semibold text-niyam-text px-2">Page {currentPage}</span>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => loadPreview(currentPage + 1)}
                  disabled={currentPage * previewData.page_size >= previewData.total_rows || isLoadingPreview}
                >
                  Next
                </Button>
              </div>
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};
