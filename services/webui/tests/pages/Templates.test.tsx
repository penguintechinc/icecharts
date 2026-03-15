/**
 * Templates Page Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Templates from '@/client/pages/Templates';

vi.mock('@/client/lib/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

import api from '@/client/lib/api';

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-router-dom')>();
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

const renderWithRouter = (ui: React.ReactElement) =>
  render(<BrowserRouter>{ui}</BrowserRouter>);

const mockTemplates = [
  {
    id: 1,
    name: 'Network Diagram',
    description: 'A network topology template',
    category: 'Infrastructure',
    thumbnail_url: null,
    content: {},
    created_by: 1,
    created_by_name: 'Admin',
    usage_count: 42,
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 2,
    name: 'Flow Chart',
    description: null,
    category: 'Process',
    thumbnail_url: '/thumb.png',
    content: {},
    created_by: 1,
    created_by_name: 'Admin',
    usage_count: 15,
    created_at: '2024-01-02T00:00:00Z',
  },
];

const makeTemplatesResponse = (templates = mockTemplates) => ({
  data: { success: true, templates },
});

describe('Templates Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockNavigate.mockClear();
    (api.get as any).mockResolvedValue(makeTemplatesResponse());
  });

  it('renders page heading', async () => {
    renderWithRouter(<Templates />);
    await waitFor(() => {
      expect(screen.getByText('Templates')).toBeDefined();
    });
  });

  it('shows page subtitle', async () => {
    renderWithRouter(<Templates />);
    await waitFor(() => {
      expect(screen.getByText('Start from a template to speed up your workflow')).toBeDefined();
    });
  });

  it('shows template names after fetch', async () => {
    renderWithRouter(<Templates />);
    await waitFor(() => {
      expect(screen.getByText('Network Diagram')).toBeDefined();
      expect(screen.getByText('Flow Chart')).toBeDefined();
    });
  });

  it('shows template categories', async () => {
    renderWithRouter(<Templates />);
    await waitFor(() => {
      // Category badges render inside the template cards
      const infraItems = screen.getAllByText('Infrastructure');
      expect(infraItems.length).toBeGreaterThanOrEqual(1);
    });
  });

  it('shows usage counts', async () => {
    renderWithRouter(<Templates />);
    await waitFor(() => {
      expect(screen.getByText('42 uses')).toBeDefined();
      expect(screen.getByText('15 uses')).toBeDefined();
    });
  });

  it('shows creator names', async () => {
    renderWithRouter(<Templates />);
    await waitFor(() => {
      const adminItems = screen.getAllByText('By Admin');
      expect(adminItems.length).toBeGreaterThanOrEqual(1);
    });
  });

  it('shows All Templates filter button', async () => {
    renderWithRouter(<Templates />);
    await waitFor(() => {
      expect(screen.getByText('All Templates')).toBeDefined();
    });
  });

  it('shows category filter buttons extracted from templates', async () => {
    renderWithRouter(<Templates />);
    await waitFor(() => {
      // Category buttons in the filter area
      expect(screen.getByText('Process')).toBeDefined();
    });
  });

  it('shows empty state when no templates', async () => {
    (api.get as any).mockResolvedValue(makeTemplatesResponse([]));
    renderWithRouter(<Templates />);
    await waitFor(() => {
      expect(screen.getByText('No templates available')).toBeDefined();
    });
  });

  it('refetches when category filter changes', async () => {
    renderWithRouter(<Templates />);
    await waitFor(() => {
      expect(screen.getByText('Network Diagram')).toBeDefined();
    });

    const processButton = screen.getByText('Process');
    fireEvent.click(processButton);

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledTimes(2);
    });
  });

  it('calls use template API and navigates on success', async () => {
    (api.post as any).mockResolvedValue({
      data: { drawing: { id: 99 } },
    });

    renderWithRouter(<Templates />);
    await waitFor(() => {
      expect(screen.getByText('Network Diagram')).toBeDefined();
    });

    // Hover the template card to make Use Template button visible
    const useTemplateButtons = screen.getAllByText('Use Template');
    fireEvent.click(useTemplateButtons[0]);

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/templates/1/use', expect.any(Object));
      expect(mockNavigate).toHaveBeenCalledWith('/drawings/99');
    });
  });

  it('handles fetch error gracefully', async () => {
    (api.get as any).mockRejectedValue(new Error('Network error'));
    renderWithRouter(<Templates />);
    await waitFor(() => {
      expect(screen.queryByText('Network Diagram')).toBeNull();
    });
  });
});
