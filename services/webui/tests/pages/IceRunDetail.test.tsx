/**
 * IceRunDetail Page Tests
 *
 * Tests for detail page with tabs, overview card, and execute button.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';

// Mock react-router-dom
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useParams: vi.fn(() => ({ id: 'run-456' })),
    useNavigate: vi.fn(() => mockNavigate),
  };
});

// Mock WebhookConfig component which lives in same directory
vi.mock('@/client/pages/iceruns/components/WebhookConfig', () => ({
  WebhookConfig: ({ functionId }: { functionId: string }) => (
    <div data-testid="webhook-config">WebhookConfig for {functionId}</div>
  ),
}));

import IceRunDetail from '@/client/pages/iceruns/IceRunDetail';

const renderWithRouter = (ui: React.ReactElement) =>
  render(<BrowserRouter>{ui}</BrowserRouter>);

describe('IceRunDetail Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders Function Details heading', async () => {
    renderWithRouter(<IceRunDetail />);
    await waitFor(() => {
      expect(screen.getByText('Function Details')).toBeDefined();
    });
  });

  it('displays the function ID from URL params', async () => {
    renderWithRouter(<IceRunDetail />);
    await waitFor(() => {
      expect(screen.getByText(/function_id: run-456/)).toBeDefined();
    });
  });

  it('renders the Execute action button', async () => {
    renderWithRouter(<IceRunDetail />);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Execute' })).toBeDefined();
    });
  });

  it('renders the Delete action button', async () => {
    renderWithRouter(<IceRunDetail />);
    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Delete' })).toBeDefined();
    });
  });

  it('renders overview card with status, runtime, executions', async () => {
    renderWithRouter(<IceRunDetail />);
    await waitFor(() => {
      expect(screen.getByText('Active')).toBeDefined();
      expect(screen.getByText('Python 3.13')).toBeDefined();
      expect(screen.getByText('1,234')).toBeDefined();
    });
  });

  it('renders tabs: Overview, Executions, Webhook, Versions, Metrics', async () => {
    renderWithRouter(<IceRunDetail />);
    await waitFor(() => {
      // Use getAllByText since 'Executions' appears both in tab bar and overview card
      expect(screen.getAllByText('Overview').length).toBeGreaterThan(0);
      expect(screen.getAllByText('Executions').length).toBeGreaterThan(0);
      expect(screen.getByText('Webhook')).toBeDefined();
      expect(screen.getByText('Versions')).toBeDefined();
      expect(screen.getByText('Metrics')).toBeDefined();
    });
  });

  it('switches to Webhook tab and renders WebhookConfig', async () => {
    renderWithRouter(<IceRunDetail />);
    await waitFor(() => screen.getByText('Webhook'));

    fireEvent.click(screen.getByText('Webhook'));

    await waitFor(() => {
      expect(screen.getByTestId('webhook-config')).toBeDefined();
    });
  });
});
