import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import Button from '../Button';

interface LocationState {
  from?: { pathname: string };
}

interface GoogleLoginButtonProps {
  className?: string;
  variant?: 'primary' | 'secondary';
}

export default function GoogleLoginButton({ className = '', variant = 'secondary' }: GoogleLoginButtonProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const location = useLocation();
  const { useAuthStore } = useAuth();

  // State to track OAuth callback - use window session storage to communicate
  const handleGoogleSignIn = async () => {
    setError('');
    setIsLoading(true);

    try {
      // Get Google auth URL from backend
      const response = await fetch('/api/v1/auth/google', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
      });

      if (!response.ok) {
        throw new Error('Failed to get Google auth URL');
      }

      const data = await response.json();
      const authUrl = data.auth_url;

      // Store return path for after OAuth callback
      const returnPath = (location.state as LocationState)?.from?.pathname || '/';
      sessionStorage.setItem('oauthReturnPath', returnPath);

      // Store callback handler in session to process result
      sessionStorage.setItem('expectedOauthFlow', 'google');

      // Redirect to Google OAuth
      window.location.href = authUrl;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Google sign-in failed');
      setIsLoading(false);
    }
  };

  const buttonVariantClass = variant === 'primary'
    ? 'bg-gold-500 hover:bg-gold-600 text-dark-950'
    : 'bg-dark-800 hover:bg-dark-700 border border-dark-600 text-gold-400';

  return (
    <div className={className}>
      {error && (
        <div className="mb-4 p-3 bg-red-900/30 border border-red-700 rounded-lg text-red-400 text-sm">
          {error}
        </div>
      )}
      <button
        onClick={handleGoogleSignIn}
        disabled={isLoading}
        className={`w-full py-2 px-4 rounded-lg font-medium transition-colors flex items-center justify-center gap-2 ${buttonVariantClass} ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12.545,10.239v3.821h5.445c-0.712,2.315-2.647,3.972-5.445,3.972c-3.332,0-6.033-2.701-6.033-6.032 c0-3.331,2.701-6.032,6.033-6.032c1.498,0,2.866,0.549,3.921,1.453l2.814-2.814C17.461,2.268,15.365,1,12.545,1 C6.477,1,1.54,5.938,1.54,12s4.937,11,11.005,11c6.067,0,11.067-4.933,11.067-11c0-0.546-0.033-1.074-0.099-1.595h-11.068V10.239z" />
        </svg>
        {isLoading ? 'Signing in...' : 'Sign in with Google'}
      </button>
      <p className="text-center text-xs text-dark-500 mt-3">
        We never post without your permission
      </p>
    </div>
  );
}
