import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { usersApi } from '../hooks/useApi';
import Button from '../components/Button';
import type { User, UserRole } from '../types';

export default function Users() {
  const [users, setUsers] = useState<User[]>([]);
  const [filteredUsers, setFilteredUsers] = useState<User[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Create user form state
  const [newUser, setNewUser] = useState({
    email: '',
    password: '',
    full_name: '',
    role: 'viewer' as UserRole,
  });
  const [createLoading, setCreateLoading] = useState(false);

  const fetchUsers = async () => {
    setIsLoading(true);
    try {
      const response = await usersApi.list();
      setUsers(response.users);
      setError(null);
    } catch (err) {
      setError('Failed to load users');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  // Filter users when search query changes
  useEffect(() => {
    if (!searchQuery.trim()) {
      setFilteredUsers(users);
    } else {
      const query = searchQuery.toLowerCase();
      setFilteredUsers(
        users.filter(
          (user) =>
            user.full_name?.toLowerCase().includes(query) ||
            user.email?.toLowerCase().includes(query) ||
            user.role?.toLowerCase().includes(query) ||
            user.groups?.some((g) => g.name.toLowerCase().includes(query))
        )
      );
    }
  }, [searchQuery, users]);

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateLoading(true);
    try {
      await usersApi.create(newUser);
      setShowCreateModal(false);
      setNewUser({ email: '', password: '', full_name: '', role: 'viewer' });
      fetchUsers();
    } catch (err) {
      setError('Failed to create user');
    } finally {
      setCreateLoading(false);
    }
  };

  const handleDeleteUser = async (id: number) => {
    if (!confirm('Are you sure you want to delete this user?')) return;
    try {
      await usersApi.delete(id);
      fetchUsers();
    } catch (err) {
      setError('Failed to delete user');
    }
  };

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-ice-gold-400">User Management</h1>
          <p className="text-ice-navy-400 mt-1">Manage system users and permissions</p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>+ Add User</Button>
      </div>

      {/* Search */}
      <div className="mb-6">
        <div className="relative">
          <svg
            className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-ice-navy-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <input
            type="text"
            placeholder="Search by name, email, role, or group..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input w-full pl-12"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-4 top-1/2 -translate-y-1/2 text-ice-navy-400 hover:text-white"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
        {searchQuery && (
          <p className="text-sm text-ice-navy-400 mt-2">
            Found {filteredUsers.length} {filteredUsers.length === 1 ? 'user' : 'users'}
          </p>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-3 bg-red-900/30 border border-red-700 rounded-lg text-red-400">
          {error}
        </div>
      )}

      {/* Users List */}
      {isLoading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 bg-ice-navy-800 rounded-lg animate-pulse"></div>
          ))}
        </div>
      ) : filteredUsers.length === 0 ? (
        <div className="text-center py-12 text-ice-navy-400 bg-ice-navy-800/50 rounded-lg border border-ice-navy-700">
          <p>{searchQuery ? 'No users match your search' : 'No users found'}</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredUsers.map((user) => (
            <div
              key={user.id}
              className="bg-ice-navy-800 border border-ice-navy-700 rounded-lg p-4 hover:border-ice-navy-600 transition-colors"
            >
              <div className="flex items-center justify-between">
                {/* User Info */}
                <div className="flex items-center gap-4 flex-1 min-w-0">
                  {/* Avatar */}
                  <div className="w-12 h-12 rounded-full bg-ice-gold-500/20 flex items-center justify-center flex-shrink-0">
                    <span className="text-ice-gold-400 font-semibold text-lg">
                      {user.full_name?.charAt(0)?.toUpperCase() || user.email?.charAt(0)?.toUpperCase() || 'U'}
                    </span>
                  </div>

                  {/* Name & Email */}
                  <div className="min-w-0 flex-1">
                    <h3 className="font-semibold text-white truncate">{user.full_name}</h3>
                    <p className="text-sm text-ice-navy-400 truncate">{user.email}</p>
                  </div>
                </div>

                {/* Role Badge */}
                <div className="flex-shrink-0 px-4">
                  <span
                    className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                      user.role === 'admin'
                        ? 'bg-red-900/50 text-red-400'
                        : user.role === 'maintainer'
                        ? 'bg-blue-900/50 text-blue-400'
                        : 'bg-gray-700/50 text-gray-400'
                    }`}
                  >
                    {user.role}
                  </span>
                </div>

                {/* Groups */}
                <div className="flex-shrink-0 w-48 px-4">
                  {user.groups && user.groups.length > 0 ? (
                    <div className="flex flex-wrap gap-1">
                      {user.groups.slice(0, 2).map((group) => (
                        <Link
                          key={group.id}
                          to={`/groups/${group.id}`}
                          className="inline-flex items-center px-2 py-0.5 rounded text-xs bg-ice-navy-700 text-ice-navy-300 hover:bg-ice-navy-600 hover:text-white transition-colors"
                        >
                          {group.name}
                        </Link>
                      ))}
                      {user.groups.length > 2 && (
                        <span className="text-xs text-ice-navy-500">
                          +{user.groups.length - 2} more
                        </span>
                      )}
                    </div>
                  ) : (
                    <span className="text-sm text-ice-navy-500">No groups</span>
                  )}
                </div>

                {/* Status */}
                <div className="flex-shrink-0 w-24 px-4">
                  <span
                    className={`inline-flex items-center gap-1.5 text-sm ${
                      user.is_active ? 'text-green-400' : 'text-red-400'
                    }`}
                  >
                    <span
                      className={`w-2 h-2 rounded-full ${
                        user.is_active ? 'bg-green-400' : 'bg-red-400'
                      }`}
                    />
                    {user.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-3 flex-shrink-0">
                  <Link
                    to={`/users/${user.id}`}
                    className="px-3 py-1.5 text-sm font-medium text-ice-gold-400 hover:text-ice-gold-300 bg-ice-gold-400/10 hover:bg-ice-gold-400/20 rounded transition-colors"
                  >
                    Edit
                  </Link>
                  <button
                    onClick={() => handleDeleteUser(user.id)}
                    className="px-3 py-1.5 text-sm font-medium text-red-400 hover:text-red-300 bg-red-400/10 hover:bg-red-400/20 rounded transition-colors"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create User Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="card w-full max-w-md mx-4">
            <h2 className="text-xl font-bold text-ice-gold-400 mb-4">Create New User</h2>
            <form onSubmit={handleCreateUser} className="space-y-4">
              <div>
                <label className="block text-sm text-ice-navy-400 mb-1">Full Name</label>
                <input
                  type="text"
                  value={newUser.full_name}
                  onChange={(e) => setNewUser({ ...newUser, full_name: e.target.value })}
                  className="input"
                  required
                />
              </div>
              <div>
                <label className="block text-sm text-ice-navy-400 mb-1">Email</label>
                <input
                  type="email"
                  value={newUser.email}
                  onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                  className="input"
                  required
                />
              </div>
              <div>
                <label className="block text-sm text-ice-navy-400 mb-1">Password</label>
                <input
                  type="password"
                  value={newUser.password}
                  onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                  className="input"
                  required
                  minLength={8}
                />
              </div>
              <div>
                <label className="block text-sm text-ice-navy-400 mb-1">Role</label>
                <select
                  value={newUser.role}
                  onChange={(e) => setNewUser({ ...newUser, role: e.target.value as UserRole })}
                  className="input"
                >
                  <option value="viewer">Viewer</option>
                  <option value="maintainer">Maintainer</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div className="flex justify-end gap-3 mt-6">
                <Button
                  type="button"
                  variant="secondary"
                  onClick={() => setShowCreateModal(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" isLoading={createLoading}>
                  Create User
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
