import React, { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';

export const Header: React.FC = () => {
  const { user, logout } = useAuthStore();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/drawings?search=${encodeURIComponent(searchQuery)}`);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const userInitials = user?.full_name
    ? user.full_name.split(' ').map((n: string) => n[0]).join('').toUpperCase().slice(0, 2)
    : user?.email?.[0]?.toUpperCase() || 'U';

  return (
    <header className="h-16 bg-ice-navy-800 border-b border-ice-navy-700 flex items-center justify-between px-6">
      {/* Search */}
      <form onSubmit={handleSearch} className="flex-1 max-w-xl">
        <div className="relative">
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-ice-navy-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search drawings..."
            className="w-full pl-10 pr-4 py-2 bg-ice-navy-700 border border-ice-navy-600 rounded-lg text-white placeholder-ice-navy-400 focus:outline-none focus:ring-2 focus:ring-ice-gold-400 focus:border-transparent"
          />
        </div>
      </form>

      {/* User Menu */}
      <div className="flex items-center gap-4">
        {/* Notifications */}
        <button className="p-2 text-ice-navy-400 hover:text-white transition-colors">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
        </button>

        {/* User Dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="flex items-center gap-3 hover:opacity-80 transition-opacity"
          >
            <div className="w-9 h-9 rounded-full bg-ice-gold-500 flex items-center justify-center text-ice-navy-900 font-semibold text-sm">
              {userInitials}
            </div>
            <svg className={`w-4 h-4 text-ice-navy-400 transition-transform ${dropdownOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {dropdownOpen && (
            <div className="absolute right-0 mt-2 w-56 bg-ice-navy-800 rounded-lg shadow-xl border border-ice-navy-700 py-1 z-50">
              <div className="px-4 py-3 border-b border-ice-navy-700">
                <p className="text-sm font-medium text-white truncate">{user?.full_name || 'User'}</p>
                <p className="text-sm text-ice-navy-400 truncate">{user?.email}</p>
              </div>
              <Link
                to="/settings"
                onClick={() => setDropdownOpen(false)}
                className="flex items-center gap-3 px-4 py-2 text-sm text-ice-navy-200 hover:bg-ice-navy-700 hover:text-white"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                Settings
              </Link>
              <button
                onClick={handleLogout}
                className="flex items-center gap-3 w-full px-4 py-2 text-sm text-red-400 hover:bg-ice-navy-700"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
                Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Header;
