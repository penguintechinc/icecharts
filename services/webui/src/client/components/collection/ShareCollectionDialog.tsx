import { useState, useEffect } from 'react';
import Modal from '../common/Modal';
import Input from '../common/Input';
import Select from '../common/Select';
import Button from '../common/Button';
import Card from '../common/Card';
import Spinner from '../common/Spinner';
import Badge from '../common/Badge';
import apiClient from '../../lib/api';

interface ShareWithUser {
  id: string;
  name: string;
  email: string;
  permission: 'viewer' | 'editor' | 'admin';
}

interface ShareWithGroup {
  id: string;
  name: string;
  permission: 'viewer' | 'editor' | 'admin';
}

interface User {
  id: string;
  name: string;
  email: string;
}

interface Group {
  id: string;
  name: string;
}

interface ShareCollectionDialogProps {
  collectionId: string;
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

type TabType = 'users' | 'groups' | 'public_link';

const permissionOptions = [
  { value: 'viewer', label: 'Viewer - Can view only' },
  { value: 'editor', label: 'Editor - Can edit' },
  { value: 'admin', label: 'Admin - Full control' },
];

export default function ShareCollectionDialog({
  collectionId,
  isOpen,
  onClose,
  onSuccess,
}: ShareCollectionDialogProps) {
  const [activeTab, setActiveTab] = useState<TabType>('users');
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  // User sharing state
  const [usersSearchQuery, setUsersSearchQuery] = useState('');
  const [availableUsers, setAvailableUsers] = useState<User[]>([]);
  const [usersLoading, setUsersLoading] = useState(false);
  const [sharedUsers, setSharedUsers] = useState<ShareWithUser[]>([]);
  const [selectedUserPermission, setSelectedUserPermission] = useState<
    'viewer' | 'editor' | 'admin'
  >('viewer');

  // Group sharing state
  const [availableGroups, setAvailableGroups] = useState<Group[]>([]);
  const [groupsLoading, setGroupsLoading] = useState(false);
  const [sharedGroups, setSharedGroups] = useState<ShareWithGroup[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<string>('');
  const [selectedGroupPermission, setSelectedGroupPermission] = useState<
    'viewer' | 'editor' | 'admin'
  >('viewer');

  // Public link state
  const [publicLink, setPublicLink] = useState<string | null>(null);
  const [shareToken, setShareToken] = useState<string | null>(null);
  const [linkGenerating, setLinkGenerating] = useState(false);

  // Fetch shared users and groups when dialog opens
  useEffect(() => {
    if (isOpen) {
      fetchSharedUsers();
      fetchSharedGroups();
      fetchPublicLink();
      fetchAvailableUsers();
      fetchAvailableGroups();
    }
  }, [isOpen]);

  // Search available users
  useEffect(() => {
    if (usersSearchQuery.trim()) {
      searchUsers();
    } else {
      setAvailableUsers([]);
    }
  }, [usersSearchQuery]);

  const searchUsers = async () => {
    setUsersLoading(true);
    try {
      const response = await apiClient.get('/users/search', {
        params: {
          query: usersSearchQuery,
          per_page: 10,
        },
      });
      setAvailableUsers(response.data.items || []);
    } catch (err) {
      console.error('Search users error:', err);
    } finally {
      setUsersLoading(false);
    }
  };

  const fetchAvailableUsers = async () => {
    try {
      await apiClient.get('/users', {
        params: {
          per_page: 50,
        },
      });
      // Don't set available users here, only on search
    } catch (err) {
      console.error('Fetch users error:', err);
    }
  };

  const fetchAvailableGroups = async () => {
    setGroupsLoading(true);
    try {
      const response = await apiClient.get('/groups');
      setAvailableGroups(response.data.items || []);
    } catch (err) {
      console.error('Fetch groups error:', err);
    } finally {
      setGroupsLoading(false);
    }
  };

  const fetchSharedUsers = async () => {
    try {
      const response = await apiClient.get(
        `/collections/${collectionId}/shares`
      );
      const userShares = response.data.filter(
        (share: any) => share.shared_with_id
      );
      setSharedUsers(
        userShares.map((share: any) => ({
          id: share.shared_with_id,
          name: share.shared_with_name,
          email: share.shared_with_email,
          permission: share.permission,
        }))
      );
    } catch (err) {
      console.error('Fetch shared users error:', err);
    }
  };

  const fetchSharedGroups = async () => {
    try {
      const response = await apiClient.get(
        `/collections/${collectionId}/shares`
      );
      const groupShares = response.data.filter(
        (share: any) => share.shared_with_group_id
      );
      setSharedGroups(
        groupShares.map((share: any) => ({
          id: share.shared_with_group_id,
          name: share.shared_with_group_name,
          permission: share.permission,
        }))
      );
    } catch (err) {
      console.error('Fetch shared groups error:', err);
    }
  };

  const fetchPublicLink = async () => {
    try {
      const response = await apiClient.get(
        `/collections/${collectionId}/share/token`
      );
      if (response.data.token) {
        setShareToken(response.data.token);
        setPublicLink(
          `${window.location.origin}/shared/collections/${response.data.token}`
        );
      }
    } catch (err) {
      console.error('Fetch public link error:', err);
    }
  };

  const handleShareWithUser = async (userId: string) => {
    setLoading(true);
    setApiError(null);

    try {
      await apiClient.post(`/collections/${collectionId}/share`, {
        shared_with_id: userId,
        permission: selectedUserPermission,
      });

      // Refresh shared users list
      await fetchSharedUsers();
      setUsersSearchQuery('');
      setAvailableUsers([]);
      setSelectedUserPermission('viewer');

      if (onSuccess) {
        onSuccess();
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to share with user';
      setApiError(errorMessage);
      console.error('Share with user error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveUserShare = async (userId: string) => {
    setLoading(true);
    setApiError(null);

    try {
      const shareToDelete = sharedUsers.find((u) => u.id === userId);
      if (!shareToDelete) return;

      // Find the share ID and delete it
      const response = await apiClient.get(
        `/collections/${collectionId}/shares`
      );
      const shareId = response.data.find(
        (s: any) => s.shared_with_id === userId
      )?.id;

      if (shareId) {
        await apiClient.delete(`/collections/${collectionId}/shares/${shareId}`);
        await fetchSharedUsers();
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to remove share';
      setApiError(errorMessage);
      console.error('Remove user share error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleShareWithGroup = async () => {
    if (!selectedGroup) return;

    setLoading(true);
    setApiError(null);

    try {
      await apiClient.post(`/collections/${collectionId}/share`, {
        shared_with_group_id: selectedGroup,
        permission: selectedGroupPermission,
      });

      await fetchSharedGroups();
      setSelectedGroup('');
      setSelectedGroupPermission('viewer');

      if (onSuccess) {
        onSuccess();
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to share with group';
      setApiError(errorMessage);
      console.error('Share with group error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveGroupShare = async (groupId: string) => {
    setLoading(true);
    setApiError(null);

    try {
      // Find the share ID and delete it
      const response = await apiClient.get(
        `/collections/${collectionId}/shares`
      );
      const shareId = response.data.find(
        (s: any) => s.shared_with_group_id === groupId
      )?.id;

      if (shareId) {
        await apiClient.delete(`/collections/${collectionId}/shares/${shareId}`);
        await fetchSharedGroups();
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to remove share';
      setApiError(errorMessage);
      console.error('Remove group share error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleGeneratePublicLink = async () => {
    setLinkGenerating(true);
    setApiError(null);

    try {
      const response = await apiClient.post(
        `/collections/${collectionId}/share/token`
      );
      setShareToken(response.data.token);
      setPublicLink(
        `${window.location.origin}/shared/collections/${response.data.token}`
      );
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to generate link';
      setApiError(errorMessage);
      console.error('Generate link error:', err);
    } finally {
      setLinkGenerating(false);
    }
  };

  const handleCopyLink = () => {
    if (publicLink) {
      navigator.clipboard.writeText(publicLink);
      // Could show a toast notification here
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Share Collection"
      size="lg"
      footer={
        <Button variant="ghost" size="md" onClick={onClose}>
          Done
        </Button>
      }
    >
      <div className="space-y-4">
        {/* API Error Alert */}
        {apiError && (
          <div className="p-3 bg-red-900/30 border border-red-500/50 rounded-lg text-red-400 text-sm">
            {apiError}
          </div>
        )}

        {/* Tab Navigation */}
        <div className="flex gap-2 border-b border-slate-700">
          {(['users', 'groups', 'public_link'] as TabType[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 border-b-2 transition-colors ${
                activeTab === tab
                  ? 'border-ice-gold-400 text-ice-gold-400'
                  : 'border-transparent text-slate-400 hover:text-slate-300'
              }`}
            >
              {tab === 'users'
                ? 'Share with Users'
                : tab === 'groups'
                  ? 'Share with Groups'
                  : 'Public Link'}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="min-h-64 space-y-4">
          {/* Users Tab */}
          {activeTab === 'users' && (
            <div className="space-y-4">
              {/* Search and Add */}
              <div className="space-y-2">
                <Input
                  placeholder="Search users by name or email..."
                  value={usersSearchQuery}
                  onChange={(e) => setUsersSearchQuery(e.target.value)}
                  disabled={loading}
                  type="text"
                />

                {/* User Search Results */}
                {usersSearchQuery && (
                  <div className="max-h-40 overflow-y-auto space-y-2">
                    {usersLoading ? (
                      <div className="flex items-center justify-center py-4">
                        <Spinner />
                      </div>
                    ) : availableUsers.length === 0 ? (
                      <p className="text-sm text-slate-400">No users found</p>
                    ) : (
                      availableUsers.map((user) => (
                        <Card
                          key={user.id}
                          padding="sm"
                          className="flex items-center justify-between gap-2"
                        >
                          <div className="min-w-0">
                            <p className="text-sm font-medium text-slate-100">
                              {user.name}
                            </p>
                            <p className="text-xs text-slate-400 truncate">
                              {user.email}
                            </p>
                          </div>
                          <div className="flex-shrink-0 flex items-center gap-2">
                            <select
                              value={selectedUserPermission}
                              onChange={(e) =>
                                setSelectedUserPermission(
                                  e.target.value as
                                    | 'viewer'
                                    | 'editor'
                                    | 'admin'
                                )
                              }
                              className="px-2 py-1 text-xs bg-slate-700 border border-slate-600 rounded text-slate-200 focus:outline-none focus:ring-1 focus:ring-ice-gold-400"
                            >
                              {permissionOptions.map((opt) => (
                                <option key={opt.value} value={opt.value}>
                                  {opt.label}
                                </option>
                              ))}
                            </select>
                            <Button
                              variant="primary"
                              size="sm"
                              onClick={() => handleShareWithUser(user.id)}
                              disabled={loading}
                            >
                              Add
                            </Button>
                          </div>
                        </Card>
                      ))
                    )}
                  </div>
                )}
              </div>

              {/* Shared Users List */}
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-slate-300">
                  Shared with ({sharedUsers.length})
                </h4>
                {sharedUsers.length === 0 ? (
                  <p className="text-sm text-slate-400">
                    Not shared with any users yet
                  </p>
                ) : (
                  <div className="space-y-2 max-h-40 overflow-y-auto">
                    {sharedUsers.map((user) => (
                      <Card key={user.id} padding="sm" className="flex items-center justify-between">
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-slate-100">
                            {user.name}
                          </p>
                          <p className="text-xs text-slate-400 truncate">
                            {user.email}
                          </p>
                        </div>
                        <div className="flex-shrink-0 flex items-center gap-2">
                          <Badge variant="info" size="sm">
                            {user.permission}
                          </Badge>
                          <button
                            onClick={() => handleRemoveUserShare(user.id)}
                            disabled={loading}
                            className="px-2 py-1 text-xs text-red-400 hover:bg-red-900/20 rounded transition-colors disabled:opacity-50"
                          >
                            Remove
                          </button>
                        </div>
                      </Card>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Groups Tab */}
          {activeTab === 'groups' && (
            <div className="space-y-4">
              {/* Select and Add Group */}
              <div className="space-y-2">
                <Select
                  label="Select Group"
                  options={availableGroups.map((g) => ({
                    value: g.id,
                    label: g.name,
                  }))}
                  value={selectedGroup}
                  onChange={(e) => setSelectedGroup(e.target.value)}
                  disabled={loading || groupsLoading}
                  placeholder="Choose a group"
                />

                {selectedGroup && (
                  <div className="flex gap-2">
                    <select
                      value={selectedGroupPermission}
                      onChange={(e) =>
                        setSelectedGroupPermission(
                          e.target.value as 'viewer' | 'editor' | 'admin'
                        )
                      }
                      className="flex-1 px-3 py-2 bg-slate-800 border border-slate-700 rounded text-slate-200 focus:outline-none focus:ring-1 focus:ring-ice-gold-400"
                    >
                      {permissionOptions.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                          {opt.label}
                        </option>
                      ))}
                    </select>
                    <Button
                      variant="primary"
                      size="md"
                      onClick={handleShareWithGroup}
                      disabled={loading || !selectedGroup}
                      isLoading={loading}
                    >
                      Add Group
                    </Button>
                  </div>
                )}
              </div>

              {/* Shared Groups List */}
              <div className="space-y-2">
                <h4 className="text-sm font-medium text-slate-300">
                  Shared with ({sharedGroups.length})
                </h4>
                {sharedGroups.length === 0 ? (
                  <p className="text-sm text-slate-400">
                    Not shared with any groups yet
                  </p>
                ) : (
                  <div className="space-y-2 max-h-40 overflow-y-auto">
                    {sharedGroups.map((group) => (
                      <Card key={group.id} padding="sm" className="flex items-center justify-between">
                        <p className="text-sm font-medium text-slate-100">
                          {group.name}
                        </p>
                        <div className="flex-shrink-0 flex items-center gap-2">
                          <Badge variant="info" size="sm">
                            {group.permission}
                          </Badge>
                          <button
                            onClick={() => handleRemoveGroupShare(group.id)}
                            disabled={loading}
                            className="px-2 py-1 text-xs text-red-400 hover:bg-red-900/20 rounded transition-colors disabled:opacity-50"
                          >
                            Remove
                          </button>
                        </div>
                      </Card>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Public Link Tab */}
          {activeTab === 'public_link' && (
            <div className="space-y-4">
              {publicLink ? (
                <div className="space-y-2">
                  <p className="text-sm text-slate-300">
                    Share this link to allow anyone to view the collection:
                  </p>
                  <div className="flex gap-2">
                    <Input
                      readOnly
                      value={publicLink}
                      className="bg-slate-700 cursor-pointer"
                    />
                    <Button
                      variant="secondary"
                      size="md"
                      onClick={handleCopyLink}
                    >
                      Copy
                    </Button>
                  </div>
                  <p className="text-xs text-slate-400">
                    Link Token: <code className="text-ice-gold-400">{shareToken}</code>
                  </p>
                </div>
              ) : (
                <div className="space-y-2">
                  <p className="text-sm text-slate-400">
                    No public link generated yet
                  </p>
                  <Button
                    variant="primary"
                    size="md"
                    onClick={handleGeneratePublicLink}
                    disabled={linkGenerating}
                    isLoading={linkGenerating}
                  >
                    Generate Public Link
                  </Button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </Modal>
  );
}
