import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './store/authStore';
import { Layout } from './components/layout';

// Lazy load pages for code splitting
const Dashboard = React.lazy(() => import('./pages/Dashboard'));
const Login = React.lazy(() => import('./pages/Login'));
const Register = React.lazy(() => import('./pages/Register'));
const DrawingEditor = React.lazy(() => import('./pages/DrawingEditor'));
const NotFound = React.lazy(() => import('./pages/NotFound'));
const Drawings = React.lazy(() => import('./client/pages/Drawings'));
const Groups = React.lazy(() => import('./client/pages/Groups'));
const GroupDetail = React.lazy(() => import('./client/pages/GroupDetail'));
const Templates = React.lazy(() => import('./client/pages/Templates'));
const Settings = React.lazy(() => import('./client/pages/Settings'));
const AdminUsers = React.lazy(() => import('./client/pages/Users'));
const SSOConfiguration = React.lazy(() => import('./client/pages/SSOConfiguration'));

// Protected route wrapper
interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-900">
        <div className="animate-pulse text-amber-400 text-xl">Loading...</div>
      </div>
    );
  }

  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
};

// Loading fallback component
const LoadingFallback: React.FC = () => (
  <div className="flex items-center justify-center min-h-screen bg-gray-900">
    <div className="animate-pulse text-amber-400 text-xl">Loading...</div>
  </div>
);

const App: React.FC = () => {
  const { initAuth } = useAuthStore();

  useEffect(() => {
    // Initialize authentication state from localStorage
    initAuth();
  }, [initAuth]);

  return (
    <BrowserRouter>
      <React.Suspense fallback={<LoadingFallback />}>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Protected routes with Layout */}
          <Route
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/drawings" element={<Drawings />} />
            <Route path="/drawings/new" element={<DrawingEditor />} />
            <Route path="/drawings/:id" element={<DrawingEditor />} />
            <Route path="/groups" element={<Groups />} />
            <Route path="/groups/:id" element={<GroupDetail />} />
            <Route path="/templates" element={<Templates />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/admin/users" element={<AdminUsers />} />
            <Route path="/admin/sso" element={<SSOConfiguration />} />
          </Route>

          {/* 404 */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </React.Suspense>
    </BrowserRouter>
  );
};

export default App;
