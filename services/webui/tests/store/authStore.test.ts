/**
 * Auth Store Tests (Zustand)
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { act } from '@testing-library/react';

// Mock dependencies before importing the store
vi.mock('@/lib/api', () => ({
  api: {
    auth: {
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      me: vi.fn(),
      refreshToken: vi.fn(),
    },
  },
  default: { get: vi.fn(), post: vi.fn() },
}));

vi.mock('@/lib/websocket', () => ({
  wsClient: {
    connect: vi.fn(),
    disconnect: vi.fn(),
  },
}));

import { useAuthStore } from '@/store/authStore';
import { api } from '@/lib/api';
import { wsClient } from '@/lib/websocket';

const mockUser = {
  id: 1,
  email: 'test@example.com',
  full_name: 'Test User',
  role: 'admin' as const,
  is_active: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: null,
};

describe('authStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset store to initial state
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: true,
      error: null,
    });
    (localStorage.getItem as ReturnType<typeof vi.fn>).mockReturnValue(null);
    (localStorage.setItem as ReturnType<typeof vi.fn>).mockImplementation(() => {});
    (localStorage.removeItem as ReturnType<typeof vi.fn>).mockImplementation(() => {});
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Initial State', () => {
    it('has null user initially', () => {
      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
    });

    it('is not authenticated initially', () => {
      const state = useAuthStore.getState();
      expect(state.isAuthenticated).toBe(false);
    });

    it('has null error initially', () => {
      const state = useAuthStore.getState();
      expect(state.error).toBeNull();
    });
  });

  describe('login', () => {
    it('sets user and token on successful login', async () => {
      (api.auth.login as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: { access_token: 'test-token', user: mockUser },
      });

      await act(async () => {
        await useAuthStore.getState().login('test@example.com', 'password');
      });

      const state = useAuthStore.getState();
      expect(state.user).toEqual(mockUser);
      expect(state.token).toBe('test-token');
      expect(state.isAuthenticated).toBe(true);
      expect(state.isLoading).toBe(false);
    });

    it('stores token in localStorage on login', async () => {
      (api.auth.login as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: { access_token: 'test-token', user: mockUser },
      });

      await act(async () => {
        await useAuthStore.getState().login('test@example.com', 'password');
      });

      expect(localStorage.setItem).toHaveBeenCalledWith('authToken', 'test-token');
    });

    it('connects WebSocket on login', async () => {
      (api.auth.login as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: { access_token: 'test-token', user: mockUser },
      });

      await act(async () => {
        await useAuthStore.getState().login('test@example.com', 'password');
      });

      expect(wsClient.connect).toHaveBeenCalledWith('test-token');
    });

    it('sets error on login failure', async () => {
      (api.auth.login as ReturnType<typeof vi.fn>).mockRejectedValue(
        new Error('Invalid credentials')
      );

      await act(async () => {
        try {
          await useAuthStore.getState().login('bad@example.com', 'wrong');
        } catch {
          // expected
        }
      });

      const state = useAuthStore.getState();
      expect(state.error).toBe('Invalid credentials');
      expect(state.isAuthenticated).toBe(false);
    });

    it('sets isLoading false after login attempt', async () => {
      (api.auth.login as ReturnType<typeof vi.fn>).mockRejectedValue(
        new Error('Login failed')
      );

      await act(async () => {
        try {
          await useAuthStore.getState().login('bad@example.com', 'wrong');
        } catch {
          // expected
        }
      });

      expect(useAuthStore.getState().isLoading).toBe(false);
    });
  });

  describe('logout', () => {
    it('clears user and token on logout', async () => {
      // Set authenticated state first
      useAuthStore.setState({
        user: mockUser,
        token: 'test-token',
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });

      (api.auth.logout as ReturnType<typeof vi.fn>).mockResolvedValue({});

      await act(async () => {
        await useAuthStore.getState().logout();
      });

      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.token).toBeNull();
      expect(state.isAuthenticated).toBe(false);
    });

    it('removes token from localStorage on logout', async () => {
      useAuthStore.setState({
        user: mockUser,
        token: 'test-token',
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });

      (api.auth.logout as ReturnType<typeof vi.fn>).mockResolvedValue({});

      await act(async () => {
        await useAuthStore.getState().logout();
      });

      expect(localStorage.removeItem).toHaveBeenCalledWith('authToken');
    });

    it('disconnects WebSocket on logout', async () => {
      (api.auth.logout as ReturnType<typeof vi.fn>).mockResolvedValue({});

      await act(async () => {
        await useAuthStore.getState().logout();
      });

      expect(wsClient.disconnect).toHaveBeenCalled();
    });

    it('clears auth even when API logout fails', async () => {
      useAuthStore.setState({
        user: mockUser,
        token: 'test-token',
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });

      (api.auth.logout as ReturnType<typeof vi.fn>).mockRejectedValue(
        new Error('Network error')
      );

      await act(async () => {
        await useAuthStore.getState().logout();
      });

      // Even on error, auth should be cleared (finally block)
      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
    });
  });

  describe('updateUser', () => {
    it('merges partial user updates', () => {
      useAuthStore.setState({ user: mockUser, isAuthenticated: true });

      act(() => {
        useAuthStore.getState().updateUser({ full_name: 'Updated Name' });
      });

      expect(useAuthStore.getState().user?.full_name).toBe('Updated Name');
      expect(useAuthStore.getState().user?.email).toBe('test@example.com');
    });

    it('stores updated user in localStorage', () => {
      useAuthStore.setState({ user: mockUser, isAuthenticated: true });

      act(() => {
        useAuthStore.getState().updateUser({ full_name: 'Updated Name' });
      });

      expect(localStorage.setItem).toHaveBeenCalledWith(
        'user',
        expect.stringContaining('Updated Name')
      );
    });

    it('does nothing when user is null', () => {
      useAuthStore.setState({ user: null });

      act(() => {
        useAuthStore.getState().updateUser({ full_name: 'Updated Name' });
      });

      expect(useAuthStore.getState().user).toBeNull();
    });
  });

  describe('clearError', () => {
    it('clears the error state', () => {
      useAuthStore.setState({ error: 'Some error' });

      act(() => {
        useAuthStore.getState().clearError();
      });

      expect(useAuthStore.getState().error).toBeNull();
    });
  });

  describe('initAuth', () => {
    it('restores auth state from localStorage when token and user exist', () => {
      const userStr = JSON.stringify(mockUser);
      (localStorage.getItem as ReturnType<typeof vi.fn>).mockImplementation((key: string) => {
        if (key === 'authToken') return 'stored-token';
        if (key === 'user') return userStr;
        return null;
      });

      (api.auth.me as ReturnType<typeof vi.fn>).mockResolvedValue({ data: mockUser });

      act(() => {
        useAuthStore.getState().initAuth();
      });

      const state = useAuthStore.getState();
      expect(state.isAuthenticated).toBe(true);
      expect(state.token).toBe('stored-token');
    });

    it('sets isLoading false when no stored token', () => {
      (localStorage.getItem as ReturnType<typeof vi.fn>).mockReturnValue(null);

      act(() => {
        useAuthStore.getState().initAuth();
      });

      expect(useAuthStore.getState().isLoading).toBe(false);
    });

    it('connects WebSocket when restoring auth', () => {
      const userStr = JSON.stringify(mockUser);
      (localStorage.getItem as ReturnType<typeof vi.fn>).mockImplementation((key: string) => {
        if (key === 'authToken') return 'stored-token';
        if (key === 'user') return userStr;
        return null;
      });

      (api.auth.me as ReturnType<typeof vi.fn>).mockResolvedValue({ data: mockUser });

      act(() => {
        useAuthStore.getState().initAuth();
      });

      expect(wsClient.connect).toHaveBeenCalledWith('stored-token');
    });
  });

  describe('register', () => {
    it('sets user and token on successful registration', async () => {
      (api.auth.register as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: { access_token: 'new-token', user: mockUser },
      });

      await act(async () => {
        await useAuthStore.getState().register('new@example.com', 'password', 'New User');
      });

      const state = useAuthStore.getState();
      expect(state.user).toEqual(mockUser);
      expect(state.isAuthenticated).toBe(true);
    });

    it('sets error on registration failure', async () => {
      (api.auth.register as ReturnType<typeof vi.fn>).mockRejectedValue(
        new Error('Email already exists')
      );

      await act(async () => {
        try {
          await useAuthStore.getState().register('existing@example.com', 'password', 'User');
        } catch {
          // expected
        }
      });

      expect(useAuthStore.getState().error).toBe('Email already exists');
    });
  });
});
