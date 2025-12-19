import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './store/authStore';
import { Layout } from './components/layout';

// Lazy load pages for code splitting
const Dashboard = React.lazy(() => import('./pages/Dashboard'));
const Login = React.lazy(() => import('./pages/Login'));
const Register = React.lazy(() => import('./pages/Register'));
const DrawingEditor = React.lazy(() => import('./client/pages/DrawingEditor'));
const DrawingDetail = React.lazy(() => import('./client/pages/DrawingDetail'));
const NotFound = React.lazy(() => import('./pages/NotFound'));
const Drawings = React.lazy(() => import('./client/pages/Drawings'));
const Collections = React.lazy(() => import('./client/pages/Collections'));
const Groups = React.lazy(() => import('./client/pages/Groups'));
const GroupDetail = React.lazy(() => import('./client/pages/GroupDetail'));
const Templates = React.lazy(() => import('./client/pages/Templates'));
const Settings = React.lazy(() => import('./client/pages/Settings'));
const AdminUsers = React.lazy(() => import('./client/pages/Users'));
const AdminDashboard = React.lazy(() => import('./client/pages/AdminDashboard'));
const SSOConfiguration = React.lazy(() => import('./client/pages/SSOConfiguration'));
const StorageConfiguration = React.lazy(() => import('./client/pages/Admin/StorageConfiguration'));
const VerifyEmail = React.lazy(() => import('./client/pages/VerifyEmail'));
const SharedDrawing = React.lazy(() => import('./pages/SharedDrawing'));
const SharedCollectionView = React.lazy(() => import('./pages/SharedCollectionView'));

// IceStreams - Playbooks
const PlaybookList = React.lazy(() => import('./client/pages/playbooks/PlaybookList'));
const PlaybookEditor = React.lazy(() => import('./client/pages/playbooks/PlaybookEditor'));
const PlaybookDetail = React.lazy(() => import('./client/pages/playbooks/PlaybookDetail'));
const PlaybookTemplates = React.lazy(() => import('./client/pages/playbooks/PlaybookTemplates'));
const PlaybookCollections = React.lazy(() => import('./client/pages/playbooks/PlaybookCollections'));
const DiagramCollections = React.lazy(() => import('./client/pages/collections/DiagramCollections'));

// Protected route wrapper
interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: string;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, requiredRole }) => {
  const { isAuthenticated, isLoading, user } = useAuthStore();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-ice-navy-900">
        <div className="animate-pulse text-ice-gold-400 text-xl">Loading...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (requiredRole && user?.role !== requiredRole) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};

// Loading fallback component
const LoadingFallback: React.FC = () => (
  <div className="flex items-center justify-center min-h-screen bg-ice-navy-900">
    <div className="animate-pulse text-ice-gold-400 text-xl">Loading...</div>
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
          <Route path="/verify-email/:token" element={<VerifyEmail />} />
          <Route path="/shared/drawings/:token" element={<SharedDrawing />} />
          <Route path="/shared/collections/:token" element={<SharedCollectionView />} />

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
            <Route path="/drawings/:id/edit" element={<DrawingEditor />} />
            <Route path="/drawings/:id" element={<DrawingDetail />} />
            <Route path="/collections" element={<Collections />} />
            <Route path="/collections/:id" element={<Collections />} />
            <Route path="/collections/diagrams" element={<DiagramCollections />} />
            <Route path="/collections/playbooks" element={<PlaybookCollections />} />
            <Route path="/groups" element={<Groups />} />
            <Route path="/groups/:id" element={<GroupDetail />} />
            <Route path="/templates" element={<Templates />} />

            {/* IceStreams - Playbooks (Workflows) */}
            <Route path="/playbooks" element={<PlaybookList />} />
            <Route path="/playbooks/new" element={<PlaybookEditor />} />
            <Route path="/playbooks/templates" element={<PlaybookTemplates />} />
            <Route path="/playbooks/:id" element={<PlaybookDetail />} />
            <Route path="/playbooks/:id/edit" element={<PlaybookEditor />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/admin/users" element={<AdminUsers />} />
            <Route path="/admin/dashboard" element={<ProtectedRoute requiredRole="admin"><AdminDashboard /></ProtectedRoute>} />
            <Route path="/admin/sso" element={<SSOConfiguration />} />
            <Route path="/admin/storage" element={<StorageConfiguration />} />
          </Route>

          {/* 404 */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </React.Suspense>
    </BrowserRouter>
  );
};

export default App;
