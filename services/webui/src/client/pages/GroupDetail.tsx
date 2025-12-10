import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import api from '../lib/api';
import Button from '../components/Button';
import Card from '../components/Card';
import type { Group, GroupMember, Drawing } from '../types';

export default function GroupDetail() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [group, setGroup] = useState<Group | null>(null);
  const [members, setMembers] = useState<GroupMember[]>([]);
  const [drawings, setDrawings] = useState<Drawing[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showAddMemberModal, setShowAddMemberModal] = useState(false);
  const [newMemberEmail, setNewMemberEmail] = useState('');
  const [isAddingMember, setIsAddingMember] = useState(false);

  useEffect(() => {
    fetchGroupData();
  }, [id]);

  const fetchGroupData = async () => {
    setIsLoading(true);
    try {
      const [groupRes, membersRes, drawingsRes] = await Promise.all([
        api.get<Group>(`/groups/${id}`),
        api.get<{ items: GroupMember[] }>(`/groups/${id}/members`),
        api.get<{ items: Drawing[] }>(`/drawings?group_id=${id}`),
      ]);

      setGroup(groupRes.data);
      setMembers(membersRes.data.items);
      setDrawings(drawingsRes.data.items);
    } catch (err) {
      console.error('Failed to fetch group data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsAddingMember(true);

    try {
      await api.post(`/groups/${id}/members`, { email: newMemberEmail });
      setNewMemberEmail('');
      setShowAddMemberModal(false);
      fetchGroupData();
    } catch (err) {
      console.error('Failed to add member:', err);
    } finally {
      setIsAddingMember(false);
    }
  };

  const handleRemoveMember = async (memberId: number) => {
    if (!confirm('Remove this member from the group?')) return;

    try {
      await api.delete(`/groups/${id}/members/${memberId}`);
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

  const isOwner = group?.owner_id === user?.id;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gold-400 text-xl">Loading group...</div>
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
            <h1 className="text-2xl font-bold text-gold-400">{group.name}</h1>
            {group.description && (
              <p className="text-dark-400 mt-2">{group.description}</p>
            )}
            <p className="text-dark-500 text-sm mt-2">
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
                  className="flex items-center justify-between p-2 rounded bg-dark-850"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gold-400 truncate">
                      {member.user_name}
                    </p>
                    <p className="text-xs text-dark-400 truncate">
                      {member.user_email}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-xs px-2 py-0.5 rounded ${
                        member.role === 'owner'
                          ? 'bg-gold-900/30 text-gold-400'
                          : 'bg-dark-800 text-dark-400'
                      }`}
                    >
                      {member.role}
                    </span>
                    {isOwner && member.role !== 'owner' && (
                      <button
                        onClick={() => handleRemoveMember(member.id)}
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
            <h2 className="text-xl font-semibold text-gold-400">
              Group Drawings ({drawings.length})
            </h2>
          </div>

          {drawings.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {drawings.map((drawing) => (
                <Link
                  key={drawing.id}
                  to={`/drawings/${drawing.id}`}
                  className="card hover:bg-dark-850 transition-colors"
                >
                  <div className="h-24 bg-dark-800 rounded mb-3 flex items-center justify-center overflow-hidden">
                    {drawing.thumbnail_url ? (
                      <img
                        src={drawing.thumbnail_url}
                        alt={drawing.name}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <svg
                        className="w-10 h-10 text-dark-600"
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
                  <h3 className="font-medium text-gold-400 truncate mb-1">
                    {drawing.name}
                  </h3>
                  <p className="text-xs text-dark-400">
                    By {drawing.owner_name}
                  </p>
                  <p className="text-xs text-dark-500">
                    Updated {new Date(drawing.updated_at).toLocaleDateString()}
                  </p>
                </Link>
              ))}
            </div>
          ) : (
            <div className="card text-center py-12">
              <p className="text-dark-400">No drawings in this group yet</p>
            </div>
          )}
        </div>
      </div>

      {/* Add Member Modal */}
      {showAddMemberModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="card max-w-md w-full">
            <h2 className="text-xl font-bold text-gold-400 mb-4">Add Member</h2>

            <form onSubmit={handleAddMember} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gold-400 mb-2">
                  Member Email
                </label>
                <input
                  type="email"
                  value={newMemberEmail}
                  onChange={(e) => setNewMemberEmail(e.target.value)}
                  className="input w-full"
                  placeholder="user@example.com"
                  required
                  autoFocus
                />
                <p className="text-xs text-dark-500 mt-1">
                  User must have an existing account
                </p>
              </div>

              <div className="flex gap-3 pt-2">
                <Button
                  type="button"
                  onClick={() => {
                    setShowAddMemberModal(false);
                    setNewMemberEmail('');
                  }}
                  className="flex-1 bg-dark-800 hover:bg-dark-700"
                >
                  Cancel
                </Button>
                <Button type="submit" className="flex-1" isLoading={isAddingMember}>
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
