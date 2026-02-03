import { useState, useEffect } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import Button from '../components/Button';
import { GoogleLoginButton } from '../components/auth';

interface LocationState {
  from?: { pathname: string };
  message?: string;
}

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isProcessingOAuth, setIsProcessingOAuth] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = (location.state as LocationState)?.from?.pathname || '/';
  const successMessage = (location.state as LocationState)?.message;

  // Handle OAuth callback
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const code = params.get('code');
    const state = params.get('state');

    if (code && state) {
      handleOAuthCallback(code, state);
    }
  }, [location.search]);

  const handleOAuthCallback = async (code: string, state: string) => {
    setIsProcessingOAuth(true);
    setError('');

    try {
      const response = await fetch('/api/v1/auth/google/callback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, state }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'OAuth callback failed');
      }

      const data = await response.json();
      const { access_token, refresh_token, user } = data;

      // Store tokens
      localStorage.setItem('authToken', access_token);
      localStorage.setItem('refreshToken', refresh_token);
      localStorage.setItem('user', JSON.stringify(user));

      // Clean up OAuth parameters from URL
      window.history.replaceState({}, document.title, '/login');

      // Get return path from session storage
      const returnPath = sessionStorage.getItem('oauthReturnPath') || from;
      sessionStorage.removeItem('oauthReturnPath');
      sessionStorage.removeItem('expectedOauthFlow');

      // Redirect to dashboard
      navigate(returnPath, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'OAuth authentication failed');
    } finally {
      setIsProcessingOAuth(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await login({ email, password });
      navigate(from, { replace: true });
    } catch (err) {
      setError('Invalid email or password');
    } finally {
      setIsLoading(false);
    }
  };

  // Show processing message during OAuth flow
  if (isProcessingOAuth) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-dark-950">
        <div className="w-full max-w-md">
          <div className="card text-center">
            <div className="mb-4">
              <div className="inline-block animate-spin">
                <svg className="w-12 h-12 text-gold-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" fill="none" opacity="0.25" />
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8z" strokeLinecap="round" />
                </svg>
              </div>
            </div>
            <p className="text-gold-400 font-medium">Completing sign in...</p>
            <p className="text-dark-400 text-sm mt-2">Please wait while we authenticate your account</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-dark-950">
      <div className="w-full max-w-md">
        {/* Logo/Title */}
        <div className="text-center mb-8">
          <div className="flex justify-center">
            <img
              src="/logo-transparent.png"
              alt="IceCharts"
              className="h-20 w-auto mb-2"
            />
          </div>
          <p className="text-dark-400">Sign in to your account</p>
        </div>

        {/* Google Login Button */}
        <GoogleLoginButton className="mb-6" />

        {/* Divider */}
        <div className="flex items-center gap-4 my-6">
          <div className="flex-1 h-px bg-dark-700"></div>
          <span className="text-sm text-dark-500">Or continue with email</span>
          <div className="flex-1 h-px bg-dark-700"></div>
        </div>

        {/* Login Form */}
        <div className="card">
          <form onSubmit={handleSubmit} className="space-y-6">
            {successMessage && (
              <div className="p-3 bg-green-900/30 border border-green-700 rounded-lg text-green-400 text-sm">
                {successMessage}
              </div>
            )}

            {error && (
              <div className="p-3 bg-red-900/30 border border-red-700 rounded-lg text-red-400 text-sm">
                {error}
              </div>
            )}

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gold-400 mb-2">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input"
                placeholder="you@example.com"
                required
                autoComplete="email"
                disabled={isLoading}
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gold-400 mb-2">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input"
                placeholder="••••••••"
                required
                autoComplete="current-password"
                disabled={isLoading}
              />
            </div>

            <Button type="submit" className="w-full" isLoading={isLoading}>
              Sign In
            </Button>

            <div className="text-center pt-2">
              <Link
                to="/register"
                className="text-sm text-gold-400 hover:text-gold-300 transition-colors"
              >
                Don't have an account? Sign up
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
