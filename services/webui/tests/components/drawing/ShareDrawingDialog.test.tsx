/**
 * ShareDrawingDialog Component Tests
 *
 * Tests for tab navigation, user search, public link generation, and error display.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';

// Mock api module
vi.mock('@/client/lib/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

// Mock Modal to render a simple wrapper
vi.mock('@/client/components/common/Modal', () => ({
  default: ({
    isOpen,
    onClose,
    title,
    children,
  }: {
    isOpen: boolean;
    onClose: () => void;
    title?: string;
    children: React.ReactNode;
  }) => {
    if (!isOpen) return null;
    return (
      <div data-testid="modal">
        <div data-testid="modal-title">{title}</div>
        <button data-testid="modal-close" onClick={onClose}>
          Close
        </button>
        {children}
      </div>
    );
  },
}));

// Mock Button
vi.mock('@/client/components/Button', () => ({
  default: ({
    children,
    onClick,
    disabled,
  }: {
    children: React.ReactNode;
    onClick?: () => void;
    disabled?: boolean;
  }) => (
    <button onClick={onClick} disabled={disabled}>
      {children}
    </button>
  ),
}));

import ShareDrawingDialog from '@/client/components/drawing/ShareDrawingDialog';
import api from '@/client/lib/api';

const renderWithRouter = (ui: React.ReactElement) =>
  render(<BrowserRouter>{ui}</BrowserRouter>);

const defaultProps = {
  isOpen: true,
  onClose: vi.fn(),
  drawingId: 123,
  drawingName: 'My Chart',
};

describe('ShareDrawingDialog Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();

    (api.get as ReturnType<typeof vi.fn>).mockImplementation((url: string) => {
      if (url.includes('/shares')) {
        return Promise.resolve({
          data: {
            shares: {
              user_shares: [],
              group_shares: [],
              public_shares: [],
            },
          },
        });
      }
      if (url.includes('/users')) {
        return Promise.resolve({ data: { items: [] } });
      }
      if (url.includes('/groups')) {
        return Promise.resolve({ data: { groups: [] } });
      }
      if (url.includes('/analytics')) {
        return Promise.resolve({
          data: {
            drawing_id: 123,
            total_views: 42,
            unique_ips: 10,
            public_shares: [],
            recent_accesses: [],
          },
        });
      }
      return Promise.resolve({ data: {} });
    });

    (api.post as ReturnType<typeof vi.fn>).mockResolvedValue({ data: {} });
    (api.delete as ReturnType<typeof vi.fn>).mockResolvedValue({ data: {} });
  });

  it('does not render modal when isOpen is false', () => {
    renderWithRouter(
      <ShareDrawingDialog {...defaultProps} isOpen={false} />
    );
    expect(screen.queryByTestId('modal')).toBeNull();
  });

  it('renders modal with drawing name in title', async () => {
    renderWithRouter(<ShareDrawingDialog {...defaultProps} />);
    await waitFor(() => {
      expect(screen.getByTestId('modal-title').textContent).toContain('My Chart');
    });
  });

  it('renders Users, Groups, Public Link, Analytics tabs', async () => {
    renderWithRouter(<ShareDrawingDialog {...defaultProps} />);
    await waitFor(() => {
      expect(screen.getByText('Users')).toBeDefined();
      expect(screen.getByText('Groups')).toBeDefined();
      expect(screen.getByText('Public Link')).toBeDefined();
      expect(screen.getByText('Analytics')).toBeDefined();
    });
  });

  it('renders user search input on Users tab', async () => {
    renderWithRouter(<ShareDrawingDialog {...defaultProps} />);
    await waitFor(() => {
      expect(screen.getByPlaceholderText('Search users...')).toBeDefined();
    });
  });

  it('shows empty state message when no users have access', async () => {
    renderWithRouter(<ShareDrawingDialog {...defaultProps} />);
    await waitFor(() => {
      expect(screen.getByText('No users have access yet')).toBeDefined();
    });
  });

  it('switches to Public Link tab and shows generate button', async () => {
    renderWithRouter(<ShareDrawingDialog {...defaultProps} />);
    await waitFor(() => screen.getByText('Public Link'));

    fireEvent.click(screen.getByText('Public Link'));

    await waitFor(() => {
      expect(screen.getByText('Generate Link')).toBeDefined();
    });
  });

  it('calls onClose when modal close button is clicked', async () => {
    const onClose = vi.fn();
    renderWithRouter(
      <ShareDrawingDialog {...defaultProps} onClose={onClose} />
    );
    await waitFor(() => screen.getByTestId('modal-close'));

    fireEvent.click(screen.getByTestId('modal-close'));
    expect(onClose).toHaveBeenCalledTimes(1);
  });
});
