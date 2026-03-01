/**
 * Dashboard Page Tests
 *
 * Tests for the Dashboard page which shows stats cards and recent drawings/groups.
 * The page uses the `api` module (axios-based) not raw fetch.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Dashboard from '@/client/pages/Dashboard';

// Mock useAuth
vi.mock('@/client/hooks/useAuth', () => ({
  useAuth: () => ({
    user: { id: 1, full_name: 'Test User', email: 'test@example.com', role: 'admin' },
    isAuthenticated: true,
    isLoading: false,
  }),
  useAuthStore: vi.fn(),
}));

// Mock the api module
vi.mock('@/client/lib/api', () => ({
  default: {
    get: vi.fn(),
  },
}));

// Mock Card component
vi.mock('@/client/components/Card', () => ({
  default: ({ title, children }: { title?: string; children: React.ReactNode }) => (
    <div data-testid="card">
      {title && <h3>{title}</h3>}
      {children}
    </div>
  ),
}));

import api from '@/client/lib/api';

const renderWithRouter = (ui: React.ReactElement) =>
  render(<BrowserRouter>{ui}</BrowserRouter>);

const mockDrawingsResponse = {
  data: {
    items: [
      {
        id: 1,
        name: 'Test Drawing',
        description: null,
        thumbnail_url: null,
        updated_at: '2024-01-01T00:00:00Z',
        group_name: null,
      },
      {
        id: 2,
        name: 'Another Drawing',
        description: 'Some desc',
        thumbnail_url: '/thumb.png',
        updated_at: '2024-01-02T00:00:00Z',
        group_name: 'My Group',
      },
    ],
  },
};

const mockGroupsResponse = {
  data: {
    items: [
      {
        id: 1,
        name: 'My Group',
        description: 'A test group',
        member_count: 5,
        drawing_count: 10,
      },
    ],
  },
};

const mockStatsResponse = {
  data: {
    totalDrawings: 42,
    totalGroups: 7,
    sharedDrawings: 3,
  },
};

describe('Dashboard Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (api.get as any).mockImplementation((url: string) => {
      if (url.includes('/drawings')) return Promise.resolve(mockDrawingsResponse);
      if (url.includes('/groups')) return Promise.resolve(mockGroupsResponse);
      if (url.includes('/dashboard/stats')) return Promise.resolve(mockStatsResponse);
      return Promise.resolve({ data: {} });
    });
  });

  it('renders dashboard heading', async () => {
    renderWithRouter(<Dashboard />);
    await waitFor(() => {
      expect(screen.getByText('Dashboard')).toBeDefined();
    });
  });

  it('shows welcome message with user name', async () => {
    renderWithRouter(<Dashboard />);
    await waitFor(() => {
      expect(screen.getByText(/welcome back/i)).toBeDefined();
    });
  });

  it('shows loading skeleton initially', () => {
    // Make the API calls hang to observe loading state
    (api.get as any).mockImplementation(() => new Promise(() => {}));
    renderWithRouter(<Dashboard />);
    // Loading state renders pulse animation divs
    const cards = screen.getAllByTestId('card');
    expect(cards.length).toBeGreaterThan(0);
  });

  it('renders stats cards with correct titles', async () => {
    renderWithRouter(<Dashboard />);
    await waitFor(() => {
      expect(screen.getByText('My Drawings')).toBeDefined();
      expect(screen.getByText('My Groups')).toBeDefined();
      expect(screen.getByText('Shared with Me')).toBeDefined();
    });
  });

  it('displays stats values after data loads', async () => {
    renderWithRouter(<Dashboard />);
    await waitFor(() => {
      expect(screen.getByText('42')).toBeDefined();
      expect(screen.getByText('7')).toBeDefined();
      expect(screen.getByText('3')).toBeDefined();
    });
  });

  it('shows recent drawings section heading', async () => {
    renderWithRouter(<Dashboard />);
    await waitFor(() => {
      expect(screen.getByText('Recent Drawings')).toBeDefined();
    });
  });

  it('displays drawing names after data loads', async () => {
    renderWithRouter(<Dashboard />);
    await waitFor(() => {
      expect(screen.getByText('Test Drawing')).toBeDefined();
      expect(screen.getByText('Another Drawing')).toBeDefined();
    });
  });

  it('shows empty state when no drawings', async () => {
    (api.get as any).mockImplementation((url: string) => {
      if (url.includes('/drawings')) return Promise.resolve({ data: { items: [] } });
      if (url.includes('/groups')) return Promise.resolve({ data: { items: [] } });
      if (url.includes('/dashboard/stats')) return Promise.resolve(mockStatsResponse);
      return Promise.resolve({ data: {} });
    });

    renderWithRouter(<Dashboard />);
    await waitFor(() => {
      expect(screen.getByText('No drawings yet')).toBeDefined();
    });
  });
});
