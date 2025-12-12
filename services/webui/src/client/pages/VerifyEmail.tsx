import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export default function VerifyEmail() {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();
  const { verifyEmail } = useAuth();

  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [error, setError] = useState('');
  const [showResendForm, setShowResendForm] = useState(false);

  useEffect(() => {
    if (!token) {
      setStatus('error');
      setError('Invalid verification link');
      return;
    }

    const verifyEmailToken = async () => {
      try {
        await verifyEmail(token);
        setStatus('success');
        // Redirect to dashboard after 3 seconds
        const timer = setTimeout(() => {
          navigate('/', { replace: true });
        }, 3000);
        return () => clearTimeout(timer);
      } catch (err) {
        setStatus('error');
        const errorMessage = err instanceof Error ? err.message : 'Verification failed';
        if (errorMessage.includes('Token') || errorMessage.includes('expired')) {
          setError('Verification link has expired or is invalid');
          setShowResendForm(true);
        } else {
          setError(errorMessage || 'Failed to verify email');
        }
      }
    };

    verifyEmailToken();
  }, [token, verifyEmail, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-dark-950 px-4">
      <div className="w-full max-w-md">
        {/* Logo/Title */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gold-gradient mb-2">IceCharts</h1>
          <p className="text-dark-400">Verify your email</p>
        </div>

        {/* Verification Status */}
        <div className="card">
          {status === 'loading' && (
            <div className="text-center">
              <div className="mb-6 flex justify-center">
                <div className="inline-block animate-spin">
                  <svg
                    className="w-12 h-12 text-gold-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="2"
                      fill="none"
                      opacity="0.25"
                    />
                    <path
                      d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8z"
                      strokeLinecap="round"
                    />
                  </svg>
                </div>
              </div>
              <p className="text-gold-400 font-medium">Verifying your email...</p>
              <p className="text-dark-400 text-sm mt-2">
                Please wait while we confirm your email address
              </p>
            </div>
          )}

          {status === 'success' && (
            <div className="text-center">
              <div className="mb-6 flex justify-center">
                <div className="w-12 h-12 rounded-full bg-green-900/30 border border-green-700 flex items-center justify-center">
                  <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
              </div>
              <h2 className="text-xl font-semibold text-gold-400 mb-2">Email Verified!</h2>
              <p className="text-dark-400 text-sm mb-4">
                Your email has been successfully verified. Redirecting to dashboard...
              </p>
              <p className="text-dark-500 text-xs">
                If you're not redirected, <Link to="/" className="text-gold-400 hover:text-gold-300">click here</Link>
              </p>
            </div>
          )}

          {status === 'error' && (
            <div className="text-center">
              <div className="mb-6 flex justify-center">
                <div className="w-12 h-12 rounded-full bg-red-900/30 border border-red-700 flex items-center justify-center">
                  <svg className="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </div>
              </div>
              <h2 className="text-xl font-semibold text-red-400 mb-2">Verification Failed</h2>
              <p className="text-dark-400 text-sm mb-6">{error}</p>

              <div className="space-y-3">
                {showResendForm && (
                  <Link
                    to="/register?resend=true"
                    className="block w-full px-4 py-2 rounded-lg font-medium transition-colors duration-200 bg-gold-500 text-dark-950 hover:bg-gold-400 text-center"
                  >
                    Resend Verification Email
                  </Link>
                )}

                <Link
                  to="/login"
                  className="block w-full px-4 py-2 rounded-lg font-medium transition-colors duration-200 border border-gold-500 text-gold-400 hover:bg-gold-500/10 text-center"
                >
                  Back to Login
                </Link>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <p className="text-center text-sm text-dark-500 mt-6">
          Penguin Tech Inc. &copy; {new Date().getFullYear()}
        </p>
      </div>
    </div>
  );
}
