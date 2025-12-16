import { Routes, Route, Navigate } from 'react-router-dom';
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

function App() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-dark-950">
        <div className="text-gold-400 text-xl">Loading...</div>
      </div>
    );
  }

  return (
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
      </Route>

      {/* Catch all - redirect to dashboard or login */}
      <Route
        path="*"
        element={<Navigate to={isAuthenticated ? '/' : '/login'} replace />}
      />
    </Routes>
  );
}

export default App;
