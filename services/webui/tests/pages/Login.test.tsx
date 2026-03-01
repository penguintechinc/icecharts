/**
 * Login Page Tests
 *
 * Tests for the Login page component which renders email/password form
 * and Google OAuth sign-in button.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import Login from '@/client/pages/Login';

// Mock react-router-dom navigation
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => ({ search: '', state: null, pathname: '/login' }),
  };
});

// Mock useAuth hook
const mockLogin = vi.fn();
vi.mock('@/client/hooks/useAuth', () => ({
  useAuth: () => ({
    login: mockLogin,
    user: null,
    isAuthenticated: false,
    isLoading: false,
  }),
  useAuthStore: vi.fn(),
}));

// Mock GoogleLoginButton
vi.mock('@/client/components/auth', () => ({
  GoogleLoginButton: ({ className }: { className?: string }) => (
    <div data-testid="google-login-button" className={className}>
      Sign in with Google
    </div>
  ),
}));

// Mock Button component
vi.mock('@/client/components/Button', () => ({
  default: ({
    children,
    type,
    className,
    isLoading,
    ...props
  }: {
    children: React.ReactNode;
    type?: string;
    className?: string;
    isLoading?: boolean;
    [key: string]: any;
  }) => (
    <button
      type={type || 'button'}
      className={className}
      disabled={isLoading || props.disabled}
      {...props}
    >
      {isLoading ? 'Loading...' : children}
    </button>
  ),
}));

const renderWithRouter = (ui: React.ReactElement) =>
  render(<BrowserRouter>{ui}</BrowserRouter>);

describe('Login Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockLogin.mockReset();
    (global.fetch as any).mockReset();
  });

  it('renders login form with email field', () => {
    renderWithRouter(<Login />);
    const emailInput = screen.getByLabelText(/email/i);
    expect(emailInput).toBeDefined();
  });

  it('renders login form with password field', () => {
    renderWithRouter(<Login />);
    const passwordInput = screen.getByLabelText(/password/i);
    expect(passwordInput).toBeDefined();
  });

  it('renders sign in submit button', () => {
    renderWithRouter(<Login />);
    const submitButton = screen.getByRole('button', { name: /sign in/i });
    expect(submitButton).toBeDefined();
  });

  it('renders Google OAuth button', () => {
    renderWithRouter(<Login />);
    const googleButton = screen.getByTestId('google-login-button');
    expect(googleButton).toBeDefined();
  });

  it('email input has type="email"', () => {
    renderWithRouter(<Login />);
    const emailInput = screen.getByLabelText(/email/i) as HTMLInputElement;
    expect(emailInput.type).toBe('email');
  });

  it('password input has type="password"', () => {
    renderWithRouter(<Login />);
    const passwordInput = screen.getByLabelText(/password/i) as HTMLInputElement;
    expect(passwordInput.type).toBe('password');
  });

  it('form is accessible with labels linked to inputs', () => {
    renderWithRouter(<Login />);
    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    expect(emailInput).toBeDefined();
    expect(passwordInput).toBeDefined();
  });

  it('calls login with email and password on submit', async () => {
    mockLogin.mockResolvedValueOnce(undefined);
    renderWithRouter(<Login />);

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    fireEvent.change(emailInput, { target: { value: 'user@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        email: 'user@example.com',
        password: 'password123',
      });
    });
  });

  it('navigates after successful login', async () => {
    mockLogin.mockResolvedValueOnce(undefined);
    renderWithRouter(<Login />);

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    fireEvent.change(emailInput, { target: { value: 'user@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'password123' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/', { replace: true });
    });
  });

  it('shows error message on failed login', async () => {
    mockLogin.mockRejectedValueOnce(new Error('Invalid credentials'));
    renderWithRouter(<Login />);

    const emailInput = screen.getByLabelText(/email/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /sign in/i });

    fireEvent.change(emailInput, { target: { value: 'user@example.com' } });
    fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/invalid email or password/i)).toBeDefined();
    });
  });

  it('shows register link', () => {
    renderWithRouter(<Login />);
    const registerLink = screen.getByText(/sign up/i);
    expect(registerLink).toBeDefined();
  });
});
