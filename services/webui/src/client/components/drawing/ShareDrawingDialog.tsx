import { useState, useEffect } from 'react';
import Modal from '../common/Modal';
import Button from '../Button';
import api from '../../lib/api';
import type { User } from '../../types';

interface ShareDrawingDialogProps {
  isOpen: boolean;
  onClose: () => void;
  drawingId: number;
  drawingName: string;
}

type TabType = 'users' | 'groups' | 'public' | 'analytics';
type Permission = 'view' | 'edit' | 'admin';

interface UserShare {
  id: number;
  user_id: number;
  email: string;
  full_name: string;
  permission: Permission;
  created_at: string;
}

interface GroupShare {
  id: number;
  group_id: number;
  group_name: string;
  permission: Permission;
  created_at: string;
}

interface PublicShare {
  id: number;
  token: string;
  permission: Permission;
  expires_at: string | null;
  created_at: string;
}

interface Group {
  id: number;
  name: string;
  description: string | null;
}

interface AccessLog {
  accessed_at: string;
  access_ip: string;
  user_agent: string;
  accessed_by_id: number | null;
  accessed_by_username: string | null;
}

interface SharesData {
  user_shares: UserShare[];
  group_shares: GroupShare[];
  public_shares: PublicShare[];
}

interface AnalyticsData {
  drawing_id: number;
  total_views: number;
  unique_ips: number;
  public_shares: PublicShare[];
  recent_accesses: AccessLog[];
}

export default function ShareDrawingDialog({
  isOpen,
  onClose,
  drawingId,
  drawingName,
}: ShareDrawingDialogProps) {
  const [activeTab, setActiveTab] = useState<TabType>('users');
  const [shares, setShares] = useState<SharesData>({
    user_shares: [],
    group_shares: [],
    public_shares: [],
  });
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // User share state
  const [availableUsers, setAvailableUsers] = useState<User[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [userPermission, setUserPermission] = useState<Permission>('view');
  const [userSearch, setUserSearch] = useState('');

  // Group share state
  const [availableGroups, setAvailableGroups] = useState<Group[]>([]);
  const [selectedGroupId, setSelectedGroupId] = useState<number | null>(null);
  const [groupPermission, setGroupPermission] = useState<Permission>('view');

  // Public share state
  const [publicPermission, setPublicPermission] = useState<Permission>('view');
  const [expiresInDays, setExpiresInDays] = useState<number | null>(null);
  const [copiedToken, setCopiedToken] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      fetchShares();
      if (activeTab === 'users') {
        fetchUsers();
      } else if (activeTab === 'groups') {
        fetchGroups();
      } else if (activeTab === 'analytics') {
        fetchAnalytics();
      }
    }
  }, [isOpen, activeTab, drawingId]);

  const fetchShares = async () => {
    setIsLoading(true);
    try {
      const response = await api.get<{ shares: SharesData }>(`/drawings/${drawingId}/shares`);
      setShares(response.data.shares);
      setError('');
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to load shares');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await api.get<{ items: User[] }>('/users');
      setAvailableUsers(response.data.items || []);
    } catch (err) {
      console.error('Failed to fetch users:', err);
    }
  };

  const fetchGroups = async () => {
    try {
      const response = await api.get<{ groups: Group[] }>('/groups');
      setAvailableGroups(response.data.groups || []);
    } catch (err) {
      console.error('Failed to fetch groups:', err);
    }
  };

  const fetchAnalytics = async () => {
    setIsLoading(true);
    try {
      const response = await api.get<AnalyticsData>(`/drawings/${drawingId}/analytics`);
      setAnalytics(response.data);
      setError('');
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to load analytics');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddUserShare = async () => {
    if (!selectedUserId) return;

    try {
      await api.post(`/drawings/${drawingId}/shares`, {
        type: 'user',
        user_id: selectedUserId,
        permission: userPermission,
      });
      setSuccess('User added successfully');
      setSelectedUserId(null);
      fetchShares();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to add user share');
    }
  };

  const handleAddGroupShare = async () => {
    if (!selectedGroupId) return;

    try {
      await api.post(`/drawings/${drawingId}/shares`, {
        type: 'group',
        group_id: selectedGroupId,
        permission: groupPermission,
      });
      setSuccess('Group added successfully');
      setSelectedGroupId(null);
      fetchShares();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to add group share');
    }
  };

  const handleGeneratePublicLink = async () => {
    try {
      const response = await api.post<{
        token: string;
        share_url: string;
        expires_at: string | null;
      }>(`/drawings/${drawingId}/shares`, {
        type: 'public',
        permission: publicPermission,
        expires_in_days: expiresInDays,
      });
      setSuccess('Public link generated successfully');
      fetchShares();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to generate public link');
    }
  };

  const handleRemoveShare = async (shareId: number) => {
    if (!confirm('Are you sure you want to remove this share?')) return;

    try {
      await api.delete(`/drawings/${drawingId}/shares/${shareId}`);
      setSuccess('Share removed successfully');
      fetchShares();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to remove share');
    }
  };

  const handleUpdatePermission = async (shareId: number, permission: Permission) => {
    try {
      await api.put(`/drawings/${drawingId}/shares/${shareId}`, { permission });
      setSuccess('Permission updated successfully');
      fetchShares();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to update permission');
    }
  };

  const copyToClipboard = (token: string) => {
    const url = `${window.location.origin}/shared/drawings/${token}`;
    navigator.clipboard.writeText(url);
    setCopiedToken(token);
    setSuccess('Link copied to clipboard!');
    setTimeout(() => {
      setCopiedToken(null);
      setSuccess('');
    }, 2000);
  };

  const filteredUsers = availableUsers.filter((user) => {
    const matchesSearch = userSearch
      ? user.full_name.toLowerCase().includes(userSearch.toLowerCase()) ||
        user.email.toLowerCase().includes(userSearch.toLowerCase())
      : true;
    const notAlreadyShared = !shares.user_shares.find((s) => s.user_id === user.id);
    return matchesSearch && notAlreadyShared;
  });

  const filteredGroups = availableGroups.filter(
    (group) => !shares.group_shares.find((s) => s.group_id === group.id)
  );

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Share "${drawingName}"`} size="lg">
      <div>
        {/* Tabs */}
        <div className="flex gap-2 border-b border-slate-700 mb-4">
          <button
            onClick={() => setActiveTab('users')}
            className={`px-4 py-2 font-medium transition-colors ${
              activeTab === 'users'
                ? 'text-ice-gold-400 border-b-2 border-ice-gold-400'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Users
          </button>
          <button
            onClick={() => setActiveTab('groups')}
            className={`px-4 py-2 font-medium transition-colors ${
              activeTab === 'groups'
                ? 'text-ice-gold-400 border-b-2 border-ice-gold-400'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Groups
          </button>
          <button
            onClick={() => setActiveTab('public')}
            className={`px-4 py-2 font-medium transition-colors ${
              activeTab === 'public'
                ? 'text-ice-gold-400 border-b-2 border-ice-gold-400'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Public Link
          </button>
          <button
            onClick={() => setActiveTab('analytics')}
            className={`px-4 py-2 font-medium transition-colors ${
              activeTab === 'analytics'
                ? 'text-ice-gold-400 border-b-2 border-ice-gold-400'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Analytics
          </button>
        </div>

        {/* Error/Success Messages */}
        {error && (
          <div className="mb-4 p-3 bg-red-900/30 border border-red-700 rounded-lg text-red-400 text-sm">
            {error}
          </div>
        )}
        {success && (
          <div className="mb-4 p-3 bg-green-900/30 border border-green-700 rounded-lg text-green-400 text-sm">
            {success}
          </div>
        )}

        {/* Tab Content */}
        {activeTab === 'users' && (
          <div>
            <h3 className="text-sm font-medium text-slate-300 mb-3">Share with Users</h3>

            {/* Add User Form */}
            <div className="bg-slate-900 rounded-lg p-4 mb-4">
              <input
                type="text"
                placeholder="Search users..."
                value={userSearch}
                onChange={(e) => setUserSearch(e.target.value)}
                className="input w-full mb-3"
              />
              <div className="flex gap-3">
                <select
                  value={selectedUserId || ''}
                  onChange={(e) => setSelectedUserId(Number(e.target.value) || null)}
                  className="input flex-1"
                >
                  <option value="">Select user...</option>
                  {filteredUsers.map((user) => (
                    <option key={user.id} value={user.id}>
                      {user.full_name} ({user.email})
                    </option>
                  ))}
                </select>
                <select
                  value={userPermission}
                  onChange={(e) => setUserPermission(e.target.value as Permission)}
                  className="input w-32"
                >
                  <option value="view">View</option>
                  <option value="edit">Edit</option>
                  <option value="admin">Admin</option>
                </select>
                <Button onClick={handleAddUserShare} disabled={!selectedUserId} size="sm">
                  Add
                </Button>
              </div>
            </div>

            {/* User Shares List */}
            <div className="space-y-2">
              {shares.user_shares.length === 0 ? (
                <p className="text-sm text-slate-400 text-center py-4">
                  No users have access yet
                </p>
              ) : (
                shares.user_shares.map((share) => (
                  <div
                    key={share.id}
                    className="flex items-center justify-between p-3 bg-slate-900 rounded-lg"
                  >
                    <div className="flex-1">
                      <div className="text-sm font-medium text-slate-200">{share.full_name}</div>
                      <div className="text-xs text-slate-400">{share.email}</div>
                    </div>
                    <div className="flex items-center gap-3">
                      <select
                        value={share.permission}
                        onChange={(e) =>
                          handleUpdatePermission(share.id, e.target.value as Permission)
                        }
                        className="input w-28 text-xs"
                      >
                        <option value="view">View</option>
                        <option value="edit">Edit</option>
                        <option value="admin">Admin</option>
                      </select>
                      <button
                        onClick={() => handleRemoveShare(share.id)}
                        className="text-red-400 hover:text-red-300 transition-colors"
                        title="Remove access"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                          />
                        </svg>
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {activeTab === 'groups' && (
          <div>
            <h3 className="text-sm font-medium text-slate-300 mb-3">Share with Groups</h3>

            {/* Add Group Form */}
            <div className="bg-slate-900 rounded-lg p-4 mb-4">
              <div className="flex gap-3">
                <select
                  value={selectedGroupId || ''}
                  onChange={(e) => setSelectedGroupId(Number(e.target.value) || null)}
                  className="input flex-1"
                >
                  <option value="">Select group...</option>
                  {filteredGroups.map((group) => (
                    <option key={group.id} value={group.id}>
                      {group.name}
                    </option>
                  ))}
                </select>
                <select
                  value={groupPermission}
                  onChange={(e) => setGroupPermission(e.target.value as Permission)}
                  className="input w-32"
                >
                  <option value="view">View</option>
                  <option value="edit">Edit</option>
                  <option value="admin">Admin</option>
                </select>
                <Button onClick={handleAddGroupShare} disabled={!selectedGroupId} size="sm">
                  Add
                </Button>
              </div>
            </div>

            {/* Group Shares List */}
            <div className="space-y-2">
              {shares.group_shares.length === 0 ? (
                <p className="text-sm text-slate-400 text-center py-4">
                  No groups have access yet
                </p>
              ) : (
                shares.group_shares.map((share) => (
                  <div
                    key={share.id}
                    className="flex items-center justify-between p-3 bg-slate-900 rounded-lg"
                  >
                    <div className="flex-1">
                      <div className="text-sm font-medium text-slate-200">{share.group_name}</div>
                      <div className="text-xs text-slate-400">
                        Shared {new Date(share.created_at).toLocaleDateString()}
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <select
                        value={share.permission}
                        onChange={(e) =>
                          handleUpdatePermission(share.id, e.target.value as Permission)
                        }
                        className="input w-28 text-xs"
                      >
                        <option value="view">View</option>
                        <option value="edit">Edit</option>
                        <option value="admin">Admin</option>
                      </select>
                      <button
                        onClick={() => handleRemoveShare(share.id)}
                        className="text-red-400 hover:text-red-300 transition-colors"
                        title="Remove access"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                          />
                        </svg>
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {activeTab === 'public' && (
          <div>
            <h3 className="text-sm font-medium text-slate-300 mb-3">Public Link Sharing</h3>

            {/* Generate Public Link */}
            <div className="bg-slate-900 rounded-lg p-4 mb-4">
              <p className="text-sm text-slate-400 mb-3">
                Anyone with the link can access this drawing
              </p>
              <div className="flex gap-3 mb-3">
                <select
                  value={publicPermission}
                  onChange={(e) => setPublicPermission(e.target.value as Permission)}
                  className="input w-32"
                >
                  <option value="view">View</option>
                  <option value="edit">Edit</option>
                </select>
                <select
                  value={expiresInDays || ''}
                  onChange={(e) => setExpiresInDays(Number(e.target.value) || null)}
                  className="input flex-1"
                >
                  <option value="">Never expires</option>
                  <option value="1">Expires in 1 day</option>
                  <option value="7">Expires in 7 days</option>
                  <option value="30">Expires in 30 days</option>
                  <option value="90">Expires in 90 days</option>
                </select>
                <Button onClick={handleGeneratePublicLink} size="sm">
                  Generate Link
                </Button>
              </div>
            </div>

            {/* Public Links List */}
            <div className="space-y-2">
              {shares.public_shares.length === 0 ? (
                <p className="text-sm text-slate-400 text-center py-4">
                  No public links created yet
                </p>
              ) : (
                shares.public_shares.map((share) => (
                  <div key={share.id} className="p-3 bg-slate-900 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs px-2 py-1 rounded bg-slate-700 text-slate-300">
                        {share.permission}
                      </span>
                      <button
                        onClick={() => handleRemoveShare(share.id)}
                        className="text-red-400 hover:text-red-300 transition-colors text-xs"
                      >
                        Revoke
                      </button>
                    </div>
                    <div className="flex items-center gap-2 mb-2">
                      <input
                        type="text"
                        value={`${window.location.origin}/shared/drawings/${share.token}`}
                        readOnly
                        className="input flex-1 text-xs"
                      />
                      <Button
                        onClick={() => copyToClipboard(share.token)}
                        size="sm"
                        variant={copiedToken === share.token ? 'secondary' : 'primary'}
                      >
                        {copiedToken === share.token ? 'Copied!' : 'Copy'}
                      </Button>
                    </div>
                    <div className="text-xs text-slate-400">
                      Created {new Date(share.created_at).toLocaleDateString()}
                      {share.expires_at && (
                        <> • Expires {new Date(share.expires_at).toLocaleDateString()}</>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {activeTab === 'analytics' && (
          <div>
            <h3 className="text-sm font-medium text-slate-300 mb-3">Analytics</h3>

            {isLoading ? (
              <div className="animate-pulse space-y-4">
                <div className="h-20 bg-slate-900 rounded-lg"></div>
                <div className="h-32 bg-slate-900 rounded-lg"></div>
              </div>
            ) : analytics ? (
              <>
                {/* Summary Stats */}
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div className="bg-slate-900 rounded-lg p-4">
                    <div className="text-2xl font-bold text-ice-gold-400">
                      {analytics.total_views}
                    </div>
                    <div className="text-xs text-slate-400">Total Views</div>
                  </div>
                  <div className="bg-slate-900 rounded-lg p-4">
                    <div className="text-2xl font-bold text-ice-gold-400">
                      {analytics.unique_ips}
                    </div>
                    <div className="text-xs text-slate-400">Unique Visitors</div>
                  </div>
                </div>

                {/* Recent Accesses */}
                <div>
                  <h4 className="text-sm font-medium text-slate-300 mb-2">Recent Accesses</h4>
                  <div className="bg-slate-900 rounded-lg overflow-hidden">
                    <div className="max-h-64 overflow-y-auto">
                      <table className="w-full text-xs">
                        <thead className="bg-slate-800 sticky top-0">
                          <tr>
                            <th className="px-3 py-2 text-left text-slate-400 font-medium">
                              Date/Time
                            </th>
                            <th className="px-3 py-2 text-left text-slate-400 font-medium">IP</th>
                            <th className="px-3 py-2 text-left text-slate-400 font-medium">
                              User Agent
                            </th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800">
                          {analytics.recent_accesses.length === 0 ? (
                            <tr>
                              <td colSpan={3} className="px-3 py-4 text-center text-slate-400">
                                No access logs yet
                              </td>
                            </tr>
                          ) : (
                            analytics.recent_accesses.map((access, idx) => (
                              <tr key={idx} className="hover:bg-slate-800/50">
                                <td className="px-3 py-2 text-slate-300">
                                  {new Date(access.accessed_at).toLocaleString()}
                                </td>
                                <td className="px-3 py-2 text-slate-300">
                                  {access.access_ip || 'N/A'}
                                </td>
                                <td className="px-3 py-2 text-slate-400 truncate max-w-xs">
                                  {access.user_agent || 'N/A'}
                                </td>
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <p className="text-sm text-slate-400 text-center py-4">No analytics available</p>
            )}
          </div>
        )}
      </div>
    </Modal>
  );
}
