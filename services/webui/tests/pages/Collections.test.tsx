/**
 * Collections Page Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Collections from '@/client/pages/Collections';

// Mock useAuth - Collections uses user.id for owner check
vi.mock('@/client/hooks/useAuth', () => ({
  useAuth: () => ({
    user: { id: 1, full_name: 'Test User', email: 'test@example.com', role: 'admin' },
    isAuthenticated: true,
    isLoading: false,
  }),
  useAuthStore: vi.fn(),
}));

vi.mock('@/client/lib/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}));

import api from '@/client/lib/api';

const renderWithRouter = (ui: React.ReactElement) =>
  render(<BrowserRouter>{ui}</BrowserRouter>);

const mockCollections = [
  {
    id: 1,
    name: 'My Collection',
    description: 'A great collection',
    owner_id: 1,
    owner_name: 'Test User',
    thumbnail_url: null,
    is_public: false,
    share_token: null,
    share_mode: 'private' as const,
    drawing_count: 3,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
  },
  {
    id: 2,
    name: 'Shared Collection',
    description: null,
    owner_id: 2,
    owner_name: 'Other User',
    thumbnail_url: '/thumb.png',
    is_public: false,
    share_token: 'abc123',
    share_mode: 'link_only' as const,
    drawing_count: 5,
    created_at: '2024-01-03T00:00:00Z',
    updated_at: '2024-01-04T00:00:00Z',
  },
];

const makeCollectionsResponse = (collections = mockCollections, count = collections.length) => ({
  data: { success: true, count, collections },
});

describe('Collections Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (api.get as any).mockResolvedValue(makeCollectionsResponse());
  });

  it('renders page heading', async () => {
    renderWithRouter(<Collections />);
    await waitFor(() => {
      expect(screen.getByText('Collections')).toBeDefined();
    });
  });

  it('shows Create New Collection button', async () => {
    renderWithRouter(<Collections />);
    await waitFor(() => {
      expect(screen.getByText('Create New Collection')).toBeDefined();
    });
  });

  it('shows collection names after fetch', async () => {
    renderWithRouter(<Collections />);
    await waitFor(() => {
      expect(screen.getByText('My Collection')).toBeDefined();
      expect(screen.getByText('Shared Collection')).toBeDefined();
    });
  });

  it('shows share mode badges', async () => {
    renderWithRouter(<Collections />);
    await waitFor(() => {
      expect(screen.getByText('Link sharing')).toBeDefined();
      expect(screen.getByText('Private')).toBeDefined();
    });
  });

  it('shows drawing count for each collection', async () => {
    renderWithRouter(<Collections />);
    await waitFor(() => {
      expect(screen.getByText('3 drawings')).toBeDefined();
      expect(screen.getByText('5 drawings')).toBeDefined();
    });
  });

  it('shows total collection count', async () => {
    (api.get as any).mockResolvedValue(makeCollectionsResponse(mockCollections, 2));
    renderWithRouter(<Collections />);
    await waitFor(() => {
      expect(screen.getByText(/2 collection/)).toBeDefined();
    });
  });

  it('shows empty state when no collections', async () => {
    (api.get as any).mockResolvedValue(makeCollectionsResponse([], 0));
    renderWithRouter(<Collections />);
    await waitFor(() => {
      expect(screen.getByText('No collections yet')).toBeDefined();
    });
  });

  it('shows Create Your First Collection in empty state', async () => {
    (api.get as any).mockResolvedValue(makeCollectionsResponse([], 0));
    renderWithRouter(<Collections />);
    await waitFor(() => {
      expect(screen.getByText('Create Your First Collection')).toBeDefined();
    });
  });

  it('has search input', async () => {
    renderWithRouter(<Collections />);
    await waitFor(() => {
      expect(screen.getByPlaceholderText('Search collections...')).toBeDefined();
    });
  });

  it('has share mode filter', async () => {
    renderWithRouter(<Collections />);
    await waitFor(() => {
      expect(screen.getByText('All Collections')).toBeDefined();
    });
  });

  it('shows delete button only for owned collections', async () => {
    renderWithRouter(<Collections />);
    await waitFor(() => {
      // user.id === 1, only collection with owner_id 1 should show delete button
      const deleteButtons = screen.queryAllByTitle('Delete collection');
      expect(deleteButtons).toHaveLength(1);
    });
  });

  it('refetches when search query changes', async () => {
    renderWithRouter(<Collections />);
    await waitFor(() => {
      expect(screen.getByText('My Collection')).toBeDefined();
    });

    const searchInput = screen.getByPlaceholderText('Search collections...');
    fireEvent.change(searchInput, { target: { value: 'chart' } });

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledTimes(2);
    });
  });

  it('handles API error gracefully', async () => {
    (api.get as any).mockRejectedValue(new Error('Network error'));
    renderWithRouter(<Collections />);
    await waitFor(() => {
      expect(screen.queryByText('My Collection')).toBeNull();
    });
  });

  it('shows no collections found when search has no results', async () => {
    (api.get as any).mockResolvedValueOnce(makeCollectionsResponse()).mockResolvedValueOnce(makeCollectionsResponse([], 0));
    renderWithRouter(<Collections />);
    await waitFor(() => {
      expect(screen.getByText('My Collection')).toBeDefined();
    });

    const searchInput = screen.getByPlaceholderText('Search collections...');
    fireEvent.change(searchInput, { target: { value: 'nonexistent' } });

    await waitFor(() => {
      expect(screen.getByText('No collections found matching your filters')).toBeDefined();
    });
  });
});
