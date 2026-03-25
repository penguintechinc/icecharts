/**
 * IceFlowDetail Page Tests
 *
 * Tests for detail page with tabs, stage cards, and action buttons.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';

// Mock react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useParams: vi.fn(() => ({ id: 'flow-123' })),
    useNavigate: vi.fn(() => vi.fn()),
  };
});

// Mock api client
vi.mock('@/client/lib/api', () => ({
  default: {
    get: vi.fn(),
  },
}));

import IceFlowDetail from '@/client/pages/iceflows/IceFlowDetail';
import apiClient from '@/client/lib/api';

const mockFlowData = {
  flow_id: 'flow-123',
  name: 'My Test Flow',
  description: 'A test IceFlow',
  repository_url: 'https://github.com/org/repo',
  repository_provider: 'github',
  status: 'active',
  gitops_enabled: true,
  stages: [
    {
      stage_id: 'stage-1',
      branch_name: 'develop',
      display_name: 'Development',
      stage_order: 1,
      is_production: false,
      min_approvers: 1,
      approvers_count: 2,
      tests_count: 5,
      calls_count: 3,
    },
    {
      stage_id: 'stage-2',
      branch_name: 'main',
      display_name: 'Production',
      stage_order: 2,
      is_production: true,
      min_approvers: 2,
      approvers_count: 3,
      tests_count: 10,
      calls_count: 5,
    },
  ],
};

const renderWithRouter = (ui: React.ReactElement) =>
  render(<BrowserRouter>{ui}</BrowserRouter>);

describe('IceFlowDetail Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (apiClient.get as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: { flow: mockFlowData },
    });
  });

  it('shows loading state initially', () => {
    (apiClient.get as ReturnType<typeof vi.fn>).mockImplementation(
      () => new Promise(() => {})
    );
    renderWithRouter(<IceFlowDetail />);
    expect(screen.getByText('Loading...')).toBeDefined();
  });

  it('renders flow name after data loads', async () => {
    renderWithRouter(<IceFlowDetail />);
    await waitFor(() => {
      expect(screen.getByText('My Test Flow')).toBeDefined();
    });
  });

  it('renders flow status badge', async () => {
    renderWithRouter(<IceFlowDetail />);
    await waitFor(() => {
      expect(screen.getByText('active')).toBeDefined();
    });
  });

  it('renders tab buttons for stages, promotions, executions, settings', async () => {
    renderWithRouter(<IceFlowDetail />);
    await waitFor(() => {
      expect(screen.getByText('Stages')).toBeDefined();
      expect(screen.getByText('Promotions')).toBeDefined();
      expect(screen.getByText('Executions')).toBeDefined();
      expect(screen.getByText('Settings')).toBeDefined();
    });
  });

  it('renders stage cards with display names', async () => {
    renderWithRouter(<IceFlowDetail />);
    await waitFor(() => {
      expect(screen.getByText('Development')).toBeDefined();
      expect(screen.getByText('Production')).toBeDefined();
    });
  });

  it('shows stage configuration panel when a stage is clicked', async () => {
    renderWithRouter(<IceFlowDetail />);
    await waitFor(() => screen.getByText('Development'));

    fireEvent.click(screen.getByText('Development'));

    await waitFor(() => {
      expect(screen.getByText('Stage Configuration: Development')).toBeDefined();
    });
  });

  it('switches to settings tab and shows description', async () => {
    renderWithRouter(<IceFlowDetail />);
    await waitFor(() => screen.getByText('Settings'));

    fireEvent.click(screen.getByText('Settings'));

    await waitFor(() => {
      expect(screen.getByText('A test IceFlow')).toBeDefined();
    });
  });
});
