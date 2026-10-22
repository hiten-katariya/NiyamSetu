import React, { useState, useEffect } from 'react';
import { Badge } from '../../components/Badge';
import { Button } from '../../components/Button';
import { Card } from '../../components/Card';
import { api, ApiClientError } from '../../lib/apiClient';
import { User, UserRole } from '../../types';
import { Shield, UserCheck, UserX, AlertCircle, RefreshCw } from 'lucide-react';

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

export const AdminConfigPage: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoadingUsers, setIsLoadingUsers] = useState(false);
  const [userError, setUserError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [updatingUserId, setUpdatingUserId] = useState<string | null>(null);

  const fetchUsers = async () => {
    setIsLoadingUsers(true);
    setUserError(null);
    try {
      const data = await api.get<User[]>('/admin/users');
      setUsers(data);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setUserError(err.message);
      } else {
        setUserError('Failed to load system users.');
      }
    } finally {
      setIsLoadingUsers(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleRoleChange = async (userId: string, newRole: UserRole) => {
    setUpdatingUserId(userId);
    setStatusMessage(null);
    setUserError(null);
    try {
      await api.patch(`/admin/users/${userId}/role`, { role: newRole });
      setStatusMessage('User role updated successfully.');
      await fetchUsers();
    } catch (err) {
      if (err instanceof ApiClientError) {
        setUserError(err.message);
      } else {
        setUserError('Failed to update user role.');
      }
    } finally {
      setUpdatingUserId(null);
    }
  };

  const handleStatusToggle = async (userId: string, currentStatus: boolean) => {
    setUpdatingUserId(userId);
    setStatusMessage(null);
    setUserError(null);
    try {
      await api.patch(`/admin/users/${userId}/status`, { is_active: !currentStatus });
      setStatusMessage(`User account successfully ${!currentStatus ? 'activated' : 'deactivated'}.`);
      await fetchUsers();
    } catch (err) {
      if (err instanceof ApiClientError) {
        setUserError(err.message);
      } else {
        setUserError('Failed to update user account status.');
      }
    } finally {
      setUpdatingUserId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-niyam-border">
        <div>
          <h2 className="text-xl sm:text-2xl font-bold text-niyam-text">
            Admin System Configuration & Security
          </h2>
          <p className="text-sm text-niyam-text-muted mt-1">
            Configure approval routes, stage timelines, security controls, and manage user role assignments under least-privilege policy.
          </p>
        </div>
        <Badge variant="warning">Database Managed</Badge>
      </div>

      {/* User Management & RBAC Governance Card */}
      <Card
        title="User Role Management & Status"
        subtitle="Manage user role assignments and account active statuses with server-side audit logging"
      >
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2 text-xs text-niyam-text-muted">
            <Shield className="w-4 h-4 text-niyam-primary" />
            <span>Authorised administrative controls with CSRF double-submit validation</span>
          </div>
          <Button
            size="sm"
            variant="outline"
            onClick={fetchUsers}
            disabled={isLoadingUsers}
            className="gap-1.5"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoadingUsers ? 'animate-spin' : ''}`} />
            <span>Refresh Users</span>
          </Button>
        </div>

        {statusMessage && (
          <div className="mb-4 p-2.5 rounded bg-green-50 border border-green-200 text-niyam-status-success text-xs font-medium">
            {statusMessage}
          </div>
        )}

        {userError && (
          <div className="mb-4 p-2.5 rounded bg-red-50 border border-red-200 text-niyam-status-danger text-xs font-medium flex items-center gap-1.5">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{userError}</span>
          </div>
        )}

        {isLoadingUsers && users.length === 0 ? (
          <div className="text-center py-8 text-xs text-niyam-text-muted">
            Loading user list...
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-niyam-surface-alt border-y border-niyam-border text-niyam-text-muted font-semibold">
                <tr>
                  <th className="py-2.5 px-3">Full Name & Email</th>
                  <th className="py-2.5 px-3">Current Role</th>
                  <th className="py-2.5 px-3">Scope Scope / Unit</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-niyam-border">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-niyam-surface-alt/50">
                    <td className="py-2.5 px-3">
                      <p className="font-semibold text-niyam-text">{u.full_name}</p>
                      <p className="text-[11px] text-niyam-text-muted">{u.email}</p>
                    </td>
                    <td className="py-2.5 px-3">
                      <select
                        aria-label={`Change role for ${u.full_name}`}
                        value={u.role}
                        disabled={updatingUserId === u.id}
                        onChange={(e) => handleRoleChange(u.id, e.target.value as UserRole)}
                        className="text-xs bg-niyam-surface border border-niyam-border rounded px-2 py-1 text-niyam-text focus:outline-none focus:ring-1 focus:ring-niyam-primary font-medium"
                      >
                        {ALL_ROLES.map((r) => (
                          <option key={r} value={r}>
                            {r.replace(/_/g, ' ')}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="py-2.5 px-3 text-niyam-text-muted">
                      {u.institution_id
                        ? 'Institutional User'
                        : u.region_id
                        ? 'Regional Desk'
                        : 'Bureau / Central'}
                    </td>
                    <td className="py-2.5 px-3">
                      <Badge variant={u.is_active ? 'success' : 'danger'}>
                        {u.is_active ? 'Active' : 'Disabled'}
                      </Badge>
                    </td>
                    <td className="py-2.5 px-3 text-right">
                      <Button
                        size="sm"
                        variant={u.is_active ? 'outline' : 'primary'}
                        disabled={updatingUserId === u.id}
                        onClick={() => handleStatusToggle(u.id, u.is_active)}
                        className="text-[11px] py-1 px-2.5 gap-1"
                      >
                        {u.is_active ? (
                          <>
                            <UserX className="w-3 h-3 text-red-500" />
                            <span>Deactivate</span>
                          </>
                        ) : (
                          <>
                            <UserCheck className="w-3 h-3 text-emerald-500" />
                            <span>Activate</span>
                          </>
                        )}
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Route & SLA Configuration Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card title="Configurable Route Types" subtitle="Ordered sequence of approval stages">
          <div className="p-3 rounded bg-niyam-surface-alt border border-niyam-border mb-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-niyam-text">Sample Scrutiny + EVC Route</span>
              <Badge variant="success">Active (v1)</Badge>
            </div>
            <p className="text-xs text-niyam-text-muted mt-1">
              6 stages: Scrutiny (7d) → Re-Scrutiny (5d) → EVC Scheduling (10d) → EVC Conduct (7d) → Report Review (5d) → Decision (7d)
            </p>
          </div>
          <Button size="sm" variant="outline">
            + Configure New Route Type
          </Button>
        </Card>

        <Card title="Automated Escalation Chains" subtitle="Tiered SLA breaches and recipient matrix">
          <div className="p-3 rounded bg-niyam-surface-alt border border-niyam-border mb-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-niyam-text">Level 1 Escalation: Stage Overdue (+1 Day)</span>
              <Badge variant="danger">Escalates to RO</Badge>
            </div>
            <p className="text-xs text-niyam-text-muted mt-1">
              Triggered 1 day past stage deadline. Notifies Regional Officer and flags application red.
            </p>
          </div>
          <Button size="sm" variant="outline">
            + Add Escalation Rule
          </Button>
        </Card>
      </div>
    </div>
  );
};
