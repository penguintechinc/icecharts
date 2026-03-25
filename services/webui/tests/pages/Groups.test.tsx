/**
 * Groups Page Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Groups from '@/client/pages/Groups';

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

const mockGroups = [
  {
    id: 1,
    name: 'Engineering Team',
    description: 'The engineering group',
    owner_id: 1,
    owner_name: 'Admin User',
    member_count: 8,
    drawing_count: 12,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
  },
  {
    id: 2,
    name: 'Design Team',
    description: null,
    owner_id: 2,
    owner_name: 'Design Lead',
    member_count: 4,
    drawing_count: 7,
    created_at: '2024-01-03T00:00:00Z',
    updated_at: '2024-01-04T00:00:00Z',
  },
];

const makeGroupsResponse = (groups = mockGroups) => ({
  data: { success: true, groups },
});

describe('Groups Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (api.get as any).mockResolvedValue(makeGroupsResponse());
  });

  it('renders page heading', async () => {
    renderWithRouter(<Groups />);
    await waitFor(() => {
      expect(screen.getByText('Groups')).toBeDefined();
    });
  });

  it('shows page subtitle', async () => {
    renderWithRouter(<Groups />);
    await waitFor(() => {
      expect(screen.getByText('Collaborate with team members on drawings')).toBeDefined();
    });
  });

  it('shows Create New Group button', async () => {
    renderWithRouter(<Groups />);
    await waitFor(() => {
      expect(screen.getByText('Create New Group')).toBeDefined();
    });
  });

  it('shows group names after fetch', async () => {
    renderWithRouter(<Groups />);
    await waitFor(() => {
      expect(screen.getByText('Engineering Team')).toBeDefined();
      expect(screen.getByText('Design Team')).toBeDefined();
    });
  });

  it('shows group descriptions', async () => {
    renderWithRouter(<Groups />);
    await waitFor(() => {
      expect(screen.getByText('The engineering group')).toBeDefined();
    });
  });

  it('shows member counts', async () => {
    renderWithRouter(<Groups />);
    await waitFor(() => {
      expect(screen.getByText('8 members')).toBeDefined();
      expect(screen.getByText('4 members')).toBeDefined();
    });
  });

  it('shows drawing counts', async () => {
    renderWithRouter(<Groups />);
    await waitFor(() => {
      expect(screen.getByText('12 drawings')).toBeDefined();
      expect(screen.getByText('7 drawings')).toBeDefined();
    });
  });

  it('shows owner names', async () => {
    renderWithRouter(<Groups />);
    await waitFor(() => {
      expect(screen.getByText('Owner: Admin User')).toBeDefined();
    });
  });

  it('shows empty state when no groups', async () => {
    (api.get as any).mockResolvedValue(makeGroupsResponse([]));
    renderWithRouter(<Groups />);
    await waitFor(() => {
      expect(screen.getByText('No groups yet')).toBeDefined();
    });
  });

  it('shows Create Your First Group in empty state', async () => {
    (api.get as any).mockResolvedValue(makeGroupsResponse([]));
    renderWithRouter(<Groups />);
    await waitFor(() => {
      expect(screen.getByText('Create Your First Group')).toBeDefined();
    });
  });

  it('has search input', async () => {
    renderWithRouter(<Groups />);
    await waitFor(() => {
      expect(screen.getByPlaceholderText('Search groups...')).toBeDefined();
    });
  });

  it('opens create modal when Create New Group is clicked', async () => {
    renderWithRouter(<Groups />);
    await waitFor(() => {
      expect(screen.getByText('Engineering Team')).toBeDefined();
    });

    fireEvent.click(screen.getByText('Create New Group'));

    await waitFor(() => {
      expect(screen.getByText('Create New Group', { selector: 'h2' })).toBeDefined();
      expect(screen.getByPlaceholderText('My Team')).toBeDefined();
    });
  });

  it('closes create modal on Cancel', async () => {
    renderWithRouter(<Groups />);
    await waitFor(() => {
      expect(screen.getByText('Engineering Team')).toBeDefined();
    });

    fireEvent.click(screen.getAllByText('Create New Group')[0]);
    await waitFor(() => {
      expect(screen.getByPlaceholderText('My Team')).toBeDefined();
    });

    fireEvent.click(screen.getByText('Cancel'));
    await waitFor(() => {
      expect(screen.queryByPlaceholderText('My Team')).toBeNull();
    });
  });

  it('creates group and refetches on form submit', async () => {
    (api.post as any).mockResolvedValue({ data: { group: { id: 3, name: 'New Group' } } });

    renderWithRouter(<Groups />);
    await waitFor(() => {
      expect(screen.getByText('Engineering Team')).toBeDefined();
    });

    fireEvent.click(screen.getAllByText('Create New Group')[0]);
    await waitFor(() => {
      expect(screen.getByPlaceholderText('My Team')).toBeDefined();
    });

    fireEvent.change(screen.getByPlaceholderText('My Team'), { target: { value: 'New Group' } });

    const form = screen.getByPlaceholderText('My Team').closest('form');
    fireEvent.submit(form!);

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/groups', {
        name: 'New Group',
        description: undefined,
      });
    });
  });

  it('refetches when search query changes', async () => {
    renderWithRouter(<Groups />);
    await waitFor(() => {
      expect(screen.getByText('Engineering Team')).toBeDefined();
    });

    const searchInput = screen.getByPlaceholderText('Search groups...');
    fireEvent.change(searchInput, { target: { value: 'design' } });

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledTimes(2);
    });
  });

  it('handles API error gracefully', async () => {
    (api.get as any).mockRejectedValue(new Error('Network error'));
    renderWithRouter(<Groups />);
    await waitFor(() => {
      expect(screen.queryByText('Engineering Team')).toBeNull();
    });
  });

  it('shows no groups found when search has no results', async () => {
    (api.get as any).mockResolvedValueOnce(makeGroupsResponse()).mockResolvedValueOnce(makeGroupsResponse([]));
    renderWithRouter(<Groups />);
    await waitFor(() => {
      expect(screen.getByText('Engineering Team')).toBeDefined();
    });

    const searchInput = screen.getByPlaceholderText('Search groups...');
    fireEvent.change(searchInput, { target: { value: 'nonexistent' } });

    await waitFor(() => {
      expect(screen.getByText('No groups found')).toBeDefined();
    });
  });
});
