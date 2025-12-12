// Re-export the main auth store and provide convenience helpers
import { useAuthStore } from '../../store/authStore';
import { api } from '../../lib/api';
import apiClient from '../../lib/api';

// Hook for components - wraps the main auth store with additional helpers
export const useAuth = () => {
  const store = useAuthStore();

  return {
    user: store.user,
    isAuthenticated: store.isAuthenticated,
    isLoading: store.isLoading,
    login: async (credentials: { email: string; password: string }) => {
      await store.login(credentials.email, credentials.password);
    },
    logout: store.logout,
    setUser: store.updateUser,
    checkAuth: async () => {
      // Re-verify auth by calling /auth/me
      try {
        const response = await api.auth.me();
        store.updateUser(response.data);
        return true;
      } catch {
        await store.logout();
        return false;
      }
    },
    verifyEmail: async (token: string) => {
      const response = await apiClient.get(`/auth/verify-email/${token}`);
      const { access_token, user } = response.data;
      localStorage.setItem('authToken', access_token);
      localStorage.setItem('user', JSON.stringify(user));
      store.updateUser(user);
    },
    resendVerification: async () => {
      await apiClient.post('/auth/resend-verification');
    },
    hasRole: (roles: string[]) => {
      if (!store.user) return false;
      return roles.includes(store.user.role);
    },
    isAdmin: () => store.user?.role === 'admin',
    isMaintainer: () => store.user?.role === 'maintainer',
    isViewer: () => store.user?.role === 'viewer',
  };
};

// Re-export the store for direct access if needed
export { useAuthStore };
