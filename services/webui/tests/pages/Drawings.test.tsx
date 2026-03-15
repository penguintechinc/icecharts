/**
 * Drawings Page Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Drawings from '@/client/pages/Drawings';

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

const mockDrawings = [
  {
    id: 1,
    name: 'My First Drawing',
    description: 'A test drawing',
    visibility: 'private' as const,
    thumbnail_url: null,
    owner_id: 1,
    owner_name: 'Test User',
    group_id: null,
    group_name: null,
    is_template: false,
    content: {},
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
  },
  {
    id: 2,
    name: 'Public Drawing',
    description: null,
    visibility: 'public' as const,
    thumbnail_url: '/thumb.png',
    owner_id: 1,
    owner_name: 'Test User',
    group_id: null,
    group_name: null,
    is_template: true,
    content: {},
    created_at: '2024-01-03T00:00:00Z',
    updated_at: '2024-01-04T00:00:00Z',
  },
];

const makeDrawingsResponse = (drawings = mockDrawings, count = drawings.length) => ({
  data: { success: true, count, drawings },
});

describe('Drawings Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (api.get as any).mockResolvedValue(makeDrawingsResponse());
  });

  it('renders page heading', async () => {
    renderWithRouter(<Drawings />);
    await waitFor(() => {
      expect(screen.getByText('Drawings')).toBeDefined();
    });
  });

  it('shows Create New Drawing button', async () => {
    renderWithRouter(<Drawings />);
    await waitFor(() => {
      expect(screen.getByText('Create New Drawing')).toBeDefined();
    });
  });

  it('shows drawing names after fetch', async () => {
    renderWithRouter(<Drawings />);
    await waitFor(() => {
      expect(screen.getByText('My First Drawing')).toBeDefined();
      expect(screen.getByText('Public Drawing')).toBeDefined();
    });
  });

  it('shows visibility badges', async () => {
    renderWithRouter(<Drawings />);
    await waitFor(() => {
      expect(screen.getByText('private')).toBeDefined();
      expect(screen.getByText('public')).toBeDefined();
    });
  });

  it('shows template badge for template drawings', async () => {
    renderWithRouter(<Drawings />);
    await waitFor(() => {
      expect(screen.getByText('template')).toBeDefined();
    });
  });

  it('shows total count', async () => {
    (api.get as any).mockResolvedValue(makeDrawingsResponse(mockDrawings, 2));
    renderWithRouter(<Drawings />);
    await waitFor(() => {
      expect(screen.getByText(/2 drawing/)).toBeDefined();
    });
  });

  it('shows empty state when no drawings', async () => {
    (api.get as any).mockResolvedValue(makeDrawingsResponse([], 0));
    renderWithRouter(<Drawings />);
    await waitFor(() => {
      expect(screen.getByText('No drawings yet')).toBeDefined();
    });
  });

  it('shows Create Your First Drawing in empty state', async () => {
    (api.get as any).mockResolvedValue(makeDrawingsResponse([], 0));
    renderWithRouter(<Drawings />);
    await waitFor(() => {
      expect(screen.getByText('Create Your First Drawing')).toBeDefined();
    });
  });

  it('has search input', async () => {
    renderWithRouter(<Drawings />);
    await waitFor(() => {
      expect(screen.getByPlaceholderText('Search drawings...')).toBeDefined();
    });
  });

  it('has visibility filter select', async () => {
    renderWithRouter(<Drawings />);
    await waitFor(() => {
      expect(screen.getByText('All Drawings')).toBeDefined();
    });
  });

  it('refetches when search query changes', async () => {
    renderWithRouter(<Drawings />);
    await waitFor(() => {
      expect(screen.getByText('My First Drawing')).toBeDefined();
    });

    const searchInput = screen.getByPlaceholderText('Search drawings...');
    fireEvent.change(searchInput, { target: { value: 'chart' } });

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledTimes(2);
    });
  });

  it('handles API error gracefully', async () => {
    (api.get as any).mockRejectedValue(new Error('Network error'));
    renderWithRouter(<Drawings />);
    await waitFor(() => {
      // Should show empty state or not crash
      expect(screen.queryByText('My First Drawing')).toBeNull();
    });
  });

  it('shows no drawings found message when search has no results', async () => {
    (api.get as any).mockResolvedValueOnce(makeDrawingsResponse()).mockResolvedValueOnce(makeDrawingsResponse([], 0));
    renderWithRouter(<Drawings />);
    await waitFor(() => {
      expect(screen.getByText('My First Drawing')).toBeDefined();
    });

    const searchInput = screen.getByPlaceholderText('Search drawings...');
    fireEvent.change(searchInput, { target: { value: 'nonexistent' } });

    await waitFor(() => {
      expect(screen.getByText('No drawings found matching your filters')).toBeDefined();
    });
  });
});
