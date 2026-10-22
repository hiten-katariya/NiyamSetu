import React, { useState, useEffect } from 'react';
import { Badge } from '../../components/Badge';
import { Button } from '../../components/Button';
import { Card } from '../../components/Card';
import { Input } from '../../components/Input';
import { api } from '../../lib/apiClient';
import {
  AuditLogItem,
  ConfigVersionItem,
  EscalationRuleItem,
  HolidayItem,
  MessageTemplateItem,
  ReminderRuleItem,
  RouteStage,
  RouteType,
  User,
  UserRole,
  WorkerMonitoringResponse,
} from '../../types';
import {
  Shield,
  UserCheck,
  GitBranch,
  Calendar,
  Mail,
  History,
  Activity,
  Search,
  Sliders,
  Plus,
  Trash2,
  Edit,
} from 'lucide-react';
import { LoadingState, EmptyState } from '../../components/States';

const ALL_ROLES: UserRole[] = [
  'admin',
  'system_admin',
  'institution_user',
  'scrutiny_officer',
  'regional_officer',
  'bureau_officer',
  'committee_member',
  'senior_authority',
];

type AdminTab =
  | 'users'
  | 'routes'
  | 'rules'
  | 'holidays'
  | 'templates'
  | 'versions'
  | 'monitoring'
  | 'audit';

export const AdminConfigPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<AdminTab>('users');

  // Tab 1: Users
  const [users, setUsers] = useState<User[]>([]);
  const [isLoadingUsers, setIsLoadingUsers] = useState(false);
  const [updatingUserId, setUpdatingUserId] = useState<string | null>(null);

  // Tab 2: Route Types & Stages
  const [routeTypes, setRouteTypes] = useState<RouteType[]>([]);
  const [selectedStage, setSelectedStage] = useState<RouteStage | null>(null);
  const [isEditStageModalOpen, setIsEditStageModalOpen] = useState(false);
  const [editTimelineDays, setEditTimelineDays] = useState<number>(10);
  const [editDayType, setEditDayType] = useState<string>('working_days');
  const [stageChangeReason, setStageChangeReason] = useState<string>('');

  // Tab 3: Reminder & Escalation Rules
  const [reminderRules, setReminderRules] = useState<ReminderRuleItem[]>([]);
  const [escalationRules, setEscalationRules] = useState<EscalationRuleItem[]>([]);
  const [isRuleModalOpen, setIsRuleModalOpen] = useState(false);
  const [ruleType, setRuleType] = useState<'reminder' | 'escalation'>('reminder');
  const [ruleName, setRuleName] = useState('');
  const [ruleTarget, setRuleTarget] = useState('application');
  const [ruleDays, setRuleDays] = useState<number>(3);
  const [ruleLevel, setRuleLevel] = useState<number>(1);
  const [ruleRoles, setRuleRoles] = useState('scrutiny_officer');
  const [ruleChangeReason, setRuleChangeReason] = useState('');

  // Tab 4: Holidays
  const [holidays, setHolidays] = useState<HolidayItem[]>([]);
  const [isHolidayModalOpen, setIsHolidayModalOpen] = useState(false);
  const [holidayName, setHolidayName] = useState('');
  const [holidayDate, setHolidayDate] = useState('');
  const [holidayChangeReason, setHolidayChangeReason] = useState('');

  // Tab 5: Message Templates
  const [templates, setTemplates] = useState<MessageTemplateItem[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<MessageTemplateItem | null>(null);
  const [templateSubject, setTemplateSubject] = useState('');
  const [templateBody, setTemplateBody] = useState('');
  const [templateReason, setTemplateReason] = useState('');
  const [isTemplateModalOpen, setIsTemplateModalOpen] = useState(false);

  // Tab 6: Version History
  const [configVersions, setConfigVersions] = useState<ConfigVersionItem[]>([]);

  // Tab 7: Worker Health & Operational Monitoring
  const [workerHealth, setWorkerHealth] = useState<WorkerMonitoringResponse | null>(null);

  // Tab 8: Audit Logs Explorer
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);
  const [auditPage, setAuditPage] = useState<number>(1);
  const [auditTotal, setAuditTotal] = useState<number>(0);
  const [auditFilterAction, setAuditFilterAction] = useState<string>('');
  const [auditFilterType, setAuditFilterType] = useState<string>('');

  // General Status & Errors
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchUsers = async () => {
    setIsLoadingUsers(true);
    try {
      const data = await api.get<User[]>('/admin/users');
      setUsers(data);
    } catch {
      setErrorMessage('Failed to load system users.');
    } finally {
      setIsLoadingUsers(false);
    }
  };

  const fetchRoutes = async () => {
    try {
      const data = await api.get<RouteType[]>('/admin/route-types');
      setRouteTypes(data);
    } catch {
      setErrorMessage('Failed to load workflow route types.');
    }
  };

  const fetchRules = async () => {
    try {
      const [rems, escs] = await Promise.all([
        api.get<ReminderRuleItem[]>('/admin/rules/reminders'),
        api.get<EscalationRuleItem[]>('/admin/rules/escalations'),
      ]);
      setReminderRules(rems);
      setEscalationRules(escs);
    } catch {
      setErrorMessage('Failed to load reminder and escalation rules.');
    }
  };

  const fetchHolidays = async () => {
    try {
      const data = await api.get<HolidayItem[]>('/admin/holidays');
      setHolidays(data);
    } catch {
      setErrorMessage('Failed to load holiday calendar.');
    }
  };

  const fetchTemplates = async () => {
    try {
      const data = await api.get<MessageTemplateItem[]>('/admin/message-templates');
      setTemplates(data);
    } catch {
      setErrorMessage('Failed to load message templates.');
    }
  };

  const fetchVersions = async () => {
    try {
      const data = await api.get<ConfigVersionItem[]>('/admin/config/versions');
      setConfigVersions(data);
    } catch {
      setErrorMessage('Failed to load configuration version history.');
    }
  };

  const fetchMonitoring = async () => {
    try {
      const data = await api.get<WorkerMonitoringResponse>('/monitoring/worker');
      setWorkerHealth(data);
    } catch {
      setErrorMessage('Failed to load worker monitoring metrics.');
    }
  };

  const fetchAuditLogs = async (page = 1) => {
    try {
      const q = new URLSearchParams();
      q.set('page', String(page));
      q.set('page_size', '20');
      if (auditFilterAction) q.set('action', auditFilterAction);
      if (auditFilterType) q.set('entity_type', auditFilterType);

      const res = await api.get<any>(`/audit/logs?${q.toString()}`);
      setAuditLogs(res.data);
      setAuditTotal(res.meta.total);
      setAuditPage(page);
    } catch {
      setErrorMessage('Failed to load audit logs.');
    }
  };

  useEffect(() => {
    if (activeTab === 'users') fetchUsers();
    else if (activeTab === 'routes') fetchRoutes();
    else if (activeTab === 'rules') fetchRules();
    else if (activeTab === 'holidays') fetchHolidays();
    else if (activeTab === 'templates') fetchTemplates();
    else if (activeTab === 'versions') fetchVersions();
    else if (activeTab === 'monitoring') fetchMonitoring();
    else if (activeTab === 'audit') fetchAuditLogs(1);
  }, [activeTab]);

  const handleRoleChange = async (userId: string, newRole: UserRole) => {
    setUpdatingUserId(userId);
    setStatusMessage(null);
    setErrorMessage(null);
    try {
      await api.patch(`/admin/users/${userId}/role`, { role: newRole });
      setStatusMessage('User role updated successfully.');
      await fetchUsers();
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : 'Failed to update user role.');
    } finally {
      setUpdatingUserId(null);
    }
  };

  const handleStatusToggle = async (userId: string, currentStatus: boolean) => {
    setUpdatingUserId(userId);
    setStatusMessage(null);
    setErrorMessage(null);
    try {
      await api.patch(`/admin/users/${userId}/status`, { is_active: !currentStatus });
      setStatusMessage(`User account successfully ${!currentStatus ? 'activated' : 'deactivated'}.`);
      await fetchUsers();
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : 'Failed to update account status.');
    } finally {
      setUpdatingUserId(null);
    }
  };

  const handleOpenEditStage = (stage: RouteStage) => {
    setSelectedStage(stage);
    setEditTimelineDays(stage.timeline_days);
    setEditDayType(stage.day_type);
    setStageChangeReason('');
    setIsEditStageModalOpen(true);
  };

  const handleSaveStage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedStage) return;
    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      await api.patch(`/admin/stages/${selectedStage.id}`, {
        timeline_days: editTimelineDays,
        day_type: editDayType,
        change_reason: stageChangeReason,
      });
      setIsEditStageModalOpen(false);
      setStatusMessage(`Stage ${selectedStage.stage_name} updated successfully.`);
      await fetchRoutes();
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : 'Failed to update stage');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCreateRule = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      const roles = ruleRoles.split(',').map((r) => r.trim()).filter(Boolean);
      if (ruleType === 'reminder') {
        await api.post('/admin/rules/reminders', {
          name: ruleName,
          target_type: ruleTarget,
          days_before_due: ruleDays,
          recipient_roles: roles,
          is_active: true,
          change_reason: ruleChangeReason,
        });
      } else {
        await api.post('/admin/rules/escalations', {
          name: ruleName,
          target_type: ruleTarget,
          level: ruleLevel,
          days_after_due: ruleDays,
          recipient_roles: roles,
          is_active: true,
          change_reason: ruleChangeReason,
        });
      }
      setIsRuleModalOpen(false);
      setStatusMessage('Rule created successfully.');
      await fetchRules();
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : 'Failed to create rule');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteReminderRule = async (id: string, name: string) => {
    const reason = window.prompt(`Enter mandatory reason to delete reminder rule "${name}":`);
    if (!reason || reason.trim().length < 3) return;
    try {
      await api.delete(`/admin/rules/reminders/${id}?change_reason=${encodeURIComponent(reason)}`);
      setStatusMessage('Reminder rule deleted successfully.');
      await fetchRules();
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : 'Failed to delete rule');
    }
  };

  const handleDeleteEscalationRule = async (id: string, name: string) => {
    const reason = window.prompt(`Enter mandatory reason to delete escalation rule "${name}":`);
    if (!reason || reason.trim().length < 3) return;
    try {
      await api.delete(`/admin/rules/escalations/${id}?change_reason=${encodeURIComponent(reason)}`);
      setStatusMessage('Escalation rule deleted successfully.');
      await fetchRules();
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : 'Failed to delete rule');
    }
  };

  const handleCreateHoliday = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      await api.post('/admin/holidays', {
        name: holidayName,
        holiday_date: holidayDate,
        change_reason: holidayChangeReason,
      });
      setIsHolidayModalOpen(false);
      setStatusMessage('Holiday registered successfully.');
      await fetchHolidays();
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : 'Failed to create holiday');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteHoliday = async (id: string, name: string) => {
    const reason = window.prompt(`Enter mandatory reason to delete holiday "${name}":`);
    if (!reason || reason.trim().length < 3) return;
    try {
      await api.delete(`/admin/holidays/${id}?change_reason=${encodeURIComponent(reason)}`);
      setStatusMessage('Holiday deleted successfully.');
      await fetchHolidays();
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : 'Failed to delete holiday');
    }
  };

  const handleOpenEditTemplate = (tpl: MessageTemplateItem) => {
    setSelectedTemplate(tpl);
    setTemplateSubject(tpl.subject_template);
    setTemplateBody(tpl.body_template);
    setTemplateReason('');
    setIsTemplateModalOpen(true);
  };

  const handleSaveTemplate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTemplate) return;
    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      await api.put(`/admin/message-templates/${selectedTemplate.id}`, {
        subject_template: templateSubject,
        body_template: templateBody,
        is_active: selectedTemplate.is_active,
        change_reason: templateReason,
      });
      setIsTemplateModalOpen(false);
      setStatusMessage('Message template updated successfully.');
      await fetchTemplates();
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : 'Failed to update template');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-niyam-border">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-niyam-text">
            Admin System Configuration & Operational Control
          </h2>
          <p className="text-sm text-niyam-text-muted mt-1">
            Configure approval routes, stage timelines, deadline rules, holiday calendars, inspect version history, and monitor worker health.
          </p>
        </div>
        <Badge variant="warning">Database Managed & Versioned</Badge>
      </div>

      {statusMessage && (
        <div className="p-3 bg-emerald-50 text-emerald-800 text-xs rounded-lg border border-emerald-200 flex items-center justify-between">
          <span>{statusMessage}</span>
          <button onClick={() => setStatusMessage(null)} className="font-bold cursor-pointer text-emerald-900 ml-2">
            &times;
          </button>
        </div>
      )}

      {errorMessage && (
        <div className="p-3 bg-rose-50 text-rose-800 text-xs rounded-lg border border-rose-200 flex items-center justify-between">
          <span>{errorMessage}</span>
          <button onClick={() => setErrorMessage(null)} className="font-bold cursor-pointer text-rose-900 ml-2">
            &times;
          </button>
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex items-center gap-1.5 border-b border-niyam-border overflow-x-auto pb-1">
        <button
          onClick={() => setActiveTab('users')}
          className={`px-3 py-2 text-xs font-semibold rounded-t-lg transition-colors cursor-pointer flex items-center gap-1.5 whitespace-nowrap ${
            activeTab === 'users'
              ? 'bg-niyam-primary text-white'
              : 'text-niyam-text-muted hover:text-niyam-text hover:bg-slate-100'
          }`}
        >
          <UserCheck className="w-3.5 h-3.5" />
          User Roles
        </button>

        <button
          onClick={() => setActiveTab('routes')}
          className={`px-3 py-2 text-xs font-semibold rounded-t-lg transition-colors cursor-pointer flex items-center gap-1.5 whitespace-nowrap ${
            activeTab === 'routes'
              ? 'bg-niyam-primary text-white'
              : 'text-niyam-text-muted hover:text-niyam-text hover:bg-slate-100'
          }`}
        >
          <GitBranch className="w-3.5 h-3.5" />
          Workflow Routes
        </button>

        <button
          onClick={() => setActiveTab('rules')}
          className={`px-3 py-2 text-xs font-semibold rounded-t-lg transition-colors cursor-pointer flex items-center gap-1.5 whitespace-nowrap ${
            activeTab === 'rules'
              ? 'bg-niyam-primary text-white'
              : 'text-niyam-text-muted hover:text-niyam-text hover:bg-slate-100'
          }`}
        >
          <Sliders className="w-3.5 h-3.5" />
          Reminder & Escalation Rules
        </button>

        <button
          onClick={() => setActiveTab('holidays')}
          className={`px-3 py-2 text-xs font-semibold rounded-t-lg transition-colors cursor-pointer flex items-center gap-1.5 whitespace-nowrap ${
            activeTab === 'holidays'
              ? 'bg-niyam-primary text-white'
              : 'text-niyam-text-muted hover:text-niyam-text hover:bg-slate-100'
          }`}
        >
          <Calendar className="w-3.5 h-3.5" />
          Holiday Calendars
        </button>

        <button
          onClick={() => setActiveTab('templates')}
          className={`px-3 py-2 text-xs font-semibold rounded-t-lg transition-colors cursor-pointer flex items-center gap-1.5 whitespace-nowrap ${
            activeTab === 'templates'
              ? 'bg-niyam-primary text-white'
              : 'text-niyam-text-muted hover:text-niyam-text hover:bg-slate-100'
          }`}
        >
          <Mail className="w-3.5 h-3.5" />
          Message Templates
        </button>

        <button
          onClick={() => setActiveTab('versions')}
          className={`px-3 py-2 text-xs font-semibold rounded-t-lg transition-colors cursor-pointer flex items-center gap-1.5 whitespace-nowrap ${
            activeTab === 'versions'
              ? 'bg-niyam-primary text-white'
              : 'text-niyam-text-muted hover:text-niyam-text hover:bg-slate-100'
          }`}
        >
          <History className="w-3.5 h-3.5" />
          Version History
        </button>

        <button
          onClick={() => setActiveTab('monitoring')}
          className={`px-3 py-2 text-xs font-semibold rounded-t-lg transition-colors cursor-pointer flex items-center gap-1.5 whitespace-nowrap ${
            activeTab === 'monitoring'
              ? 'bg-niyam-primary text-white'
              : 'text-niyam-text-muted hover:text-niyam-text hover:bg-slate-100'
          }`}
        >
          <Activity className="w-3.5 h-3.5" />
          Worker Health
        </button>

        <button
          onClick={() => setActiveTab('audit')}
          className={`px-3 py-2 text-xs font-semibold rounded-t-lg transition-colors cursor-pointer flex items-center gap-1.5 whitespace-nowrap ${
            activeTab === 'audit'
              ? 'bg-niyam-primary text-white'
              : 'text-niyam-text-muted hover:text-niyam-text hover:bg-slate-100'
          }`}
        >
          <Shield className="w-3.5 h-3.5" />
          Audit Explorer
        </button>
      </div>

      {/* =====================================================================
          TAB 1: USERS & RBAC GOVERNANCE
          ===================================================================== */}
      {activeTab === 'users' && (
        <Card
          title="User Governance & RBAC Assignment"
          subtitle="Manage active accounts and assign roles. Role changes revoke active sessions immediately."
        >
          {isLoadingUsers ? (
            <LoadingState message="Loading system users..." />
          ) : users.length === 0 ? (
            <EmptyState title="No users found" description="No registered system users found." />
          ) : (
            <div className="overflow-x-auto border border-niyam-border rounded-lg mt-3">
              <table className="min-w-full divide-y divide-niyam-border text-xs">
                <thead className="bg-slate-50 text-niyam-text font-semibold">
                  <tr>
                    <th className="px-3 py-2.5 text-left">Full Name</th>
                    <th className="px-3 py-2.5 text-left">Email Address</th>
                    <th className="px-3 py-2.5 text-left">Current Role</th>
                    <th className="px-3 py-2.5 text-left">Status</th>
                    <th className="px-3 py-2.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-niyam-border bg-white text-niyam-text">
                  {users.map((u) => (
                    <tr key={u.id} className="hover:bg-slate-50 transition-colors">
                      <td className="px-3 py-2 font-medium">{u.full_name}</td>
                      <td className="px-3 py-2 text-niyam-text-muted">{u.email}</td>
                      <td className="px-3 py-2">
                        <select
                          value={u.role}
                          disabled={updatingUserId === u.id}
                          onChange={(e) => handleRoleChange(u.id, e.target.value as UserRole)}
                          className="text-xs border border-niyam-border rounded px-2 py-1 bg-white text-niyam-text"
                        >
                          {ALL_ROLES.map((r) => (
                            <option key={r} value={r}>
                              {r.replace(/_/g, ' ').toUpperCase()}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td className="px-3 py-2">
                        <Badge variant={u.is_active ? 'success' : 'danger'}>
                          {u.is_active ? 'ACTIVE' : 'DEACTIVATED'}
                        </Badge>
                      </td>
                      <td className="px-3 py-2 text-right">
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={updatingUserId === u.id}
                          onClick={() => handleStatusToggle(u.id, u.is_active)}
                        >
                          {u.is_active ? 'Deactivate' : 'Activate'}
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      {/* =====================================================================
          TAB 2: WORKFLOW ROUTES & STAGES
          ===================================================================== */}
      {activeTab === 'routes' && (
        <div className="space-y-4">
          {routeTypes.map((rt) => (
            <Card
              key={rt.id}
              title={`${rt.name} (${rt.code})`}
              subtitle={`Version ${rt.current_version} • Applications pin this version upon inception`}
            >
              <div className="overflow-x-auto border border-niyam-border rounded-lg mt-3">
                <table className="min-w-full divide-y divide-niyam-border text-xs">
                  <thead className="bg-slate-50 text-niyam-text font-semibold">
                    <tr>
                      <th className="px-3 py-2 text-left">Seq</th>
                      <th className="px-3 py-2 text-left">Stage Name</th>
                      <th className="px-3 py-2 text-left">Stage Code</th>
                      <th className="px-3 py-2 text-left">Required Role</th>
                      <th className="px-3 py-2 text-left">Timeline Days</th>
                      <th className="px-3 py-2 text-left">Day Type</th>
                      <th className="px-3 py-2 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-niyam-border bg-white text-niyam-text">
                    {rt.stages.map((stg) => (
                      <tr key={stg.id} className="hover:bg-slate-50">
                        <td className="px-3 py-2 font-bold">{stg.sequence}</td>
                        <td className="px-3 py-2 font-medium">{stg.stage_name}</td>
                        <td className="px-3 py-2 text-niyam-text-muted">{stg.stage_code}</td>
                        <td className="px-3 py-2 capitalize">{stg.required_role.replace(/_/g, ' ')}</td>
                        <td className="px-3 py-2">
                          <Badge variant="neutral">{stg.timeline_days} Days</Badge>
                        </td>
                        <td className="px-3 py-2 capitalize">{stg.day_type.replace(/_/g, ' ')}</td>
                        <td className="px-3 py-2 text-right">
                          <Button size="sm" variant="outline" onClick={() => handleOpenEditStage(stg)}>
                            <Edit className="w-3 h-3 mr-1" />
                            Configure
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* =====================================================================
          TAB 3: REMINDER & ESCALATION RULES
          ===================================================================== */}
      {activeTab === 'rules' && (
        <div className="space-y-6">
          <div className="flex justify-end gap-2">
            <Button
              size="sm"
              variant="primary"
              onClick={() => {
                setRuleType('reminder');
                setRuleName('');
                setRuleTarget('application');
                setRuleDays(3);
                setRuleRoles('scrutiny_officer');
                setRuleChangeReason('');
                setIsRuleModalOpen(true);
              }}
            >
              <Plus className="w-3.5 h-3.5 mr-1" />
              Add Reminder Rule
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setRuleType('escalation');
                setRuleName('');
                setRuleTarget('application');
                setRuleDays(2);
                setRuleLevel(1);
                setRuleRoles('regional_officer');
                setRuleChangeReason('');
                setIsRuleModalOpen(true);
              }}
            >
              <Plus className="w-3.5 h-3.5 mr-1" />
              Add Escalation Rule
            </Button>
          </div>

          <Card title="Configurable Reminder Rules" subtitle="Automated alerts dispatched prior to SLA due dates">
            <div className="overflow-x-auto border border-niyam-border rounded-lg mt-3">
              <table className="min-w-full divide-y divide-niyam-border text-xs">
                <thead className="bg-slate-50 text-niyam-text font-semibold">
                  <tr>
                    <th className="px-3 py-2 text-left">Rule Name</th>
                    <th className="px-3 py-2 text-left">Target Entity</th>
                    <th className="px-3 py-2 text-left">Offset</th>
                    <th className="px-3 py-2 text-left">Recipient Roles</th>
                    <th className="px-3 py-2 text-left">Status</th>
                    <th className="px-3 py-2 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-niyam-border bg-white text-niyam-text">
                  {reminderRules.map((r) => (
                    <tr key={r.id} className="hover:bg-slate-50">
                      <td className="px-3 py-2 font-medium">{r.name}</td>
                      <td className="px-3 py-2 capitalize">{r.target_type}</td>
                      <td className="px-3 py-2">
                        <Badge variant="warning">{r.days_before_due} Days Before Due</Badge>
                      </td>
                      <td className="px-3 py-2 text-niyam-text-muted">{r.recipient_roles.join(', ')}</td>
                      <td className="px-3 py-2">
                        <Badge variant={r.is_active ? 'success' : 'neutral'}>
                          {r.is_active ? 'ACTIVE' : 'INACTIVE'}
                        </Badge>
                      </td>
                      <td className="px-3 py-2 text-right">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleDeleteReminderRule(r.id, r.name)}
                        >
                          <Trash2 className="w-3 h-3 text-rose-600" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          <Card title="Configurable Escalation Rules" subtitle="System escalations triggered when SLA deadlines breach">
            <div className="overflow-x-auto border border-niyam-border rounded-lg mt-3">
              <table className="min-w-full divide-y divide-niyam-border text-xs">
                <thead className="bg-slate-50 text-niyam-text font-semibold">
                  <tr>
                    <th className="px-3 py-2 text-left">Rule Name</th>
                    <th className="px-3 py-2 text-left">Level</th>
                    <th className="px-3 py-2 text-left">Target Entity</th>
                    <th className="px-3 py-2 text-left">Trigger Offset</th>
                    <th className="px-3 py-2 text-left">Escalate To Roles</th>
                    <th className="px-3 py-2 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-niyam-border bg-white text-niyam-text">
                  {escalationRules.map((e) => (
                    <tr key={e.id} className="hover:bg-slate-50">
                      <td className="px-3 py-2 font-medium">{e.name}</td>
                      <td className="px-3 py-2">
                        <Badge variant="danger">Level {e.level}</Badge>
                      </td>
                      <td className="px-3 py-2 capitalize">{e.target_type}</td>
                      <td className="px-3 py-2 text-niyam-text-muted">+{e.days_after_due} Days Overdue</td>
                      <td className="px-3 py-2 text-niyam-text-muted">{e.recipient_roles.join(', ')}</td>
                      <td className="px-3 py-2 text-right">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleDeleteEscalationRule(e.id, e.name)}
                        >
                          <Trash2 className="w-3 h-3 text-rose-600" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}

      {/* =====================================================================
          TAB 4: HOLIDAY CALENDARS
          ===================================================================== */}
      {activeTab === 'holidays' && (
        <Card
          title="Regional & National Holiday Calendar"
          subtitle="Holidays are excluded when computing working-day workflow deadlines"
        >
          <div className="flex justify-end mb-3">
            <Button
              size="sm"
              variant="primary"
              onClick={() => {
                setHolidayName('');
                setHolidayDate('');
                setHolidayChangeReason('');
                setIsHolidayModalOpen(true);
              }}
            >
              <Plus className="w-3.5 h-3.5 mr-1" />
              Add Holiday
            </Button>
          </div>

          <div className="overflow-x-auto border border-niyam-border rounded-lg">
            <table className="min-w-full divide-y divide-niyam-border text-xs">
              <thead className="bg-slate-50 text-niyam-text font-semibold">
                <tr>
                  <th className="px-3 py-2 text-left">Holiday Name</th>
                  <th className="px-3 py-2 text-left">Date</th>
                  <th className="px-3 py-2 text-left">Jurisdiction</th>
                  <th className="px-3 py-2 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-niyam-border bg-white text-niyam-text">
                {holidays.map((h) => (
                  <tr key={h.id} className="hover:bg-slate-50">
                    <td className="px-3 py-2 font-medium">{h.name}</td>
                    <td className="px-3 py-2 font-mono">{h.holiday_date}</td>
                    <td className="px-3 py-2">
                      <Badge variant="neutral">{h.region_id ? 'Regional' : 'National All-Regions'}</Badge>
                    </td>
                    <td className="px-3 py-2 text-right">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleDeleteHoliday(h.id, h.name)}
                      >
                        <Trash2 className="w-3 h-3 text-rose-600" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* =====================================================================
          TAB 5: MESSAGE TEMPLATES
          ===================================================================== */}
      {activeTab === 'templates' && (
        <Card
          title="Notification & In-App Message Templates"
          subtitle="Configure message subject and body templates with variable interpolation"
        >
          <div className="space-y-3 pt-2">
            {templates.map((tpl) => (
              <div
                key={tpl.id}
                className="p-3.5 rounded-lg border border-niyam-border bg-white space-y-2 text-xs"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-niyam-text">{tpl.code}</span>
                  <Badge variant={tpl.is_active ? 'success' : 'neutral'}>
                    {tpl.channel.toUpperCase()} • {tpl.is_active ? 'ACTIVE' : 'INACTIVE'}
                  </Badge>
                </div>
                <p className="text-niyam-text font-medium">
                  <strong>Subject:</strong> {tpl.subject_template}
                </p>
                <p className="text-niyam-text-muted font-mono bg-slate-50 p-2 rounded">
                  {tpl.body_template}
                </p>
                <div className="flex justify-end pt-1">
                  <Button size="sm" variant="outline" onClick={() => handleOpenEditTemplate(tpl)}>
                    <Edit className="w-3 h-3 mr-1" />
                    Edit Template
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* =====================================================================
          TAB 6: VERSION HISTORY
          ===================================================================== */}
      {activeTab === 'versions' && (
        <Card
          title="Configuration Audit Version History"
          subtitle="Immutable audit trail of all administrative configuration modifications"
        >
          <div className="overflow-x-auto border border-niyam-border rounded-lg mt-3">
            <table className="min-w-full divide-y divide-niyam-border text-xs">
              <thead className="bg-slate-50 text-niyam-text font-semibold">
                <tr>
                  <th className="px-3 py-2 text-left">Config Type</th>
                  <th className="px-3 py-2 text-left">Version</th>
                  <th className="px-3 py-2 text-left">Change Summary & Justification</th>
                  <th className="px-3 py-2 text-left">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-niyam-border bg-white text-niyam-text">
                {configVersions.map((v) => (
                  <tr key={v.id} className="hover:bg-slate-50">
                    <td className="px-3 py-2">
                      <Badge variant="neutral">{v.config_type.toUpperCase()}</Badge>
                    </td>
                    <td className="px-3 py-2 font-mono font-bold">v{v.version}</td>
                    <td className="px-3 py-2 text-niyam-text">{v.change_summary}</td>
                    <td className="px-3 py-2 text-niyam-text-muted">
                      {new Date(v.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* =====================================================================
          TAB 7: WORKER HEALTH & OPERATIONAL MONITORING
          ===================================================================== */}
      {activeTab === 'monitoring' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Card className="border-l-4 border-l-emerald-500">
              <p className="text-xs text-niyam-text-muted font-medium">Worker Status</p>
              <h3 className="text-xl font-bold text-niyam-text mt-1 capitalize">
                {workerHealth?.status ?? 'Unknown'}
              </h3>
              <p className="text-[11px] text-niyam-text-muted mt-2">
                Total executions: {workerHealth?.total_runs ?? 0}
              </p>
            </Card>

            <Card className="border-l-4 border-l-blue-500">
              <p className="text-xs text-niyam-text-muted font-medium">Last Successful Execution</p>
              <h3 className="text-sm font-semibold text-niyam-text mt-1">
                {workerHealth?.last_successful_run
                  ? new Date(workerHealth.last_successful_run.started_at).toLocaleString()
                  : 'No successful runs'}
              </h3>
              <p className="text-[11px] text-emerald-700 mt-2">
                Processed: {workerHealth?.last_successful_run?.items_processed ?? 0} notifications
              </p>
            </Card>

            <Card className="border-l-4 border-l-rose-500">
              <p className="text-xs text-niyam-text-muted font-medium">Failed Executions</p>
              <h3 className="text-xl font-bold text-rose-700 mt-1">
                {workerHealth?.failed_runs ?? 0} Failures
              </h3>
              <p className="text-[11px] text-niyam-text-muted mt-2">
                Success rate: {workerHealth && workerHealth.total_runs > 0 ? `${Math.round((workerHealth.success_runs / workerHealth.total_runs) * 100)}%` : '100%'}
              </p>
            </Card>
          </div>

          <Card title="Recent Scheduler Execution History" subtitle="Audit log of background deadline scans and duration metrics">
            <div className="overflow-x-auto border border-niyam-border rounded-lg mt-3">
              <table className="min-w-full divide-y divide-niyam-border text-xs">
                <thead className="bg-slate-50 text-niyam-text font-semibold">
                  <tr>
                    <th className="px-3 py-2 text-left">Started At</th>
                    <th className="px-3 py-2 text-left">Duration</th>
                    <th className="px-3 py-2 text-left">Status</th>
                    <th className="px-3 py-2 text-left">Items Scanned</th>
                    <th className="px-3 py-2 text-left">Items Processed</th>
                    <th className="px-3 py-2 text-left">Errors</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-niyam-border bg-white text-niyam-text">
                  {workerHealth?.recent_runs.map((run) => (
                    <tr key={run.id} className="hover:bg-slate-50">
                      <td className="px-3 py-2 text-niyam-text-muted">
                        {new Date(run.started_at).toLocaleString()}
                      </td>
                      <td className="px-3 py-2 font-mono">
                        {run.duration_seconds ? `${run.duration_seconds}s` : '—'}
                      </td>
                      <td className="px-3 py-2">
                        <Badge variant={run.status === 'success' ? 'success' : 'danger'}>
                          {run.status.toUpperCase()}
                        </Badge>
                      </td>
                      <td className="px-3 py-2 font-mono">{run.items_scanned}</td>
                      <td className="px-3 py-2 font-mono">{run.items_processed}</td>
                      <td className="px-3 py-2 text-rose-700 font-mono text-[11px]">
                        {run.error_summary || 'None'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}

      {/* =====================================================================
          TAB 8: AUDIT TRAIL EXPLORER
          ===================================================================== */}
      {activeTab === 'audit' && (
        <Card
          title="System Audit Log Explorer"
          subtitle="Cryptographically verifiable append-only transaction log across all entities"
        >
          <div className="flex flex-col sm:flex-row gap-2 items-center justify-between mb-3">
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <input
                placeholder="Filter by Action..."
                value={auditFilterAction}
                onChange={(e) => setAuditFilterAction(e.target.value)}
                className="text-xs border border-niyam-border rounded px-2.5 py-1.5 bg-white text-niyam-text"
              />
              <input
                placeholder="Filter Entity Type..."
                value={auditFilterType}
                onChange={(e) => setAuditFilterType(e.target.value)}
                className="text-xs border border-niyam-border rounded px-2.5 py-1.5 bg-white text-niyam-text"
              />
              <Button size="sm" variant="outline" onClick={() => fetchAuditLogs(1)}>
                <Search className="w-3.5 h-3.5 mr-1" />
                Filter
              </Button>
            </div>
          </div>

          <div className="overflow-x-auto border border-niyam-border rounded-lg">
            <table className="min-w-full divide-y divide-niyam-border text-xs">
              <thead className="bg-slate-50 text-niyam-text font-semibold">
                <tr>
                  <th className="px-3 py-2 text-left">Timestamp</th>
                  <th className="px-3 py-2 text-left">Actor</th>
                  <th className="px-3 py-2 text-left">Action</th>
                  <th className="px-3 py-2 text-left">Entity</th>
                  <th className="px-3 py-2 text-left">Hash Snippet</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-niyam-border bg-white text-niyam-text">
                {auditLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50 font-mono text-[11px]">
                    <td className="px-3 py-2 text-niyam-text-muted">
                      {new Date(log.occurred_at).toLocaleString()}
                    </td>
                    <td className="px-3 py-2 font-sans font-medium">{log.actor_name}</td>
                    <td className="px-3 py-2 font-sans">
                      <Badge variant="neutral">{log.action}</Badge>
                    </td>
                    <td className="px-3 py-2 text-niyam-text-muted font-sans">
                      {log.entity_type}: {log.entity_id.slice(0, 8)}...
                    </td>
                    <td className="px-3 py-2 text-niyam-text-muted">{log.entry_hash.slice(0, 16)}...</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between text-xs text-niyam-text-muted pt-3">
            <span>Total Logged Actions: {auditTotal}</span>
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant="outline"
                disabled={auditPage <= 1}
                onClick={() => fetchAuditLogs(auditPage - 1)}
              >
                Previous
              </Button>
              <span className="font-semibold text-niyam-text px-2">Page {auditPage}</span>
              <Button
                size="sm"
                variant="outline"
                disabled={auditPage * 20 >= auditTotal}
                onClick={() => fetchAuditLogs(auditPage + 1)}
              >
                Next
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* MODAL 1: Edit Stage Timeline */}
      {isEditStageModalOpen && selectedStage && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6 space-y-4 border border-niyam-border">
            <h3 className="text-lg font-bold text-niyam-text">Configure Stage: {selectedStage.stage_name}</h3>
            <p className="text-xs text-niyam-text-muted">
              Configure stage SLA parameters. A version record will be created to preserve historical continuity.
            </p>

            <form onSubmit={handleSaveStage} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-niyam-text mb-1">
                  Timeline (Days) *
                </label>
                <input
                  type="number"
                  min={1}
                  max={365}
                  required
                  value={editTimelineDays}
                  onChange={(e) => setEditTimelineDays(Number(e.target.value))}
                  className="w-full text-xs border border-niyam-border rounded px-3 py-2 bg-white text-niyam-text"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-niyam-text mb-1">
                  Day Type *
                </label>
                <select
                  value={editDayType}
                  onChange={(e) => setEditDayType(e.target.value)}
                  className="w-full text-xs border border-niyam-border rounded px-3 py-2 bg-white text-niyam-text"
                >
                  <option value="working_days">Working Days (Excluding Weekends & Holidays)</option>
                  <option value="calendar_days">Calendar Days (Consecutive)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-niyam-text mb-1">
                  Mandatory Change Reason / Regulatory Authority *
                </label>
                <textarea
                  required
                  rows={3}
                  placeholder="Record basis for timeline change (e.g. Revised AICTE Handbook 2026 Table 4.1)..."
                  value={stageChangeReason}
                  onChange={(e) => setStageChangeReason(e.target.value)}
                  className="w-full text-xs border border-niyam-border rounded p-2 bg-white text-niyam-text"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setIsEditStageModalOpen(false)}
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
                <Button type="submit" size="sm" variant="primary" disabled={isSubmitting}>
                  {isSubmitting ? 'Saving...' : 'Confirm & Version'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: Create Rule */}
      {isRuleModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6 space-y-4 border border-niyam-border">
            <h3 className="text-lg font-bold text-niyam-text">
              Add {ruleType === 'reminder' ? 'Reminder Rule' : 'Escalation Rule'}
            </h3>

            <form onSubmit={handleCreateRule} className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-niyam-text mb-1">Rule Name *</label>
                <Input required value={ruleName} onChange={(e) => setRuleName(e.target.value)} />
              </div>

              <div>
                <label className="block text-xs font-medium text-niyam-text mb-1">Target Entity *</label>
                <select
                  value={ruleTarget}
                  onChange={(e) => setRuleTarget(e.target.value)}
                  className="w-full text-xs border border-niyam-border rounded px-3 py-2 bg-white text-niyam-text"
                >
                  <option value="application">Application Workflow Stage</option>
                  <option value="undertaking">Compliance Undertaking</option>
                  <option value="document">Statutory Document</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs font-medium text-niyam-text mb-1">
                    {ruleType === 'reminder' ? 'Days Before Due' : 'Days After Due'} *
                  </label>
                  <input
                    type="number"
                    min={0}
                    required
                    value={ruleDays}
                    onChange={(e) => setRuleDays(Number(e.target.value))}
                    className="w-full text-xs border border-niyam-border rounded px-3 py-2 bg-white text-niyam-text"
                  />
                </div>
                {ruleType === 'escalation' && (
                  <div>
                    <label className="block text-xs font-medium text-niyam-text mb-1">Level *</label>
                    <input
                      type="number"
                      min={1}
                      max={5}
                      required
                      value={ruleLevel}
                      onChange={(e) => setRuleLevel(Number(e.target.value))}
                      className="w-full text-xs border border-niyam-border rounded px-3 py-2 bg-white text-niyam-text"
                    />
                  </div>
                )}
              </div>

              <div>
                <label className="block text-xs font-medium text-niyam-text mb-1">
                  Recipient Roles (comma-separated) *
                </label>
                <Input
                  required
                  placeholder="e.g. scrutiny_officer, regional_officer"
                  value={ruleRoles}
                  onChange={(e) => setRuleRoles(e.target.value)}
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-niyam-text mb-1">
                  Mandatory Change Reason *
                </label>
                <textarea
                  required
                  rows={2}
                  placeholder="Record justification..."
                  value={ruleChangeReason}
                  onChange={(e) => setRuleChangeReason(e.target.value)}
                  className="w-full text-xs border border-niyam-border rounded p-2 bg-white text-niyam-text"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setIsRuleModalOpen(false)}
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
                <Button type="submit" size="sm" variant="primary" disabled={isSubmitting}>
                  {isSubmitting ? 'Saving...' : 'Create Rule'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 3: Create Holiday */}
      {isHolidayModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6 space-y-4 border border-niyam-border">
            <h3 className="text-lg font-bold text-niyam-text">Register Calendar Holiday</h3>

            <form onSubmit={handleCreateHoliday} className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-niyam-text mb-1">Holiday Name *</label>
                <Input required value={holidayName} onChange={(e) => setHolidayName(e.target.value)} />
              </div>

              <div>
                <label className="block text-xs font-medium text-niyam-text mb-1">Date *</label>
                <input
                  type="date"
                  required
                  value={holidayDate}
                  onChange={(e) => setHolidayDate(e.target.value)}
                  className="w-full text-xs border border-niyam-border rounded px-3 py-2 bg-white text-niyam-text"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-niyam-text mb-1">Change Reason *</label>
                <textarea
                  required
                  rows={2}
                  value={holidayChangeReason}
                  onChange={(e) => setHolidayChangeReason(e.target.value)}
                  className="w-full text-xs border border-niyam-border rounded p-2 bg-white text-niyam-text"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setIsHolidayModalOpen(false)}
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
                <Button type="submit" size="sm" variant="primary" disabled={isSubmitting}>
                  {isSubmitting ? 'Saving...' : 'Save Holiday'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 4: Edit Template */}
      {isTemplateModalOpen && selectedTemplate && (
        <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6 space-y-4 border border-niyam-border">
            <h3 className="text-lg font-bold text-niyam-text">Edit Template: {selectedTemplate.code}</h3>

            <form onSubmit={handleSaveTemplate} className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-niyam-text mb-1">Subject *</label>
                <Input required value={templateSubject} onChange={(e) => setTemplateSubject(e.target.value)} />
              </div>

              <div>
                <label className="block text-xs font-medium text-niyam-text mb-1">Body Template *</label>
                <textarea
                  required
                  rows={4}
                  value={templateBody}
                  onChange={(e) => setTemplateBody(e.target.value)}
                  className="w-full text-xs border border-niyam-border rounded p-2 bg-white text-niyam-text font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-niyam-text mb-1">Change Reason *</label>
                <textarea
                  required
                  rows={2}
                  value={templateReason}
                  onChange={(e) => setTemplateReason(e.target.value)}
                  className="w-full text-xs border border-niyam-border rounded p-2 bg-white text-niyam-text"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setIsTemplateModalOpen(false)}
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
                <Button type="submit" size="sm" variant="primary" disabled={isSubmitting}>
                  {isSubmitting ? 'Saving...' : 'Update Template'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
