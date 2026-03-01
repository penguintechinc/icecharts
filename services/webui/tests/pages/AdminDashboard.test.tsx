/**
 * AdminDashboard Page Tests
 *
 * Tests for stats overview, access control, and chart rendering.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';

// Mock recharts to avoid canvas/SVG rendering issues in happy-dom
vi.mock('recharts', () => ({
  LineChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="line-chart">{children}</div>
  ),
  BarChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="bar-chart">{children}</div>
  ),
  PieChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="pie-chart">{children}</div>
  ),
  Line: () => null,
  Bar: () => null,
  Pie: () => null,
  Cell: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  Legend: () => null,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
}));

// Mock Card component
vi.mock('@/client/components/Card', () => ({
  default: ({ children, title }: { children: React.ReactNode; title?: string }) => (
    <div data-testid="card">
      {title && <h2>{title}</h2>}
      {children}
    </div>
  ),
}));

// Mock api module
vi.mock('@/client/lib/api', () => ({
  default: {
    get: vi.fn(),
  },
}));

// Use a mutable object to control auth state per test
const authState = {
  user: { id: 1, username: 'admin', role: 'admin', email: 'admin@test.com' },
  isAuthenticated: true,
  isLoading: false,
  isAdmin: () => true,
  checkAuth: vi.fn().mockResolvedValue(true),
};

vi.mock('@/client/hooks/useAuth', () => ({
  useAuth: () => ({ ...authState }),
  useAuthStore: vi.fn(),
}));

import AdminDashboard from '@/client/pages/AdminDashboard';
import api from '@/client/lib/api';

const mockStats = {
  total_users: 150,
  active_users: 75,
  new_users: 10,
  verified_users: 130,
  total_drawings: 500,
  drawings_created: 20,
  public_drawings: 80,
  template_drawings: 30,
  total_collections: 40,
  collections_created: 5,
  total_drawing_shares: 200,
  shares_by_type: { user: 100, group: 50, public: 50 },
  shares_by_permission: { viewer: 120, editor: 60, admin: 20 },
  active_collaborations: 15,
  total_collaboration_sessions: 300,
  login_count: 450,
  email_verifications_sent: 140,
  email_verifications_completed: 130,
  email_verification_rate: 92.8,
  share_views: 1200,
  share_views_by_type: { drawing: 1000, collection: 200 },
  database_size_mb: 256.5,
  storage_used_gb: 4.2,
};

const renderWithRouter = (ui: React.ReactElement) =>
  render(<BrowserRouter>{ui}</BrowserRouter>);

describe('AdminDashboard Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Reset to admin user state
    authState.user = { id: 1, username: 'admin', role: 'admin', email: 'admin@test.com' };
    authState.isAdmin = () => true;
    authState.isLoading = false;
    authState.checkAuth = vi.fn().mockResolvedValue(true);

    const getMock = api.get as ReturnType<typeof vi.fn>;
    getMock.mockImplementation((url: string) => {
      if (url.includes('dashboard')) {
        return Promise.resolve({ data: mockStats });
      }
      if (url.includes('time-series')) {
        return Promise.resolve({ data: { data: [] } });
      }
      if (url.includes('top-users')) {
        return Promise.resolve({ data: { users: [] } });
      }
      if (url.includes('top-drawings')) {
        return Promise.resolve({ data: { drawings: [] } });
      }
      return Promise.resolve({ data: {} });
    });
  });

  it('renders Admin Dashboard heading', async () => {
    renderWithRouter(<AdminDashboard />);
    await waitFor(() => {
      expect(screen.getByText('Admin Dashboard')).toBeDefined();
    }, { timeout: 5000 });
  });

  it('renders Total Users stat card with value', async () => {
    renderWithRouter(<AdminDashboard />);
    await waitFor(() => {
      expect(screen.getByText('Total Users')).toBeDefined();
      expect(screen.getByText('150')).toBeDefined();
    }, { timeout: 5000 });
  });

  it('renders Total Drawings stat card', async () => {
    renderWithRouter(<AdminDashboard />);
    await waitFor(() => {
      expect(screen.getByText('Total Drawings')).toBeDefined();
      expect(screen.getByText('500')).toBeDefined();
    }, { timeout: 5000 });
  });

  it('renders System Health section', async () => {
    renderWithRouter(<AdminDashboard />);
    await waitFor(() => {
      expect(screen.getByText('System Health')).toBeDefined();
    }, { timeout: 5000 });
  });

  it('shows Access Denied when user is not admin', async () => {
    authState.user = { id: 2, username: 'viewer', role: 'viewer', email: 'viewer@test.com' };
    authState.isAdmin = () => false;

    renderWithRouter(<AdminDashboard />);
    await waitFor(() => {
      expect(screen.getByText('Access Denied')).toBeDefined();
    });
  });
});
