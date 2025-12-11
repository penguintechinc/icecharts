import { useState, useEffect } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import api, { authApi } from '../lib/api';
import Button from '../components/Button';
import type { RegisterData } from '../types';

export default function Register() {
  const [formData, setFormData] = useState<RegisterData>({
    email: '',
    password: '',
    full_name: '',
  });
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [verificationRequired, setVerificationRequired] = useState(false);
  const [resendLoading, setResendLoading] = useState(false);
  const [resendSuccess, setResendSuccess] = useState(false);

  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  // Check if we're on the resend verification page
  useEffect(() => {
    if (searchParams.get('resend') === 'true') {
      const email = sessionStorage.getItem('registerEmail');
      if (email) {
        setFormData((prev) => ({ ...prev, email }));
        setVerificationRequired(true);
      } else {
        navigate('/register');
      }
    }
  }, [searchParams, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setResendSuccess(false);

    // Validation
    if (formData.password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    setIsLoading(true);

    try {
      const response = await api.post('/auth/register', formData);

      // Store email in sessionStorage for potential resend
      sessionStorage.setItem('registerEmail', formData.email);

      // Check if email verification is required
      if (response.data.email_verification_required) {
        setVerificationRequired(true);
      } else {
        navigate('/login', {
          state: { message: 'Registration successful! Please log in.' },
        });
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendVerification = async () => {
    setResendLoading(true);
    setError('');
    setResendSuccess(false);

    try {
      await authApi.resendVerification();
      setResendSuccess(true);
    } catch (err: any) {
      setError(
        err.response?.data?.error || 'Failed to resend verification email. Please try again.'
      );
    } finally {
      setResendLoading(false);
    }
  };

  const handleChange = (field: keyof RegisterData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  if (verificationRequired) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-dark-950 px-4">
        <div className="w-full max-w-md">
          {/* Logo/Title */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gold-gradient mb-2">IceCharts</h1>
            <p className="text-dark-400">Verify your email</p>
          </div>

          {/* Verification Message */}
          <div className="card">
            <div className="text-center">
              <div className="mb-6 flex justify-center">
                <div className="w-12 h-12 rounded-full bg-blue-900/30 border border-blue-700 flex items-center justify-center">
                  <svg
                    className="w-6 h-6 text-blue-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                    />
                  </svg>
                </div>
              </div>

              <h2 className="text-xl font-semibold text-gold-400 mb-2">
                Check your email
              </h2>
              <p className="text-dark-400 text-sm mb-6">
                We've sent a verification link to <strong>{formData.email}</strong>.
                Please click the link in your email to verify your account.
              </p>

              {error && (
                <div className="p-3 bg-red-900/30 border border-red-700 rounded-lg text-red-400 text-sm mb-4">
                  {error}
                </div>
              )}

              {resendSuccess && (
                <div className="p-3 bg-green-900/30 border border-green-700 rounded-lg text-green-400 text-sm mb-4">
                  Verification email resent! Check your inbox.
                </div>
              )}

              <Button
                onClick={handleResendVerification}
                isLoading={resendLoading}
                className="w-full"
              >
                Resend Verification Email
              </Button>

              <div className="mt-4 text-center">
                <Link
                  to="/login"
                  className="text-sm text-gold-400 hover:text-gold-300 transition-colors"
                >
                  Back to login
                </Link>
              </div>
            </div>
          </div>

          {/* Footer */}
          <p className="text-center text-sm text-dark-500 mt-6">
            Penguin Tech Inc. &copy; {new Date().getFullYear()}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-dark-950 px-4">
      <div className="w-full max-w-md">
        {/* Logo/Title */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gold-gradient mb-2">IceCharts</h1>
          <p className="text-dark-400">Create your account</p>
        </div>

        {/* Registration Form */}
        <div className="card">
          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="p-3 bg-red-900/30 border border-red-700 rounded-lg text-red-400 text-sm">
                {error}
              </div>
            )}

            <div>
              <label htmlFor="full_name" className="block text-sm font-medium text-gold-400 mb-2">
                Full Name
              </label>
              <input
                id="full_name"
                type="text"
                value={formData.full_name}
                onChange={(e) => handleChange('full_name', e.target.value)}
                className="input"
                placeholder="John Doe"
                required
                autoComplete="name"
              />
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gold-400 mb-2">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) => handleChange('email', e.target.value)}
                className="input"
                placeholder="you@example.com"
                required
                autoComplete="email"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gold-400 mb-2">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={formData.password}
                onChange={(e) => handleChange('password', e.target.value)}
                className="input"
                placeholder="••••••••"
                required
                autoComplete="new-password"
                minLength={8}
              />
              <p className="mt-1 text-xs text-dark-500">
                Must be at least 8 characters long
              </p>
            </div>

            <div>
              <label htmlFor="confirm_password" className="block text-sm font-medium text-gold-400 mb-2">
                Confirm Password
              </label>
              <input
                id="confirm_password"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="input"
                placeholder="••••••••"
                required
                autoComplete="new-password"
              />
            </div>

            <Button type="submit" className="w-full" isLoading={isLoading}>
              Create Account
            </Button>

            <div className="text-center pt-2">
              <Link
                to="/login"
                className="text-sm text-gold-400 hover:text-gold-300 transition-colors"
              >
                Already have an account? Sign in
              </Link>
            </div>
          </form>
        </div>

        {/* Footer */}
        <p className="text-center text-sm text-dark-500 mt-6">
          Penguin Tech Inc. &copy; {new Date().getFullYear()}
        </p>
      </div>
    </div>
  );
}
