/**
 * PlaybookDetail - View playbook details and execution history
 */

import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../../store/authStore';

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

interface Execution {
  id: string;
  status: string;
  trigger_type: string;
  started_at: string;
  completed_at: string | null;
  duration_ms: number | null;
  error_message: string | null;
}

const PlaybookDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { token } = useAuthStore();

  const [playbook, setPlaybook] = useState<Playbook | null>(null);
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [loading, setLoading] = useState(true);
  const [executing, setExecuting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchPlaybook();
    fetchExecutions();
  }, [id, token]);

  const fetchPlaybook = async () => {
    try {
      const response = await fetch(`/api/v1/playbooks/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!response.ok) {
        if (response.status === 404) {
          navigate('/playbooks');
          return;
        }
        throw new Error('Failed to fetch playbook');
      }

      const data = await response.json();
      setPlaybook(data.playbook);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const fetchExecutions = async () => {
    try {
      const response = await fetch(`/api/v1/playbooks/${id}/executions?limit=20`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setExecutions(data.executions || []);
      }
    } catch (err) {
      console.error('Failed to fetch executions:', err);
    }
  };

  const handleExecute = async () => {
    try {
      setExecuting(true);
      const response = await fetch(`/api/v1/playbooks/${id}/execute`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({}),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to execute');
      }

      // Refresh executions list
      fetchExecutions();
      fetchPlaybook();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to execute');
    } finally {
      setExecuting(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'bg-yellow-500/20 text-yellow-400',
      running: 'bg-blue-500/20 text-blue-400',
      completed: 'bg-green-500/20 text-green-400',
      failed: 'bg-red-500/20 text-red-400',
      cancelled: 'bg-gray-500/20 text-gray-400',
    };
    return (
      <span className={`px-2 py-1 text-xs rounded-full ${colors[status] || colors.pending}`}>
        {status}
      </span>
    );
  };

  const formatDuration = (ms: number | null) => {
    if (!ms) return '-';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-pulse text-ice-gold-400">Loading...</div>
      </div>
    );
  }

  if (!playbook) {
    return (
      <div className="p-6 text-center text-ice-navy-400">
        Playbook not found
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Link
            to="/playbooks"
            className="p-2 text-ice-navy-400 hover:text-white rounded-lg transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-white">{playbook.name}</h1>
            <p className="text-ice-navy-400">{playbook.description || 'No description'}</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleExecute}
            disabled={executing || !playbook.is_enabled}
            className="flex items-center gap-2 px-4 py-2 bg-green-500 hover:bg-green-600 disabled:bg-green-500/50 text-white font-medium rounded-lg transition-colors"
          >
            {executing ? (
              <>
                <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Running...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Run Now
              </>
            )}
          </button>

          <Link
            to={`/playbooks/${id}/edit`}
            className="flex items-center gap-2 px-4 py-2 bg-ice-gold-500 hover:bg-ice-gold-600 text-ice-navy-900 font-medium rounded-lg transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
            Edit
          </Link>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400">
          {error}
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="p-4 bg-ice-navy-800 rounded-lg border border-ice-navy-700">
          <p className="text-ice-navy-400 text-sm">Status</p>
          <p className="text-white text-xl font-semibold mt-1">
            {playbook.is_enabled ? 'Enabled' : 'Disabled'}
          </p>
        </div>
        <div className="p-4 bg-ice-navy-800 rounded-lg border border-ice-navy-700">
          <p className="text-ice-navy-400 text-sm">Trigger Type</p>
          <p className="text-white text-xl font-semibold mt-1 capitalize">
            {playbook.trigger_type}
          </p>
        </div>
        <div className="p-4 bg-ice-navy-800 rounded-lg border border-ice-navy-700">
          <p className="text-ice-navy-400 text-sm">Total Executions</p>
          <p className="text-white text-xl font-semibold mt-1">
            {playbook.execution_count}
          </p>
        </div>
        <div className="p-4 bg-ice-navy-800 rounded-lg border border-ice-navy-700">
          <p className="text-ice-navy-400 text-sm">Last Run</p>
          <p className="text-white text-xl font-semibold mt-1">
            {playbook.last_execution_at
              ? new Date(playbook.last_execution_at).toLocaleDateString()
              : 'Never'}
          </p>
        </div>
      </div>

      {/* Execution History */}
      <div className="bg-ice-navy-800 rounded-lg border border-ice-navy-700">
        <div className="px-4 py-3 border-b border-ice-navy-700">
          <h2 className="text-lg font-semibold text-white">Execution History</h2>
        </div>

        {executions.length === 0 ? (
          <div className="p-8 text-center text-ice-navy-500">
            No executions yet. Run the playbook to see results here.
          </div>
        ) : (
          <div className="divide-y divide-ice-navy-700">
            {executions.map((execution) => (
              <div key={execution.id} className="px-4 py-3 flex items-center justify-between">
                <div className="flex items-center gap-4">
                  {getStatusBadge(execution.status)}
                  <span className="text-ice-navy-400 text-sm">
                    {formatDate(execution.started_at)}
                  </span>
                  <span className="text-ice-navy-500 text-sm">
                    {formatDuration(execution.duration_ms)}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  {execution.error_message && (
                    <span className="text-red-400 text-sm truncate max-w-[200px]">
                      {execution.error_message}
                    </span>
                  )}
                  <Link
                    to={`/playbooks/${id}/executions/${execution.id}`}
                    className="text-ice-gold-400 text-sm hover:underline"
                  >
                    Details
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default PlaybookDetail;
