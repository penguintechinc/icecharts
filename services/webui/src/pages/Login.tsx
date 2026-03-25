import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const { login, isLoading } = useAuthStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      await login(email, password);
      navigate('/');
    } catch (err) {
      setError('Invalid email or password');
    }
  };

  return (
    <div className="min-h-screen bg-ice-navy-900 flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        <div className="bg-gray-800 border border-ice-navy-700 rounded-lg p-8 shadow-lg">
          <div className="flex justify-center mb-6">
            <img
              src="/logo.jpg"
              alt="IceCharts"
              className="h-80 w-auto"
            />
          </div>
          <h2 className="text-xl text-ice-gold-400 mb-6 text-center">
            Sign in to your account
          </h2>

          {error && (
            <div className="bg-red-500 bg-opacity-10 border border-red-500 text-red-500 px-4 py-3 rounded mb-4">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label htmlFor="email" className="block text-ice-gold-400 mb-2">
                Email
              </label>
              <input
                type="email"
                id="email"
                className="w-full px-3 py-2 bg-ice-navy-800 border border-ice-navy-600 rounded-lg text-ice-gold-400 placeholder-gray-500 focus:outline-none focus:border-ice-gold-500 focus:ring-1 focus:ring-ice-gold-500"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
              />
            </div>

            <div className="mb-6">
              <label htmlFor="password" className="block text-ice-gold-400 mb-2">
                Password
              </label>
              <input
                type="password"
                id="password"
                className="w-full px-3 py-2 bg-ice-navy-800 border border-ice-navy-600 rounded-lg text-ice-gold-400 placeholder-gray-500 focus:outline-none focus:border-ice-gold-500 focus:ring-1 focus:ring-ice-gold-500"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
            </div>

            <button
              type="submit"
              className="w-full px-4 py-2 rounded-lg font-medium transition-colors duration-200 bg-ice-gold-500 text-ice-navy-900 hover:bg-ice-gold-400"
              disabled={isLoading}
            >
              {isLoading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>

          <p className="text-gray-400 text-center mt-4">
            Don't have an account?{' '}
            <a href="/register" className="text-ice-gold-400 hover:text-ice-gold-500">
              Sign up
            </a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
