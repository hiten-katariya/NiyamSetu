import React, { useEffect, useState, useCallback } from 'react';
import {
  BellRing,
  AlertOctagon,
  CheckCircle,
  Clock,
  ExternalLink,
  CheckCheck,
  ShieldAlert,
  X,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { Badge } from '../../components/Badge';
import { Card } from '../../components/Card';
import { LoadingState } from '../../components/States';
import { useAuth } from '../../app/AuthContext';
import { api } from '../../lib/apiClient';
import {
  EscalationItem,
  NotificationItem,
  PaginatedResponse,
} from '../../types';

export const NotificationsPage: React.FC = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'notifications' | 'escalations'>('notifications');
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [escalations, setEscalations] = useState<EscalationItem[]>([]);
  const [statusFilter, setStatusFilter] = useState<'all' | 'unread'>('all');
  const [isLoading, setIsLoading] = useState(true);
  const [isResolving, setIsResolving] = useState<string | null>(null);
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [resolveError, setResolveError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const fetchNotifications = useCallback(async () => {
    try {
      const endpoint = statusFilter === 'unread' ? '/notifications?status=unread' : '/notifications';
      const res = await api.get<PaginatedResponse<NotificationItem>>(endpoint);
      setNotifications(res.data);
    } catch (err) {
      console.error('Failed to load notifications', err);
    }
  }, [statusFilter]);

  const fetchEscalations = useCallback(async () => {
    try {
      const res = await api.get<PaginatedResponse<EscalationItem>>('/escalations');
      setEscalations(res.data);
    } catch (err) {
      console.error('Failed to load escalations', err);
    }
  }, []);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    await Promise.all([fetchNotifications(), fetchEscalations()]);
    setIsLoading(false);
  }, [fetchNotifications, fetchEscalations]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleMarkRead = async (id: string) => {
    try {
      await api.post(`/notifications/${id}/read`, {});
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, status: 'read', read_at: new Date().toISOString() } : n))
      );
    } catch (err) {
      console.error('Failed to mark read', err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await api.post('/notifications/read-all', {});
      setNotifications((prev) =>
        prev.map((n) => ({ ...n, status: 'read', read_at: new Date().toISOString() }))
      );
      setActionSuccess('All notifications marked as read.');
      setTimeout(() => setActionSuccess(null), 3000);
    } catch (err) {
      console.error('Failed to mark all read', err);
    }
  };

  const handleResolveEscalation = async (escalationId: string) => {
    if (!resolutionNotes.trim()) {
      setResolveError('Resolution notes are required.');
      return;
    }
    setResolveError(null);
    try {
      const res = await api.post<EscalationItem>(`/escalations/${escalationId}/resolve`, {
        resolution_notes: resolutionNotes.trim(),
      });
      setEscalations((prev) =>
        prev.map((e) => (e.id === escalationId ? res : e))
      );
      setIsResolving(null);
      setResolutionNotes('');
      setActionSuccess('Escalation resolved successfully and audit log generated.');
      setTimeout(() => setActionSuccess(null), 4000);
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to resolve escalation.';
      setResolveError(errorMsg);
    }
  };

  const isOfficer = user && user.role !== 'institution_user';

  if (isLoading) {
    return <LoadingState message="Loading notifications & escalation alerts..." />;
  }

  const unreadCount = notifications.filter((n) => n.status === 'unread').length;
  const openEscalationCount = escalations.filter((e) => e.status === 'open').length;

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-niyam-border">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-niyam-text">
            Notifications & Escalation Alerts
          </h2>
          <p className="text-sm text-niyam-text-muted mt-1">
            Automated approaching deadline reminders and supervisory SLA escalations.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="info">Deduplicated Engine</Badge>
          <Badge variant="neutral">Tamper-Evident Audit</Badge>
        </div>
      </div>

      {actionSuccess && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded text-xs flex items-center gap-2">
          <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{actionSuccess}</span>
        </div>
      )}

      {/* Tabs */}
      <div className="flex items-center justify-between border-b border-niyam-border">
        <div className="flex items-center gap-4">
          <button
            onClick={() => setActiveTab('notifications')}
            className={`pb-3 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 ${
              activeTab === 'notifications'
                ? 'border-niyam-primary text-niyam-primary'
                : 'border-transparent text-niyam-text-muted hover:text-niyam-text'
            }`}
          >
            <BellRing className="w-4 h-4" />
            <span>Reminders & Notifications</span>
            {unreadCount > 0 && (
              <span className="px-1.5 py-0.5 rounded-full bg-niyam-primary text-white text-[10px]">
                {unreadCount}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('escalations')}
            className={`pb-3 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 ${
              activeTab === 'escalations'
                ? 'border-niyam-status-danger text-niyam-status-danger'
                : 'border-transparent text-niyam-text-muted hover:text-niyam-text'
            }`}
          >
            <AlertOctagon className="w-4 h-4" />
            <span>Statutory Escalations</span>
            {openEscalationCount > 0 && (
              <span className="px-1.5 py-0.5 rounded-full bg-niyam-status-danger text-white text-[10px]">
                {openEscalationCount}
              </span>
            )}
          </button>
        </div>

        {activeTab === 'notifications' && (
          <div className="flex items-center gap-2 pb-2">
            <button
              onClick={() => setStatusFilter(statusFilter === 'all' ? 'unread' : 'all')}
              className="text-xs px-2.5 py-1 rounded border border-niyam-border bg-niyam-surface hover:bg-niyam-surface-alt font-medium text-niyam-text"
            >
              {statusFilter === 'all' ? 'Show Unread Only' : 'Show All'}
            </button>
            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllRead}
                className="text-xs px-2.5 py-1 rounded bg-niyam-primary-tint text-niyam-primary hover:bg-niyam-primary hover:text-white transition-colors font-medium flex items-center gap-1"
              >
                <CheckCheck className="w-3.5 h-3.5" />
                <span>Mark All Read</span>
              </button>
            )}
          </div>
        )}
      </div>

      {/* Tab 1: Notifications */}
      {activeTab === 'notifications' && (
        <div className="space-y-3">
          {notifications.length === 0 ? (
            <div className="p-8 text-center bg-niyam-surface border border-niyam-border rounded-lg">
              <CheckCircle className="w-8 h-8 text-emerald-600 mx-auto mb-2" />
              <p className="text-sm font-semibold text-niyam-text">No Notifications</p>
              <p className="text-xs text-niyam-text-muted mt-1">
                You have no {statusFilter === 'unread' ? 'unread' : ''} reminders or notifications in your queue.
              </p>
            </div>
          ) : (
            notifications.map((notif) => (
              <Card
                key={notif.id}
                className={`transition-colors ${
                  notif.status === 'unread'
                    ? 'border-l-4 border-l-niyam-primary bg-niyam-primary-tint/10'
                    : 'border-l-4 border-l-slate-300'
                }`}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-3">
                    <BellRing
                      className={`w-5 h-5 shrink-0 mt-0.5 ${
                        notif.status === 'unread' ? 'text-niyam-primary' : 'text-slate-400'
                      }`}
                    />
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="text-sm font-semibold text-niyam-text">{notif.title}</h4>
                        {notif.status === 'unread' ? (
                          <Badge variant="info">Unread</Badge>
                        ) : (
                          <Badge variant="neutral">Read</Badge>
                        )}
                      </div>
                      <p className="text-xs text-niyam-text-muted mt-1 leading-relaxed">
                        {notif.body}
                      </p>
                      <div className="flex items-center gap-4 text-[11px] text-niyam-text-muted mt-2">
                        <span className="inline-flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {new Date(notif.sent_at).toLocaleString()}
                        </span>
                        {notif.application_id && (
                          <Link
                            to={`/applications/${notif.application_id}`}
                            className="inline-flex items-center gap-1 font-semibold text-niyam-primary hover:underline"
                          >
                            <span>Open Application</span>
                            <ExternalLink className="w-3 h-3" />
                          </Link>
                        )}
                      </div>
                    </div>
                  </div>

                  {notif.status === 'unread' && (
                    <button
                      onClick={() => handleMarkRead(notif.id)}
                      className="text-xs font-semibold text-niyam-primary hover:underline whitespace-nowrap cursor-pointer"
                    >
                      Mark as read
                    </button>
                  )}
                </div>
              </Card>
            ))
          )}
        </div>
      )}

      {/* Tab 2: Escalations */}
      {activeTab === 'escalations' && (
        <div className="space-y-4">
          {escalations.length === 0 ? (
            <div className="p-8 text-center bg-niyam-surface border border-niyam-border rounded-lg">
              <ShieldAlert className="w-8 h-8 text-emerald-600 mx-auto mb-2" />
              <p className="text-sm font-semibold text-niyam-text">No Active Escalations</p>
              <p className="text-xs text-niyam-text-muted mt-1">
                All application stages are within their statutory SLA deadlines.
              </p>
            </div>
          ) : (
            escalations.map((esc) => (
              <Card
                key={esc.id}
                className={`border-l-4 ${
                  esc.status === 'open' ? 'border-l-niyam-status-danger' : 'border-l-emerald-500'
                }`}
              >
                <div className="space-y-3">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <AlertOctagon
                        className={`w-5 h-5 ${
                          esc.status === 'open' ? 'text-niyam-status-danger' : 'text-emerald-600'
                        }`}
                      />
                      <h4 className="text-sm font-semibold text-niyam-text">
                        Tier {esc.level} Statutory SLA Breach
                      </h4>
                      <Badge variant={esc.status === 'open' ? 'danger' : 'success'}>
                        {esc.status === 'open' ? `Tier ${esc.level} Open` : 'Resolved'}
                      </Badge>
                    </div>

                    <div className="flex items-center gap-2">
                      {esc.application_id && (
                        <Link
                          to={`/applications/${esc.application_id}`}
                          className="text-xs font-semibold text-niyam-primary hover:underline inline-flex items-center gap-1"
                        >
                          <span>Case {esc.application_number ?? 'Details'}</span>
                          <ExternalLink className="w-3 h-3" />
                        </Link>
                      )}
                      {esc.status === 'open' && isOfficer && (
                        <button
                          onClick={() => {
                            setIsResolving(esc.id);
                            setResolutionNotes('');
                            setResolveError(null);
                          }}
                          className="px-2.5 py-1 text-xs font-semibold text-white bg-niyam-primary hover:bg-niyam-primary-dark rounded transition-colors"
                        >
                          Resolve SLA Breach
                        </button>
                      )}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs bg-niyam-surface-alt p-3 rounded border border-niyam-border">
                    <div>
                      <span className="text-niyam-text-muted font-medium">Institution:</span>{' '}
                      <span className="font-semibold text-niyam-text">
                        {esc.institution_name ?? 'N/A'}
                      </span>
                    </div>
                    <div>
                      <span className="text-niyam-text-muted font-medium">Triggered:</span>{' '}
                      <span className="text-niyam-text">
                        {new Date(esc.triggered_at).toLocaleString()}
                      </span>
                    </div>
                    {esc.assigned_to_name && (
                      <div>
                        <span className="text-niyam-text-muted font-medium">Supervisory Desk:</span>{' '}
                        <span className="text-niyam-text font-semibold">{esc.assigned_to_name}</span>
                      </div>
                    )}
                    {esc.resolved_at && (
                      <div>
                        <span className="text-niyam-text-muted font-medium">Resolved At:</span>{' '}
                        <span className="text-emerald-700 font-semibold">
                          {new Date(esc.resolved_at).toLocaleString()}
                        </span>
                      </div>
                    )}
                  </div>

                  {esc.resolution_notes && (
                    <div className="p-2.5 rounded bg-emerald-50 border border-emerald-200 text-xs">
                      <p className="font-semibold text-emerald-900">Resolution Notes & Audit Trail:</p>
                      <p className="text-emerald-800 mt-0.5">{esc.resolution_notes}</p>
                    </div>
                  )}

                  {/* Resolution Input Drawer */}
                  {isResolving === esc.id && (
                    <div className="mt-3 p-4 rounded border border-niyam-primary/30 bg-niyam-primary-tint/10 space-y-3">
                      <div className="flex items-center justify-between">
                        <h5 className="text-xs font-bold text-niyam-primary uppercase tracking-wide">
                          Resolve Escalation Tier {esc.level}
                        </h5>
                        <button
                          onClick={() => setIsResolving(null)}
                          className="text-niyam-text-muted hover:text-niyam-text"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>

                      {resolveError && (
                        <p className="text-xs text-rose-600 bg-rose-50 p-2 rounded border border-rose-200">
                          {resolveError}
                        </p>
                      )}

                      <div>
                        <label className="block text-xs font-semibold text-niyam-text mb-1">
                          Administrative Resolution Notes (Mandatory)
                        </label>
                        <textarea
                          rows={3}
                          value={resolutionNotes}
                          onChange={(e) => setResolutionNotes(e.target.value)}
                          placeholder="Detail the remedial actions taken, committee decision references, or administrative justifications..."
                          className="w-full text-xs p-2 rounded border border-niyam-border bg-white focus:outline-none focus:ring-1 focus:ring-niyam-primary text-niyam-text"
                        />
                      </div>

                      <div className="flex items-center justify-end gap-2">
                        <button
                          type="button"
                          onClick={() => setIsResolving(null)}
                          className="px-3 py-1.5 text-xs font-medium text-niyam-text bg-white border border-niyam-border rounded hover:bg-niyam-surface-alt"
                        >
                          Cancel
                        </button>
                        <button
                          type="button"
                          onClick={() => handleResolveEscalation(esc.id)}
                          className="px-3 py-1.5 text-xs font-bold text-white bg-niyam-primary hover:bg-niyam-primary-dark rounded transition-colors"
                        >
                          Confirm Resolution
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </Card>
            ))
          )}
        </div>
      )}
    </div>
  );
};
