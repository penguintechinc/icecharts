import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../../lib/api';
import Button from '../../components/Button';
import type { User, CreateUserData } from '../../types';

export default function AdminUsers() {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newUser, setNewUser] = useState<CreateUserData>({
    email: '',
    password: '',
    full_name: '',
    role: 'viewer',
  });
  const [isCreating, setIsCreating] = useState(false);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    setIsLoading(true);
    try {
      const response = await api.get<{ users: User[]; total: number }>('/admin/users');
      setUsers(response.data.users);
    } catch (err) {
      console.error('Failed to fetch users:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsCreating(true);

    try {
      await api.post('/admin/users', newUser);
      setNewUser({ email: '', password: '', full_name: '', role: 'viewer' });
      setShowCreateModal(false);
      fetchUsers();
    } catch (err) {
      console.error('Failed to create user:', err);
    } finally {
      setIsCreating(false);
    }
  };

  const handleToggleActive = async (userId: number, isActive: boolean) => {
    try {
      // Use activate/deactivate endpoints
      const action = isActive ? 'deactivate' : 'activate';
      await api.post(`/admin/users/${userId}/${action}`);
      fetchUsers();
    } catch (err) {
      console.error('Failed to update user:', err);
    }
  };

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gold-400">User Management</h1>
          <p className="text-dark-400 mt-1">
            Manage all users and their access levels
          </p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>Create New User</Button>
      </div>

      {/* Users Table */}
      {isLoading ? (
        <div className="card animate-pulse">
          <div className="h-8 bg-dark-700 rounded mb-4"></div>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-12 bg-dark-700 rounded"></div>
            ))}
          </div>
        </div>
      ) : (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full table-fixed">
              <thead>
                <tr className="border-b border-dark-700">
                  <th className="text-left py-4 px-6 text-gold-400 font-medium w-[15%]">
                    User
                  </th>
                  <th className="text-left py-4 px-6 text-gold-400 font-medium w-[20%]">
                    Email
                  </th>
                  <th className="text-left py-4 px-6 text-gold-400 font-medium w-[10%]">
                    Role
                  </th>
                  <th className="text-left py-4 px-6 text-gold-400 font-medium w-[18%]">
                    Groups
                  </th>
                  <th className="text-left py-4 px-6 text-gold-400 font-medium w-[10%]">
                    Status
                  </th>
                  <th className="text-left py-4 px-6 text-gold-400 font-medium w-[12%]">
                    Created
                  </th>
                  <th className="text-left py-4 px-6 text-gold-400 font-medium w-[15%]">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id} className="border-b border-dark-800 hover:bg-dark-850">
                    <td className="py-4 px-6">
                      <div className="text-gold-400 font-medium truncate">{user.full_name || '—'}</div>
                    </td>
                    <td className="py-4 px-6 text-dark-300 truncate">{user.email}</td>
                    <td className="py-4 px-6">
                      <span className={`badge badge-${user.role}`}>
                        {user.role}
                      </span>
                    </td>
                    <td className="py-4 px-6">
                      {user.groups && user.groups.length > 0 ? (
                        <div className="flex flex-wrap gap-1">
                          {user.groups.map((group: { id: number; name: string; role: string }) => (
                            <Link
                              key={group.id}
                              to={`/admin/groups/${group.id}`}
                              className="text-xs px-2 py-0.5 rounded bg-dark-700 text-dark-300 hover:bg-dark-600 hover:text-gold-400 transition-colors"
                              title={`Role: ${group.role}`}
                            >
                              {group.name}
                            </Link>
                          ))}
                        </div>
                      ) : (
                        <span className="text-dark-500 text-sm">—</span>
                      )}
                    </td>
                    <td className="py-4 px-6">
                      <span
                        className={`text-xs px-2 py-1 rounded whitespace-nowrap ${
                          user.is_active
                            ? 'bg-green-900/30 text-green-400'
                            : 'bg-red-900/30 text-red-400'
                        }`}
                      >
                        {user.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="py-4 px-6 text-dark-400 text-sm whitespace-nowrap">
                      {new Date(user.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-4 px-6">
                      <div className="flex items-center gap-4">
                        <Link
                          to={`/admin/users/${user.id}`}
                          className="text-sm text-gold-400 hover:text-gold-300"
                        >
                          Edit
                        </Link>
                        <button
                          onClick={() => handleToggleActive(user.id, user.is_active)}
                          className={`text-sm ${
                            user.is_active
                              ? 'text-red-400 hover:text-red-300'
                              : 'text-green-400 hover:text-green-300'
                          }`}
                        >
                          {user.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Create User Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="card max-w-md w-full">
            <h2 className="text-xl font-bold text-gold-400 mb-4">
              Create New User
            </h2>

            <form onSubmit={handleCreateUser} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gold-400 mb-2">
                  Full Name
                </label>
                <input
                  type="text"
                  value={newUser.full_name}
                  onChange={(e) =>
                    setNewUser({ ...newUser, full_name: e.target.value })
                  }
                  className="input w-full"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gold-400 mb-2">
                  Email
                </label>
                <input
                  type="email"
                  value={newUser.email}
                  onChange={(e) =>
                    setNewUser({ ...newUser, email: e.target.value })
                  }
                  className="input w-full"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gold-400 mb-2">
                  Password
                </label>
                <input
                  type="password"
                  value={newUser.password}
                  onChange={(e) =>
                    setNewUser({ ...newUser, password: e.target.value })
                  }
                  className="input w-full"
                  required
                  minLength={8}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gold-400 mb-2">
                  Role
                </label>
                <select
                  value={newUser.role}
                  onChange={(e) =>
                    setNewUser({
                      ...newUser,
                      role: e.target.value as 'admin' | 'maintainer' | 'viewer',
                    })
                  }
                  className="input w-full"
                  required
                >
                  <option value="viewer">Viewer</option>
                  <option value="maintainer">Maintainer</option>
                  <option value="admin">Admin</option>
                </select>
              </div>

              <div className="flex gap-3 pt-2">
                <Button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    setNewUser({
                      email: '',
                      password: '',
                      full_name: '',
                      role: 'viewer',
                    });
                  }}
                  className="flex-1 bg-dark-800 hover:bg-dark-700"
                >
                  Cancel
                </Button>
                <Button type="submit" className="flex-1" isLoading={isCreating}>
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
