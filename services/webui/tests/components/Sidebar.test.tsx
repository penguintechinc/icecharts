/**
 * Sidebar Component Tests
 *
 * Tests for nav items, role-based filtering, collapse/expand, and user section.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Sidebar from '@/client/components/Sidebar';

// Mock react-router-dom to control location
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useLocation: vi.fn(() => ({ pathname: '/' })),
  };
});

// Mock api
vi.mock('@/client/lib/api', () => ({
  default: {
    get: vi.fn(() => Promise.resolve({ data: { pending_approvals: [] } })),
  },
}));

// Mock useAuth
const mockHasRole = vi.fn();
const mockLogout = vi.fn();
vi.mock('@/client/hooks/useAuth', () => ({
  useAuth: vi.fn(() => ({
    user: {
      id: 1,
      full_name: 'Admin User',
      email: 'admin@test.com',
      role: 'admin',
    },
    isAuthenticated: true,
    isLoading: false,
    logout: mockLogout,
    hasRole: mockHasRole,
  })),
  useAuthStore: vi.fn(),
}));

const renderWithRouter = (ui: React.ReactElement) =>
  render(<BrowserRouter>{ui}</BrowserRouter>);

describe('Sidebar Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Admin role returns true for all role checks
    mockHasRole.mockReturnValue(true);
  });

  it('renders the WebUI brand name when not collapsed', () => {
    renderWithRouter(<Sidebar collapsed={false} onToggle={vi.fn()} />);
    expect(screen.getByText('WebUI')).toBeDefined();
  });

  it('hides the brand name when collapsed', () => {
    renderWithRouter(<Sidebar collapsed={true} onToggle={vi.fn()} />);
    expect(screen.queryByText('WebUI')).toBeNull();
  });

  it('renders Dashboard nav link', async () => {
    renderWithRouter(<Sidebar collapsed={false} onToggle={vi.fn()} />);
    await waitFor(() => {
      expect(screen.getByText('Dashboard')).toBeDefined();
    });
  });

  it('renders admin-only navigation items for admin user', async () => {
    renderWithRouter(<Sidebar collapsed={false} onToggle={vi.fn()} />);
    await waitFor(() => {
      expect(screen.getByText('Users')).toBeDefined();
    });
  });

  it('calls onToggle when toggle button is clicked', () => {
    const onToggle = vi.fn();
    renderWithRouter(<Sidebar collapsed={false} onToggle={onToggle} />);
    const toggleButton = screen.getByTitle('Collapse');
    fireEvent.click(toggleButton);
    expect(onToggle).toHaveBeenCalledTimes(1);
  });

  it('shows expand title on toggle button when collapsed', () => {
    renderWithRouter(<Sidebar collapsed={true} onToggle={vi.fn()} />);
    expect(screen.getByTitle('Expand')).toBeDefined();
  });

  it('renders user full name and email when not collapsed', async () => {
    renderWithRouter(<Sidebar collapsed={false} onToggle={vi.fn()} />);
    await waitFor(() => {
      expect(screen.getByText('Admin User')).toBeDefined();
      expect(screen.getByText('admin@test.com')).toBeDefined();
    });
  });

  it('calls logout when logout button is clicked', () => {
    renderWithRouter(<Sidebar collapsed={false} onToggle={vi.fn()} />);
    const logoutButton = screen.getByTitle('Logout');
    fireEvent.click(logoutButton);
    expect(mockLogout).toHaveBeenCalledTimes(1);
  });
});
