import { createBrowserRouter } from 'react-router-dom';
import { AppShell } from '../components/layout/AppShell';
import { DashboardPage } from '../features/dashboard/DashboardPage';
import { ApplicationsListPage } from '../features/applications/ApplicationsListPage';
import { EVCListPage } from '../features/evc/EVCListPage';
import { ComplianceListPage } from '../features/compliance/ComplianceListPage';
import { DocumentsListPage } from '../features/documents/DocumentsListPage';
import { NotificationsPage } from '../features/notifications/NotificationsPage';
import { ReportsPage } from '../features/reports/ReportsPage';
import { AdminConfigPage } from '../features/admin/AdminConfigPage';
import { LoginPage } from '../features/auth/LoginPage';

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/',
    element: <AppShell />,
    children: [
      {
        index: true,
        element: <DashboardPage />,
      },
      {
        path: 'applications',
        element: <ApplicationsListPage />,
      },
      {
        path: 'evc',
        element: <EVCListPage />,
      },
      {
        path: 'compliance',
        element: <ComplianceListPage />,
      },
      {
        path: 'documents',
        element: <DocumentsListPage />,
      },
      {
        path: 'notifications',
        element: <NotificationsPage />,
      },
      {
        path: 'reports',
        element: <ReportsPage />,
      },
      {
        path: 'admin',
        element: <AdminConfigPage />,
      },
    ],
  },
]);
