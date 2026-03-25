/**
 * RoleGuard Component Tests
 *
 * Tests for admin-only redirect, maintainer access, and no-user redirect.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import RoleGuard from '@/client/components/RoleGuard';

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

// Mock useAuth with configurable returns
const mockHasRole = vi.fn();
const mockUseAuth = vi.fn();

vi.mock('@/client/hooks/useAuth', () => ({
  useAuth: () => mockUseAuth(),
  useAuthStore: vi.fn(),
}));

const renderWithRouter = (ui: React.ReactElement) =>
  render(<BrowserRouter>{ui}</BrowserRouter>);

describe('RoleGuard Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('redirects to /login when user is null', async () => {
    mockUseAuth.mockReturnValue({
      user: null,
      hasRole: vi.fn(() => false),
    });

    renderWithRouter(
      <RoleGuard allowedRoles={['admin']}>
        <div>Admin Content</div>
      </RoleGuard>
    );

    await waitFor(() => {
      const nav = screen.getByTestId('navigate');
      expect(nav.getAttribute('data-to')).toBe('/login');
    });
  });

  it('redirects to fallback path when user lacks required role', async () => {
    mockUseAuth.mockReturnValue({
      user: { id: 1, role: 'viewer' },
      hasRole: vi.fn(() => false),
    });

    renderWithRouter(
      <RoleGuard allowedRoles={['admin']} fallbackPath="/dashboard">
        <div>Admin Content</div>
      </RoleGuard>
    );

    await waitFor(() => {
      const nav = screen.getByTestId('navigate');
      expect(nav.getAttribute('data-to')).toBe('/dashboard');
    });
  });

  it('redirects to / by default when user lacks required role', async () => {
    mockUseAuth.mockReturnValue({
      user: { id: 1, role: 'viewer' },
      hasRole: vi.fn(() => false),
    });

    renderWithRouter(
      <RoleGuard allowedRoles={['admin']}>
        <div>Admin Content</div>
      </RoleGuard>
    );

    await waitFor(() => {
      const nav = screen.getByTestId('navigate');
      expect(nav.getAttribute('data-to')).toBe('/');
    });
  });

  it('renders children when user has required role', async () => {
    mockUseAuth.mockReturnValue({
      user: { id: 1, role: 'admin' },
      hasRole: vi.fn(() => true),
    });

    renderWithRouter(
      <RoleGuard allowedRoles={['admin']}>
        <div>Admin Content</div>
      </RoleGuard>
    );

    await waitFor(() => {
      expect(screen.getByText('Admin Content')).toBeDefined();
    });
  });

  it('renders children when maintainer has maintainer role access', async () => {
    mockUseAuth.mockReturnValue({
      user: { id: 2, role: 'maintainer' },
      hasRole: vi.fn(() => true),
    });

    renderWithRouter(
      <RoleGuard allowedRoles={['admin', 'maintainer']}>
        <div>Maintainer Content</div>
      </RoleGuard>
    );

    await waitFor(() => {
      expect(screen.getByText('Maintainer Content')).toBeDefined();
    });
  });
});
