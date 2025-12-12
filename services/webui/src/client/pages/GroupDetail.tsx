import { useState, useEffect, useRef } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import api from '../lib/api';
import Button from '../components/Button';
import Card from '../components/Card';
import type { Group, GroupMember, Drawing, User } from '../types';

export default function GroupDetail() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [group, setGroup] = useState<Group | null>(null);
  const [members, setMembers] = useState<GroupMember[]>([]);
  const [drawings, setDrawings] = useState<Drawing[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showAddMemberModal, setShowAddMemberModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<User[]>([]);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [selectedRole, setSelectedRole] = useState<'viewer' | 'editor' | 'admin'>('viewer');
  const [isSearching, setIsSearching] = useState(false);
  const [isAddingMember, setIsAddingMember] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const searchTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchGroupData();
  }, [id]);

  const fetchGroupData = async () => {
    setIsLoading(true);
    try {
      const [groupRes, membersRes, drawingsRes] = await Promise.all([
        api.get<{ group: Group } | Group>(`/groups/${id}`),
        api.get<{ items?: GroupMember[]; members?: GroupMember[] }>(`/groups/${id}/members`),
        api.get<{ items?: Drawing[]; drawings?: Drawing[] }>(`/drawings?group_id=${id}`),
      ]);

      // Handle both wrapped and unwrapped responses
      const groupData = 'group' in groupRes.data ? groupRes.data.group : groupRes.data;
      setGroup(groupData);
      // Normalize member data - API may return different field names
      const rawMembers = membersRes.data.items || membersRes.data.members || [];
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const normalizedMembers = (rawMembers as any[]).map((m, index: number) => ({
        id: m.id || m.user_id || index,
        group_id: Number(id),
        user_id: m.user_id,
        user_name: m.user_name || m.full_name || '',
        user_email: m.user_email || m.email || '',
        role: m.role || 'viewer',
        added_at: m.added_at || m.joined_at || '',
      }));
      setMembers(normalizedMembers as GroupMember[]);
      setDrawings(drawingsRes.data.items || drawingsRes.data.drawings || []);
    } catch (err) {
      console.error('Failed to fetch group data:', err);
      // Set empty arrays on error to prevent undefined errors
      setMembers([]);
      setDrawings([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle search with debouncing
  useEffect(() => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    if (!searchQuery || searchQuery.length < 2) {
      setSearchResults([]);
      setShowDropdown(false);
      return;
    }

    setIsSearching(true);
    searchTimeoutRef.current = setTimeout(async () => {
      try {
        const response = await api.get<{ users: User[] }>(
          `/users/search?q=${encodeURIComponent(searchQuery)}&exclude_group=${id}&limit=10`
        );
        setSearchResults(response.data.users || []);
        setShowDropdown(true);
      } catch (err) {
        console.error('Failed to search users:', err);
        setSearchResults([]);
      } finally {
        setIsSearching(false);
      }
    }, 300);

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [searchQuery, id]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedUser) {
      return;
    }

    setIsAddingMember(true);

    try {
      await api.post(`/groups/${id}/members`, { user_id: selectedUser.id, role: selectedRole });
      setSearchQuery('');
      setSelectedUser(null);
      setSelectedRole('viewer');
      setSearchResults([]);
      setShowAddMemberModal(false);
      fetchGroupData();
    } catch (err) {
      console.error('Failed to add member:', err);
    } finally {
      setIsAddingMember(false);
    }
  };

  const handleSelectUser = (user: User) => {
    setSelectedUser(user);
    setSearchQuery(user.email);
    setShowDropdown(false);
  };

  const handleRemoveMember = async (userId: number) => {
    if (!confirm('Remove this member from the group?')) return;

    try {
      await api.delete(`/groups/${id}/members/${userId}`);
      fetchGroupData();
    } catch (err) {
      console.error('Failed to remove member:', err);
    }
  };

  const handleDeleteGroup = async () => {
    if (!confirm('Delete this group? This action cannot be undone.')) return;

    try {
      await api.delete(`/groups/${id}`);
      navigate('/groups');
    } catch (err) {
      console.error('Failed to delete group:', err);
    }
  };

  // Compare as numbers to handle potential type mismatches
  // Admins can also manage all groups
  const isOwner = user?.role === 'admin' || group?.owner_id === user?.id || Number(group?.owner_id) === Number(user?.id);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-ice-gold-400 text-xl">Loading group...</div>
      </div>
    );
  }

  if (!group) {
    return (
      <div className="card text-center">
        <p className="text-red-400 mb-4">Group not found</p>
        <Link to="/groups">
          <Button>Back to Groups</Button>
        </Link>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-ice-gold-400">{group.name}</h1>
            {group.description && (
              <p className="text-ice-navy-400 mt-2">{group.description}</p>
            )}
            <p className="text-ice-navy-500 text-sm mt-2">
              Created {new Date(group.created_at).toLocaleDateString()} by{' '}
              {group.owner_name}
            </p>
          </div>
          {isOwner && (
            <div className="flex gap-2">
              <Button
                onClick={handleDeleteGroup}
                className="bg-red-600 hover:bg-red-700"
              >
                Delete Group
              </Button>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Members Section */}
        <div className="lg:col-span-1">
          <Card title={`Members (${members.length})`}>
            <div className="space-y-3">
              {members.map((member) => (
                <div
                  key={member.id}
                  className="flex items-center justify-between p-2 rounded bg-ice-navy-850"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-ice-gold-400 truncate">
                      {member.user_name}
                    </p>
                    <p className="text-xs text-ice-navy-400 truncate">
                      {member.user_email}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-xs px-2 py-0.5 rounded ${
                        member.role === 'owner'
                          ? 'bg-ice-gold-900/30 text-ice-gold-400'
                          : member.role === 'admin'
                          ? 'bg-red-900/30 text-red-400'
                          : member.role === 'editor'
                          ? 'bg-blue-900/30 text-blue-400'
                          : 'bg-ice-navy-800 text-ice-navy-400'
                      }`}
                    >
                      {member.role}
                    </span>
                    {isOwner && member.role !== 'owner' && (
                      <button
                        onClick={() => handleRemoveMember(member.user_id)}
                        className="text-red-400 hover:text-red-300"
                        title="Remove member"
                      >
                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                          <path
                            fillRule="evenodd"
                            d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                            clipRule="evenodd"
                          />
                        </svg>
                      </button>
                    )}
                  </div>
                </div>
              ))}

              {isOwner && (
                <Button
                  onClick={() => setShowAddMemberModal(true)}
                  className="w-full mt-3"
                >
                  Add Member
                </Button>
              )}
            </div>
          </Card>
        </div>

        {/* Drawings Section */}
        <div className="lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-ice-gold-400">
              Group Drawings ({drawings.length})
            </h2>
          </div>

          {drawings.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {drawings.map((drawing) => (
                <Link
                  key={drawing.id}
                  to={`/drawings/${drawing.id}`}
                  className="card hover:bg-ice-navy-850 transition-colors"
                >
                  <div className="h-24 bg-ice-navy-800 rounded mb-3 flex items-center justify-center overflow-hidden">
                    {drawing.thumbnail_url ? (
                      <img
                        src={drawing.thumbnail_url}
                        alt={drawing.name}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <svg
                        className="w-10 h-10 text-ice-navy-600"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2"
                        />
                      </svg>
                    )}
                  </div>
                  <h3 className="font-medium text-ice-gold-400 truncate mb-1">
                    {drawing.name}
                  </h3>
                  <p className="text-xs text-ice-navy-400">
                    By {drawing.owner_name}
                  </p>
                  <p className="text-xs text-ice-navy-500">
                    Updated {new Date(drawing.updated_at).toLocaleDateString()}
                  </p>
                </Link>
              ))}
            </div>
          ) : (
            <div className="card text-center py-12">
              <p className="text-ice-navy-400">No drawings in this group yet</p>
            </div>
          )}
        </div>
      </div>

      {/* Add Member Modal */}
      {showAddMemberModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="card max-w-md w-full">
            <h2 className="text-xl font-bold text-ice-gold-400 mb-4">Add Member</h2>

            <form onSubmit={handleAddMember} className="space-y-4">
              <div className="relative" ref={dropdownRef}>
                <label className="block text-sm font-medium text-ice-gold-400 mb-2">
                  Search for user
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => {
                      setSearchQuery(e.target.value);
                      setSelectedUser(null);
                    }}
                    onFocus={() => searchResults.length > 0 && setShowDropdown(true)}
                    className="input w-full pr-10"
                    placeholder="Search by email or name..."
                    autoFocus
                  />
                  {isSearching && (
                    <div className="absolute right-3 top-1/2 -translate-y-1/2">
                      <svg className="animate-spin h-5 w-5 text-ice-gold-400" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                    </div>
                  )}
                  {selectedUser && (
                    <div className="absolute right-3 top-1/2 -translate-y-1/2">
                      <svg className="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    </div>
                  )}
                </div>

                {/* Search results dropdown */}
                {showDropdown && searchResults.length > 0 && (
                  <div className="absolute z-10 w-full mt-1 bg-ice-navy-800 border border-ice-navy-600 rounded-lg shadow-lg max-h-60 overflow-auto">
                    {searchResults.map((user) => (
                      <button
                        key={user.id}
                        type="button"
                        onClick={() => handleSelectUser(user)}
                        className="w-full px-4 py-3 text-left hover:bg-ice-navy-700 transition-colors flex items-center gap-3 border-b border-ice-navy-700 last:border-b-0"
                      >
                        <div className="w-8 h-8 rounded-full bg-ice-gold-500/20 flex items-center justify-center flex-shrink-0">
                          <span className="text-ice-gold-400 font-medium text-sm">
                            {user.full_name.charAt(0).toUpperCase()}
                          </span>
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-ice-gold-400 truncate">
                            {user.full_name}
                          </p>
                          <p className="text-xs text-ice-navy-400 truncate">
                            {user.email}
                          </p>
                        </div>
                      </button>
                    ))}
                  </div>
                )}

                {/* No results message */}
                {!isSearching && searchQuery.length >= 2 && searchResults.length === 0 && !selectedUser && (
                  <p className="text-xs text-ice-navy-400 mt-2">
                    No users found matching "{searchQuery}"
                  </p>
                )}

                <p className="text-xs text-ice-navy-500 mt-1">
                  Type at least 2 characters to search for users
                </p>
              </div>

              {/* Role Selection */}
              <div>
                <label className="block text-sm font-medium text-ice-gold-400 mb-2">
                  Role
                </label>
                <div className="grid grid-cols-3 gap-3">
                  <button
                    type="button"
                    onClick={() => setSelectedRole('viewer')}
                    className={`p-3 rounded-lg border-2 transition-all text-left ${
                      selectedRole === 'viewer'
                        ? 'border-ice-gold-500 bg-ice-gold-500/10'
                        : 'border-ice-navy-600 bg-ice-navy-800 hover:border-ice-navy-500'
                    }`}
                  >
                    <div className="font-medium text-ice-gold-400 mb-1">Viewer</div>
                    <div className="text-xs text-ice-navy-400">Can view drawings</div>
                  </button>
                  <button
                    type="button"
                    onClick={() => setSelectedRole('editor')}
                    className={`p-3 rounded-lg border-2 transition-all text-left ${
                      selectedRole === 'editor'
                        ? 'border-ice-gold-500 bg-ice-gold-500/10'
                        : 'border-ice-navy-600 bg-ice-navy-800 hover:border-ice-navy-500'
                    }`}
                  >
                    <div className="font-medium text-ice-gold-400 mb-1">Editor</div>
                    <div className="text-xs text-ice-navy-400">Can create & edit drawings</div>
                  </button>
                  <button
                    type="button"
                    onClick={() => setSelectedRole('admin')}
                    className={`p-3 rounded-lg border-2 transition-all text-left ${
                      selectedRole === 'admin'
                        ? 'border-ice-gold-500 bg-ice-gold-500/10'
                        : 'border-ice-navy-600 bg-ice-navy-800 hover:border-ice-navy-500'
                    }`}
                  >
                    <div className="font-medium text-ice-gold-400 mb-1">Admin</div>
                    <div className="text-xs text-ice-navy-400">Can manage members</div>
                  </button>
                </div>
              </div>

              <div className="flex gap-3 pt-2">
                <Button
                  type="button"
                  onClick={() => {
                    setShowAddMemberModal(false);
                    setSearchQuery('');
                    setSelectedUser(null);
                    setSelectedRole('viewer');
                    setSearchResults([]);
                  }}
                  className="flex-1 bg-ice-navy-800 hover:bg-ice-navy-700"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  className="flex-1"
                  isLoading={isAddingMember}
                  disabled={!selectedUser}
                >
                  Add Member
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
