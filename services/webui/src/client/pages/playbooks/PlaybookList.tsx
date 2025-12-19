/**
 * PlaybookList - List of user's playbooks (IceStreams workflows)
 *
 * Shows all playbooks with free user limit indicator.
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../../lib/api';

interface Playbook {
  id: string;
  name: string;
  description: string;
  trigger_type: string;
  is_enabled: boolean;
  status: string;
  execution_count: number;
  last_execution_at: string | null;
  created_at: string;
  updated_at: string;
  tags: string[];
}

interface PlaybookListResponse {
  success: boolean;
  playbooks: Playbook[];
  count: number;
  owned_count: number;
  limit: number;
  can_create: boolean;
}

const PlaybookList: React.FC = () => {
  const [playbooks, setPlaybooks] = useState<Playbook[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [ownedCount, setOwnedCount] = useState(0);
  const [limit, setLimit] = useState(5);
  const [canCreate, setCanCreate] = useState(true);

  useEffect(() => {
    fetchPlaybooks();
  }, []);

  const fetchPlaybooks = async () => {
    try {
      setLoading(true);
      const response = await api.get<PlaybookListResponse>('/playbooks');
      const data = response.data;
      setPlaybooks(data.playbooks || []);
      setOwnedCount(data.owned_count || 0);
      setLimit(data.limit || 5);
      setCanCreate(data.can_create ?? true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Are you sure you want to delete "${name}"?`)) {
      return;
    }

    try {
      await api.delete(`/playbooks/${id}`);
      fetchPlaybooks();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete');
    }
  };

  const getTriggerIcon = (type: string) => {
    switch (type) {
      case 'webhook':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
          </svg>
        );
      case 'schedule':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case 'grpc':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        );
      default: // manual
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
          </svg>
        );
    }
  };

  const getStatusBadge = (status: string, isEnabled: boolean) => {
    if (!isEnabled) {
      return (
        <span className="px-2 py-1 text-xs rounded-full bg-gray-500/20 text-gray-400">
          Disabled
        </span>
      );
    }

    switch (status) {
      case 'active':
        return (
          <span className="px-2 py-1 text-xs rounded-full bg-green-500/20 text-green-400">
            Active
          </span>
        );
      case 'paused':
        return (
          <span className="px-2 py-1 text-xs rounded-full bg-yellow-500/20 text-yellow-400">
            Paused
          </span>
        );
      case 'archived':
        return (
          <span className="px-2 py-1 text-xs rounded-full bg-red-500/20 text-red-400">
            Archived
          </span>
        );
      default:
        return (
          <span className="px-2 py-1 text-xs rounded-full bg-blue-500/20 text-blue-400">
            Draft
          </span>
        );
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Never';
    return new Date(dateStr).toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-pulse text-ice-gold-400">Loading playbooks...</div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Playbooks</h1>
          <p className="text-ice-navy-300 mt-1">
            Automate workflows with IceStreams
          </p>
        </div>
        <div className="flex items-center gap-4">
          {/* Usage indicator */}
          <div className="text-sm text-ice-navy-300">
            <span className="text-ice-gold-400 font-medium">{ownedCount}</span>
            <span className="mx-1">/</span>
            <span>{limit}</span>
            <span className="ml-1">playbooks</span>
          </div>

          {/* Create button */}
          {canCreate ? (
            <Link
              to="/playbooks/new"
              className="flex items-center gap-2 px-4 py-2 bg-ice-gold-500 hover:bg-ice-gold-600 text-ice-navy-900 font-medium rounded-lg transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              New Playbook
            </Link>
          ) : (
            <div className="flex items-center gap-2 px-4 py-2 bg-ice-navy-700 text-ice-navy-400 font-medium rounded-lg cursor-not-allowed">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              Limit Reached
            </div>
          )}
        </div>
      </div>

      {/* Limit warning */}
      {!canCreate && (
        <div className="mb-6 p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
          <div className="flex items-center gap-3">
            <svg className="w-5 h-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div>
              <p className="text-yellow-400 font-medium">Playbook limit reached</p>
              <p className="text-ice-navy-300 text-sm">
                Free users are limited to {limit} playbooks. Upgrade to premium for unlimited playbooks.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400">
          {error}
        </div>
      )}

      {/* Empty state */}
      {playbooks.length === 0 ? (
        <div className="flex flex-col items-center justify-center min-h-[400px] bg-ice-navy-800/50 rounded-lg border border-ice-navy-700">
          <svg className="w-16 h-16 text-ice-navy-600 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          <h3 className="text-lg font-medium text-white mb-2">No playbooks yet</h3>
          <p className="text-ice-navy-400 mb-4">Create your first workflow automation</p>
          {canCreate && (
            <Link
              to="/playbooks/new"
              className="px-4 py-2 bg-ice-gold-500 hover:bg-ice-gold-600 text-ice-navy-900 font-medium rounded-lg transition-colors"
            >
              Create Playbook
            </Link>
          )}
        </div>
      ) : (
        /* Playbook list */
        <div className="grid gap-4">
          {playbooks.map((playbook) => (
            <div
              key={playbook.id}
              className="flex items-center justify-between p-4 bg-ice-navy-800 rounded-lg border border-ice-navy-700 hover:border-ice-navy-600 transition-colors"
            >
              <div className="flex items-center gap-4">
                {/* Trigger icon */}
                <div className="p-2 bg-ice-navy-700 rounded-lg text-ice-gold-400">
                  {getTriggerIcon(playbook.trigger_type)}
                </div>

                {/* Info */}
                <div>
                  <Link
                    to={`/playbooks/${playbook.id}`}
                    className="text-white font-medium hover:text-ice-gold-400 transition-colors"
                  >
                    {playbook.name}
                  </Link>
                  <p className="text-ice-navy-400 text-sm mt-0.5">
                    {playbook.description || 'No description'}
                  </p>
                  <div className="flex items-center gap-3 mt-2">
                    {getStatusBadge(playbook.status, playbook.is_enabled)}
                    <span className="text-ice-navy-500 text-xs">
                      {playbook.execution_count} executions
                    </span>
                    <span className="text-ice-navy-500 text-xs">
                      Last run: {formatDate(playbook.last_execution_at)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2">
                <Link
                  to={`/playbooks/${playbook.id}/edit`}
                  className="p-2 text-ice-navy-400 hover:text-white hover:bg-ice-navy-700 rounded-lg transition-colors"
                  title="Edit"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </Link>
                <button
                  onClick={() => handleDelete(playbook.id, playbook.name)}
                  className="p-2 text-ice-navy-400 hover:text-red-400 hover:bg-ice-navy-700 rounded-lg transition-colors"
                  title="Delete"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default PlaybookList;
