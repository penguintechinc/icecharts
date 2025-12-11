import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../lib/api';
import Button from '../components/Button';
import type { Group } from '../types';

export default function Groups() {
  const [groups, setGroups] = useState<Group[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newGroupName, setNewGroupName] = useState('');
  const [newGroupDescription, setNewGroupDescription] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  useEffect(() => {
    fetchGroups();
  }, [searchQuery]);

  const fetchGroups = async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams({
        ...(searchQuery && { search: searchQuery }),
      });

      const response = await api.get<{ success?: boolean; groups?: Group[]; items?: Group[] }>(
        `/groups?${params}`
      );
      setGroups(response.data.groups || response.data.items || []);
    } catch (err) {
      console.error('Failed to fetch groups:', err);
      setGroups([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateGroup = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsCreating(true);

    try {
      await api.post('/groups', {
        name: newGroupName,
        description: newGroupDescription || undefined,
      });

      setNewGroupName('');
      setNewGroupDescription('');
      setShowCreateModal(false);
      fetchGroups();
    } catch (err) {
      console.error('Failed to create group:', err);
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gold-400">Groups</h1>
          <p className="text-dark-400 mt-1">
            Collaborate with team members on drawings
          </p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>
          Create New Group
        </Button>
      </div>

      {/* Search */}
      <div className="card mb-6">
        <input
          type="text"
          placeholder="Search groups..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="input w-full"
        />
      </div>

      {/* Groups List */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="card animate-pulse">
              <div className="h-4 bg-dark-700 rounded w-3/4 mb-2"></div>
              <div className="h-3 bg-dark-700 rounded w-full mb-2"></div>
              <div className="h-3 bg-dark-700 rounded w-1/2"></div>
            </div>
          ))}
        </div>
      ) : groups.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {groups.map((group) => (
            <Link
              key={group.id}
              to={`/groups/${group.id}`}
              className="card hover:bg-dark-850 transition-colors"
            >
              <div className="flex items-start justify-between mb-3">
                <h3 className="text-lg font-medium text-gold-400">
                  {group.name}
                </h3>
                <span className="text-xs px-2 py-1 rounded bg-dark-800 text-dark-400">
                  Owner: {group.owner_name}
                </span>
              </div>

              {group.description && (
                <p className="text-sm text-dark-400 mb-4 line-clamp-2">
                  {group.description}
                </p>
              )}

              <div className="flex items-center gap-6 text-sm">
                <div className="flex items-center gap-2 text-dark-500">
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9 6a3 3 0 11-6 0 3 3 0 016 0zM17 6a3 3 0 11-6 0 3 3 0 016 0zM12.93 17c.046-.327.07-.66.07-1a6.97 6.97 0 00-1.5-4.33A5 5 0 0119 16v1h-6.07zM6 11a5 5 0 015 5v1H1v-1a5 5 0 015-5z" />
                  </svg>
                  <span>{group.member_count} members</span>
                </div>
                <div className="flex items-center gap-2 text-dark-500">
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" />
                  </svg>
                  <span>{group.drawing_count} drawings</span>
                </div>
              </div>

              <div className="mt-3 text-xs text-dark-600">
                Created {new Date(group.created_at).toLocaleDateString()}
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="card text-center py-12">
          <p className="text-dark-400 mb-4">
            {searchQuery ? 'No groups found' : 'No groups yet'}
          </p>
          <Button onClick={() => setShowCreateModal(true)}>
            Create Your First Group
          </Button>
        </div>
      )}

      {/* Create Group Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="card max-w-md w-full">
            <h2 className="text-xl font-bold text-gold-400 mb-4">
              Create New Group
            </h2>

            <form onSubmit={handleCreateGroup} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gold-400 mb-2">
                  Group Name
                </label>
                <input
                  type="text"
                  value={newGroupName}
                  onChange={(e) => setNewGroupName(e.target.value)}
                  className="input w-full"
                  placeholder="My Team"
                  required
                  autoFocus
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gold-400 mb-2">
                  Description (optional)
                </label>
                <textarea
                  value={newGroupDescription}
                  onChange={(e) => setNewGroupDescription(e.target.value)}
                  className="input w-full h-24 resize-none"
                  placeholder="Describe what this group is for..."
                />
              </div>

              <div className="flex gap-3 pt-2">
                <Button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    setNewGroupName('');
                    setNewGroupDescription('');
                  }}
                  className="flex-1 bg-dark-800 hover:bg-dark-700"
                >
                  Cancel
                </Button>
                <Button type="submit" className="flex-1" isLoading={isCreating}>
                  Create Group
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
