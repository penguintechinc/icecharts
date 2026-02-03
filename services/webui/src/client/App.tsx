import { Routes, Route, Navigate } from 'react-router-dom';
import { AppConsoleVersion } from '@penguin/react_libs';
import { useAuth } from './hooks/useAuth';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';
import RoleGuard from './components/RoleGuard';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Users from './pages/Users';
import UserDetail from './pages/UserDetail';
import Profile from './pages/Profile';
import Settings from './pages/Settings';
import Libraries from './pages/Libraries';
import ServiceAccounts from './pages/Admin/ServiceAccounts';
import AdminSettings from './pages/Admin/AdminSettings';
import ActivityLogs from './pages/Admin/ActivityLogs';
import AuditLogs from './pages/Admin/AuditLogs';
import LicenseSettings from './pages/Admin/LicenseSettings';
// IceFlows pages
import IceFlowsList from './pages/iceflows/IceFlowsList';
import IceFlowDetail from './pages/iceflows/IceFlowDetail';
import IceFlowEditor from './pages/iceflows/IceFlowEditor';
import IceFlowPromotions from './pages/iceflows/IceFlowPromotions';
import MyApprovals from './pages/iceflows/MyApprovals';
// IceRuns pages
import IceRunsList from './pages/iceruns/IceRunsList';
import IceRunCreate from './pages/iceruns/IceRunCreate';
import IceRunDetail from './pages/iceruns/IceRunDetail';
import IceRunEdit from './pages/iceruns/IceRunEdit';
import IceRunExecutions from './pages/iceruns/IceRunExecutions';

function App() {
  const { isAuthenticated, isLoading } = useAuth();

  // Build timestamp for verification
  console.log('IceCharts Build:', new Date().toISOString());

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-dark-950">
        <div className="text-gold-400 text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <>
      <AppConsoleVersion
        appName="IceCharts"
        webuiVersion={import.meta.env.VITE_VERSION || '0.2.0'}
        webuiBuildEpoch={Number(import.meta.env.VITE_BUILD_TIME) || 0}
        environment={import.meta.env.MODE}
        webuiEmoji="🧊"
        apiEmoji="📊"
        metadata={{
          'API URL': import.meta.env.VITE_API_URL || '(relative)',
          'WebSocket': 'Socket.IO',
        }}
      />
      <Routes>
      {/* Public routes */}
      <Route
        path="/login"
        element={isAuthenticated ? <Navigate to="/" replace /> : <Login />}
      />

      {/* Protected routes with layout */}
      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        {/* Dashboard - all authenticated users */}
        <Route path="/" element={<Dashboard />} />
        <Route path="/dashboard" element={<Navigate to="/" replace />} />

        {/* Profile - all authenticated users */}
        <Route path="/profile" element={<Profile />} />

        {/* Settings - Maintainer and Admin */}
        <Route
          path="/settings"
          element={
            <RoleGuard allowedRoles={['admin', 'maintainer']}>
              <Settings />
            </RoleGuard>
          }
        />

        {/* Libraries - Maintainer and Admin */}
        <Route
          path="/libraries"
          element={
            <RoleGuard allowedRoles={['admin', 'maintainer']}>
              <Libraries />
            </RoleGuard>
          }
        />

        {/* IceFlows - CI/CD Pipeline Orchestration - Maintainer and Admin */}
        <Route
          path="/iceflows"
          element={
            <RoleGuard allowedRoles={['admin', 'maintainer']}>
              <IceFlowsList />
            </RoleGuard>
          }
        />
        <Route
          path="/iceflows/new"
          element={
            <RoleGuard allowedRoles={['admin', 'maintainer']}>
              <IceFlowEditor />
            </RoleGuard>
          }
        />
        <Route
          path="/iceflows/:id"
          element={
            <RoleGuard allowedRoles={['admin', 'maintainer']}>
              <IceFlowDetail />
            </RoleGuard>
          }
        />
        <Route
          path="/iceflows/:id/edit"
          element={
            <RoleGuard allowedRoles={['admin', 'maintainer']}>
              <IceFlowEditor />
            </RoleGuard>
          }
        />
        <Route
          path="/iceflows/promotions"
          element={
            <RoleGuard allowedRoles={['admin', 'maintainer']}>
              <IceFlowPromotions />
            </RoleGuard>
          }
        />
        <Route
          path="/iceflows/approvals"
          element={
            <RoleGuard allowedRoles={['admin', 'maintainer']}>
              <MyApprovals />
            </RoleGuard>
          }
        />

        {/* IceRuns - Serverless Functions - Maintainer and Admin */}
        <Route
          path="/iceruns"
          element={
            <RoleGuard allowedRoles={['admin', 'maintainer']}>
              <IceRunsList />
            </RoleGuard>
          }
        />
        <Route
          path="/iceruns/new"
          element={
            <RoleGuard allowedRoles={['admin', 'maintainer']}>
              <IceRunCreate />
            </RoleGuard>
          }
        />
        <Route
          path="/iceruns/:id"
          element={
            <RoleGuard allowedRoles={['admin', 'maintainer']}>
              <IceRunDetail />
            </RoleGuard>
          }
        />
        <Route
          path="/iceruns/:id/edit"
          element={
            <RoleGuard allowedRoles={['admin', 'maintainer']}>
              <IceRunEdit />
            </RoleGuard>
          }
        />
        <Route
          path="/iceruns/:id/executions"
          element={
            <RoleGuard allowedRoles={['admin', 'maintainer']}>
              <IceRunExecutions />
            </RoleGuard>
          }
        />

        {/* User management - Admin only */}
        <Route
          path="/users"
          element={
            <RoleGuard allowedRoles={['admin']}>
              <Users />
            </RoleGuard>
          }
        />
        <Route
          path="/users/:id"
          element={
            <RoleGuard allowedRoles={['admin']}>
              <UserDetail />
            </RoleGuard>
          }
        />

        {/* Admin pages - Admin only */}
        <Route
          path="/admin/service-accounts"
          element={
            <RoleGuard allowedRoles={['admin']}>
              <ServiceAccounts />
            </RoleGuard>
          }
        />
        <Route
          path="/admin/activity"
          element={
            <RoleGuard allowedRoles={['admin']}>
              <ActivityLogs />
            </RoleGuard>
          }
        />
        <Route
          path="/admin/audit-log"
          element={
            <RoleGuard allowedRoles={['admin']}>
              <AuditLogs />
            </RoleGuard>
          }
        />
        <Route
          path="/admin/settings"
          element={
            <RoleGuard allowedRoles={['admin']}>
              <AdminSettings />
            </RoleGuard>
          }
        />
        <Route
          path="/admin/license"
          element={
            <RoleGuard allowedRoles={['admin']}>
              <LicenseSettings />
            </RoleGuard>
          }
        />
      </Route>

      {/* Catch all - redirect to dashboard or login */}
      <Route
        path="*"
        element={<Navigate to={isAuthenticated ? '/' : '/login'} replace />}
      />
    </Routes>
    </>
  );
}

export default App;
