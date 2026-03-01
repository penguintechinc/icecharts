/**
 * ProtectedRoute Component Tests
 *
 * Tests for redirecting unauthenticated users, loading state, and rendering children.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import ProtectedRoute from '@/client/components/ProtectedRoute';

// Mock useAuth
const mockCheckAuth = vi.fn();
const mockUseAuth = vi.fn();

vi.mock('@/client/hooks/useAuth', () => ({
  useAuth: () => mockUseAuth(),
  useAuthStore: vi.fn(),
}));

// Mock Navigate so we can detect redirects
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    Navigate: ({ to }: { to: string }) => (
      <div data-testid="navigate" data-to={to}>
        Redirecting to {to}
      </div>
    ),
  };
});

const renderWithRouter = (ui: React.ReactElement) =>
  render(<BrowserRouter>{ui}</BrowserRouter>);

describe('ProtectedRoute Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockCheckAuth.mockResolvedValue(true);
  });

  it('shows loading spinner while auth is being checked', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      isLoading: true,
      checkAuth: mockCheckAuth,
    });

    renderWithRouter(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    expect(screen.getByText('Loading...')).toBeDefined();
  });

  it('redirects to /login when user is not authenticated', async () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      checkAuth: mockCheckAuth,
    });

    renderWithRouter(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    await waitFor(() => {
      const navigateEl = screen.getByTestId('navigate');
      expect(navigateEl.getAttribute('data-to')).toBe('/login');
    });
  });

  it('renders children when user is authenticated', async () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      checkAuth: mockCheckAuth,
    });

    renderWithRouter(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    await waitFor(() => {
      expect(screen.getByText('Protected Content')).toBeDefined();
    });
  });

  it('does not render protected content when not authenticated', async () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: false,
      isLoading: false,
      checkAuth: mockCheckAuth,
    });

    renderWithRouter(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    await waitFor(() => {
      expect(screen.queryByText('Protected Content')).toBeNull();
    });
  });

  it('calls checkAuth on mount', () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      checkAuth: mockCheckAuth,
    });

    renderWithRouter(
      <ProtectedRoute>
        <div>Content</div>
      </ProtectedRoute>
    );

    expect(mockCheckAuth).toHaveBeenCalledTimes(1);
  });

  it('does not show loading screen when auth check is complete', async () => {
    mockUseAuth.mockReturnValue({
      isAuthenticated: true,
      isLoading: false,
      checkAuth: mockCheckAuth,
    });

    renderWithRouter(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    await waitFor(() => {
      expect(screen.queryByText('Loading...')).toBeNull();
    });
  });
});
