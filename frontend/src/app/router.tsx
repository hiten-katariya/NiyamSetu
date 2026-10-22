import { createBrowserRouter } from 'react-router-dom';
import { AppShell } from '../components/layout/AppShell';
import { ProtectedRoute } from '../components/ProtectedRoute';
import { DashboardPage } from '../features/dashboard/DashboardPage';
import { ApplicationsListPage } from '../features/applications/ApplicationsListPage';
import { ApplicationDetailPage } from '../features/applications/ApplicationDetailPage';
import { EVCListPage } from '../features/evc/EVCListPage';
import { ComplianceListPage } from '../features/compliance/ComplianceListPage';
import { DocumentsListPage } from '../features/documents/DocumentsListPage';
import { NotificationsPage } from '../features/notifications/NotificationsPage';
import { ReportsPage } from '../features/reports/ReportsPage';
import { AdminConfigPage } from '../features/admin/AdminConfigPage';
import { LoginPage } from '../features/auth/LoginPage';
import { AccessDeniedPage } from '../features/auth/AccessDeniedPage';

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/access-denied',
    element: <AccessDeniedPage />,
  },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <AppShell />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <DashboardPage />,
      },
      {
        path: 'applications',
        element: (
          <ProtectedRoute
            allowedRoles={[
              'admin',
              'system_admin',
              'institution_user',
              'scrutiny_officer',
              'regional_officer',
              'bureau_officer',
              'senior_authority',
            ]}
          >
            <ApplicationsListPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'applications/:id',
        element: (
          <ProtectedRoute
            allowedRoles={[
              'admin',
              'system_admin',
              'institution_user',
              'scrutiny_officer',
              'regional_officer',
              'bureau_officer',
              'committee_member',
              'senior_authority',
            ]}
          >
            <ApplicationDetailPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'evc',
        element: (
          <ProtectedRoute
            allowedRoles={[
              'admin',
              'system_admin',
              'regional_officer',
              'committee_member',
              'bureau_officer',
              'senior_authority',
            ]}
          >
            <EVCListPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'compliance',
        element: (
          <ProtectedRoute
            allowedRoles={[
              'admin',
              'system_admin',
              'institution_user',
              'regional_officer',
              'scrutiny_officer',
              'bureau_officer',
              'senior_authority',
            ]}
          >
            <ComplianceListPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'documents',
        element: (
          <ProtectedRoute
            allowedRoles={[
              'admin',
              'system_admin',
              'institution_user',
              'scrutiny_officer',
              'regional_officer',
              'committee_member',
              'bureau_officer',
              'senior_authority',
            ]}
          >
            <DocumentsListPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'notifications',
        element: <NotificationsPage />,
      },
      {
        path: 'reports',
        element: (
          <ProtectedRoute
            allowedRoles={[
              'admin',
              'system_admin',
              'regional_officer',
              'bureau_officer',
              'senior_authority',
            ]}
          >
            <ReportsPage />
          </ProtectedRoute>
        ),
      },
      {
        path: 'admin',
        element: (
          <ProtectedRoute allowedRoles={['admin', 'system_admin']}>
            <AdminConfigPage />
          </ProtectedRoute>
        ),
      },
    ],
  },
]);
