/**
 * Settings Page Tests
 *
 * Tests for tab navigation, saving preferences, and password validation.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Settings from '@/client/pages/Settings';

// Mock the api module
vi.mock('@/client/lib/api', () => ({
  default: {
    get: vi.fn(),
    put: vi.fn(),
  },
}));

// Mock useConnectors hook
vi.mock('@/client/hooks/useConnectors', () => ({
  useConnectors: vi.fn(() => ({
    connectors: [],
    loading: false,
    error: null,
  })),
}));

// Mock TabNavigation component
vi.mock('@/client/components/TabNavigation', () => ({
  default: ({ tabs, activeTab, onChange }: {
    tabs: Array<{ id: string; label: string }>;
    activeTab: string;
    onChange: (id: string) => void;
  }) => (
    <div data-testid="tab-navigation">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          data-testid={`tab-${tab.id}`}
          onClick={() => onChange(tab.id)}
          aria-selected={activeTab === tab.id}
        >
          {tab.label}
        </button>
      ))}
    </div>
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

// Mock Button component
vi.mock('@/client/components/Button', () => ({
  default: ({
    children,
    onClick,
    isLoading,
    disabled,
  }: {
    children: React.ReactNode;
    onClick?: () => void;
    isLoading?: boolean;
    disabled?: boolean;
  }) => (
    <button onClick={onClick} disabled={disabled || isLoading}>
      {isLoading ? 'Loading...' : children}
    </button>
  ),
}));

import api from '@/client/lib/api';

const renderWithRouter = (ui: React.ReactElement) =>
  render(<BrowserRouter>{ui}</BrowserRouter>);

describe('Settings Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (api.get as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: {
        preferences: {
          dark_mode: true,
          compact_view: false,
          timezone: 'UTC',
          email_notifications: true,
          system_alerts: true,
          weekly_reports: false,
          two_factor_enabled: false,
          session_timeout: 60,
        },
      },
    });
    (api.put as ReturnType<typeof vi.fn>).mockResolvedValue({ data: {} });
  });

  it('renders Settings heading after loading', async () => {
    renderWithRouter(<Settings />);
    await waitFor(() => {
      expect(screen.getByText('Settings')).toBeDefined();
    });
  });

  it('renders tab navigation with General, Notifications, Security, Connectors', async () => {
    renderWithRouter(<Settings />);
    await waitFor(() => {
      expect(screen.getByTestId('tab-general')).toBeDefined();
      expect(screen.getByTestId('tab-notifications')).toBeDefined();
      expect(screen.getByTestId('tab-security')).toBeDefined();
      expect(screen.getByTestId('tab-connectors')).toBeDefined();
    });
  });

  it('shows General Settings tab content by default', async () => {
    renderWithRouter(<Settings />);
    await waitFor(() => {
      expect(screen.getByText('General Settings')).toBeDefined();
    });
  });

  it('switches to Notifications tab on click', async () => {
    renderWithRouter(<Settings />);
    await waitFor(() => screen.getByTestId('tab-notifications'));

    fireEvent.click(screen.getByTestId('tab-notifications'));

    await waitFor(() => {
      expect(screen.getByText('Notification Settings')).toBeDefined();
    });
  });

  it('switches to Security tab on click', async () => {
    renderWithRouter(<Settings />);
    await waitFor(() => screen.getByTestId('tab-security'));

    fireEvent.click(screen.getByTestId('tab-security'));

    await waitFor(() => {
      expect(screen.getByText('Security Settings')).toBeDefined();
    });
  });

  it('calls api.put when Save Changes button is clicked', async () => {
    renderWithRouter(<Settings />);
    await waitFor(() => screen.getByText('Save Changes'));

    fireEvent.click(screen.getByText('Save Changes'));

    await waitFor(() => {
      expect(api.put).toHaveBeenCalledWith('/profile/preferences', expect.any(Object));
    });
  });

  it('shows error message when passwords do not match', async () => {
    renderWithRouter(<Settings />);
    await waitFor(() => screen.getByTestId('tab-security'));

    fireEvent.click(screen.getByTestId('tab-security'));

    await waitFor(() => screen.getByPlaceholderText('Enter current password'));

    fireEvent.change(screen.getByPlaceholderText('Enter current password'), {
      target: { value: 'currentpass' },
    });
    fireEvent.change(screen.getByPlaceholderText('Enter new password (min 8 characters)'), {
      target: { value: 'newpassword1' },
    });
    fireEvent.change(screen.getByPlaceholderText('Confirm new password'), {
      target: { value: 'differentpass' },
    });

    fireEvent.click(screen.getByRole('button', { name: 'Change Password' }));

    await waitFor(() => {
      expect(screen.getByText('New passwords do not match')).toBeDefined();
    });
  });

  it('shows error when new password is less than 8 characters', async () => {
    renderWithRouter(<Settings />);
    await waitFor(() => screen.getByTestId('tab-security'));

    fireEvent.click(screen.getByTestId('tab-security'));

    await waitFor(() => screen.getByPlaceholderText('Enter current password'));

    fireEvent.change(screen.getByPlaceholderText('Enter current password'), {
      target: { value: 'currentpass' },
    });
    fireEvent.change(screen.getByPlaceholderText('Enter new password (min 8 characters)'), {
      target: { value: 'short' },
    });
    fireEvent.change(screen.getByPlaceholderText('Confirm new password'), {
      target: { value: 'short' },
    });

    fireEvent.click(screen.getByRole('button', { name: 'Change Password' }));

    await waitFor(() => {
      expect(screen.getByText('New password must be at least 8 characters')).toBeDefined();
    });
  });
});
