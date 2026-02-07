/**
 * ApprovalCenter - Unified approval dashboard for IceFlows and IceStreams
 *
 * Features:
 * - Tabbed interface (All, IceFlows, IceStreams)
 * - Unified card grid layout
 * - Type badges for discrimination
 * - Parallel API fetching
 * - Auto-refresh every 30 seconds
 * - Approve/Reject actions per type
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../lib/api';

type ApprovalType = 'iceflow' | 'icestream';

interface BaseApproval {
  type: ApprovalType;
  requested_by: string;
  requested_at: string;
}

interface IceFlowApproval extends BaseApproval {
  type: 'iceflow';
  promotion_id: string;
  flow_name: string;
  repository_url: string;
  source_branch: string;
  target_branch: string;
  is_day_blocked: boolean;
}

interface IceStreamApproval extends BaseApproval {
  type: 'icestream';
  execution_id: string;
  playbook_id: string;
  playbook_name: string;
  gate_id: string | null;
  gate_name: string;
  paused_at: string;
}

type UnifiedApproval = IceFlowApproval | IceStreamApproval;

type TabType = 'all' | 'iceflows' | 'icestreams';

const getRelativeTime = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
  if (diffDays < 7) return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
  return date.toLocaleDateString();
};

const getAvatarPlaceholder = (name: string): string => {
  return name
    .split(' ')
    .map(part => part[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
};

const getAvatarColor = (name: string): string => {
  const colors = [
    'bg-purple-600',
    'bg-blue-600',
    'bg-pink-600',
    'bg-green-600',
    'bg-indigo-600',
    'bg-teal-600',
  ];
  return colors[name.length % colors.length];
};

export const ApprovalCenter: React.FC = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<TabType>('all');
  const [approvals, setApprovals] = useState<UnifiedApproval[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedApproval, setSelectedApproval] = useState<UnifiedApproval | null>(null);
  const [modalType, setModalType] = useState<'approve' | 'reject' | null>(null);
  const [rejectComment, setRejectComment] = useState('');
  const [refreshing, setRefreshing] = useState(false);

  const fetchApprovals = async (showRefreshIndicator = false) => {
    if (showRefreshIndicator) {
      setRefreshing(true);
    }

    try {
      const [iceflowsRes, icestreamsRes] = await Promise.all([
        api.get('/iceflows/my-approvals').catch(() => ({ data: { pending_approvals: [] } })),
        api.get('/playbooks/my-approvals').catch(() => ({ data: { pending_approvals: [] } })),
      ]);

      const iceflowApprovals: IceFlowApproval[] = (
        iceflowsRes.data.pending_approvals || []
      ).map((a: any) => ({
        ...a,
        type: 'iceflow' as ApprovalType,
      }));

      const icestreamApprovals: IceStreamApproval[] = (
        icestreamsRes.data.pending_approvals || []
      ).map((a: any) => ({
        ...a,
        type: 'icestream' as ApprovalType,
      }));

      const unified = [...iceflowApprovals, ...icestreamApprovals];
      setApprovals(unified);
    } catch (error) {
      console.error('Error fetching approvals:', error);
      setApprovals([]);
    } finally {
      setLoading(false);
      if (showRefreshIndicator) {
        setRefreshing(false);
      }
    }
  };

  useEffect(() => {
    fetchApprovals();

    // Auto-refresh every 30 seconds
    const interval = setInterval(() => fetchApprovals(true), 30000);
    return () => clearInterval(interval);
  }, []);

  const handleApprove = (approval: UnifiedApproval) => {
    setSelectedApproval(approval);
    setModalType('approve');
  };

  const handleReject = (approval: UnifiedApproval) => {
    setSelectedApproval(approval);
    setModalType('reject');
  };

  const confirmApprove = async () => {
    if (!selectedApproval) return;

    try {
      if (selectedApproval.type === 'iceflow') {
        await api.post(`/iceflows/promotions/${selectedApproval.promotion_id}/approve`, {
          comment: '',
        });
      } else {
        await api.post(`/playbooks/executions/${selectedApproval.execution_id}/approve`, {
          comment: '',
        });
      }

      // Remove from list
      setApprovals(approvals.filter(a => {
        if (a.type === 'iceflow' && selectedApproval.type === 'iceflow') {
          return a.promotion_id !== selectedApproval.promotion_id;
        } else if (a.type === 'icestream' && selectedApproval.type === 'icestream') {
          return a.execution_id !== selectedApproval.execution_id;
        }
        return true;
      }));

      setSelectedApproval(null);
      setModalType(null);
    } catch (error) {
      console.error('Error approving:', error);
      alert('Failed to approve. Please try again.');
    }
  };

  const confirmReject = async () => {
    if (!selectedApproval || !rejectComment.trim()) return;

    try {
      if (selectedApproval.type === 'iceflow') {
        await api.post(`/iceflows/promotions/${selectedApproval.promotion_id}/reject`, {
          comment: rejectComment,
        });
      } else {
        await api.post(`/playbooks/executions/${selectedApproval.execution_id}/reject`, {
          comment: rejectComment,
        });
      }

      // Remove from list
      setApprovals(approvals.filter(a => {
        if (a.type === 'iceflow' && selectedApproval.type === 'iceflow') {
          return a.promotion_id !== selectedApproval.promotion_id;
        } else if (a.type === 'icestream' && selectedApproval.type === 'icestream') {
          return a.execution_id !== selectedApproval.execution_id;
        }
        return true;
      }));

      setSelectedApproval(null);
      setModalType(null);
      setRejectComment('');
    } catch (error) {
      console.error('Error rejecting:', error);
      alert('Failed to reject. Please try again.');
    }
  };

  const handleViewDetails = (approval: UnifiedApproval) => {
    if (approval.type === 'iceflow') {
      navigate(`/iceflows/promotions/${approval.promotion_id}`);
    } else {
      navigate(`/playbooks/executions/${approval.execution_id}`);
    }
  };

  const filteredApprovals = approvals.filter(approval => {
    if (activeTab === 'all') return true;
    if (activeTab === 'iceflows') return approval.type === 'iceflow';
    if (activeTab === 'icestreams') return approval.type === 'icestream';
    return true;
  });

  if (loading) {
    return (
      <div className="p-6 text-white flex items-center justify-center min-h-screen">
        Loading...
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-2">
          <h1 className="text-3xl font-bold text-white">Approval Center</h1>
          {refreshing && (
            <span className="text-sm text-ice-navy-400 animate-pulse">Refreshing...</span>
          )}
        </div>
        <p className="text-ice-navy-300">
          You have {filteredApprovals.length} approval{filteredApprovals.length !== 1 ? 's' : ''} pending
        </p>
      </div>

      {/* Tabs */}
      <div className="mb-6 flex gap-2 border-b border-ice-navy-700">
        <button
          onClick={() => setActiveTab('all')}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === 'all'
              ? 'text-white border-b-2 border-purple-500'
              : 'text-ice-navy-400 hover:text-white'
          }`}
        >
          All ({approvals.length})
        </button>
        <button
          onClick={() => setActiveTab('iceflows')}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === 'iceflows'
              ? 'text-white border-b-2 border-purple-500'
              : 'text-ice-navy-400 hover:text-white'
          }`}
        >
          IceFlows ({approvals.filter(a => a.type === 'iceflow').length})
        </button>
        <button
          onClick={() => setActiveTab('icestreams')}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            activeTab === 'icestreams'
              ? 'text-white border-b-2 border-purple-500'
              : 'text-ice-navy-400 hover:text-white'
          }`}
        >
          IceStreams ({approvals.filter(a => a.type === 'icestream').length})
        </button>
      </div>

      {/* Approvals Grid or Empty State */}
      {filteredApprovals.length === 0 ? (
        <div className="flex flex-col items-center justify-center min-h-64 bg-ice-navy-800 rounded-lg border border-ice-navy-700">
          <div className="text-6xl mb-4">✓</div>
          <h2 className="text-2xl font-bold text-white mb-2">All caught up!</h2>
          <p className="text-ice-navy-300">
            No pending approvals{activeTab !== 'all' ? ` in ${activeTab}` : ''} right now
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredApprovals.map((approval) => (
            <div
              key={
                approval.type === 'iceflow'
                  ? `iceflow-${approval.promotion_id}`
                  : `icestream-${approval.execution_id}`
              }
              className="bg-ice-navy-800 rounded-lg border border-ice-navy-700 hover:border-purple-500 transition-colors p-4"
            >
              {/* Type Badge */}
              <div className="mb-3">
                <span
                  className={`inline-block px-2 py-1 text-xs font-bold rounded ${
                    approval.type === 'iceflow'
                      ? 'bg-blue-600/20 text-blue-400'
                      : 'bg-green-600/20 text-green-400'
                  }`}
                >
                  {approval.type === 'iceflow' ? 'IceFlow' : 'IceStream'}
                </span>
              </div>

              {/* Card Header */}
              <div className="mb-4">
                <h3 className="text-lg font-bold text-white truncate">
                  {approval.type === 'iceflow' ? approval.flow_name : approval.playbook_name}
                </h3>
                {approval.type === 'iceflow' ? (
                  <a
                    href={approval.repository_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-blue-400 hover:text-blue-300 truncate inline-block"
                    onClick={(e) => e.stopPropagation()}
                  >
                    {approval.repository_url.split('/').slice(-2).join('/')}
                  </a>
                ) : (
                  <p className="text-sm text-ice-navy-400">{approval.gate_name}</p>
                )}
              </div>

              {/* Content Info Box */}
              <div className="bg-ice-navy-700 rounded-lg p-3 mb-4">
                {approval.type === 'iceflow' ? (
                  <div className="flex items-center justify-center space-x-3 text-sm">
                    <code className="bg-ice-navy-600 px-2 py-1 rounded text-ice-navy-200">
                      {approval.source_branch}
                    </code>
                    <span className="text-ice-navy-400">→</span>
                    <code className="bg-ice-navy-600 px-2 py-1 rounded text-ice-navy-200">
                      {approval.target_branch}
                    </code>
                  </div>
                ) : (
                  <div className="text-sm text-center text-ice-navy-300">
                    Execution: <code className="text-ice-navy-200">{approval.execution_id.slice(0, 8)}...</code>
                  </div>
                )}
              </div>

              {/* Requester and Time */}
              <div className="flex items-center space-x-3 mb-4">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold ${getAvatarColor(approval.requested_by)}`}>
                  {getAvatarPlaceholder(approval.requested_by)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white truncate">{approval.requested_by}</p>
                  <p className="text-xs text-ice-navy-400">{getRelativeTime(approval.requested_at)}</p>
                </div>
              </div>

              {/* Warning Badges */}
              {approval.type === 'iceflow' && approval.is_day_blocked && (
                <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-2 mb-4">
                  <p className="text-xs text-yellow-300 flex items-center">
                    <span className="mr-2">⚠</span>
                    Restricted by day-of-week policy
                  </p>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-2">
                <button
                  onClick={() => handleApprove(approval)}
                  className="flex-1 px-3 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition-colors"
                >
                  Approve
                </button>
                <button
                  onClick={() => handleReject(approval)}
                  className="flex-1 px-3 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-medium transition-colors"
                >
                  Reject
                </button>
                <button
                  onClick={() => handleViewDetails(approval)}
                  className="flex-1 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors"
                >
                  Details
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Approve Confirmation Modal */}
      {modalType === 'approve' && selectedApproval && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          onClick={() => {
            setSelectedApproval(null);
            setModalType(null);
          }}
        >
          <div
            className="bg-ice-navy-800 rounded-lg p-6 max-w-md w-full mx-4 border border-ice-navy-700"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-2xl font-bold text-white mb-4">Confirm Approval</h2>
            <div className="space-y-3 mb-6">
              <div>
                <p className="text-ice-navy-400 text-sm">Type</p>
                <p className="text-white font-medium">
                  {selectedApproval.type === 'iceflow' ? 'IceFlow Pipeline' : 'IceStream Playbook'}
                </p>
              </div>
              <div>
                <p className="text-ice-navy-400 text-sm">Name</p>
                <p className="text-white font-medium">
                  {selectedApproval.type === 'iceflow'
                    ? selectedApproval.flow_name
                    : selectedApproval.playbook_name}
                </p>
              </div>
              {selectedApproval.type === 'iceflow' && (
                <div>
                  <p className="text-ice-navy-400 text-sm">Promotion</p>
                  <p className="text-white font-medium">
                    {selectedApproval.source_branch} → {selectedApproval.target_branch}
                  </p>
                </div>
              )}
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => {
                  setSelectedApproval(null);
                  setModalType(null);
                }}
                className="flex-1 px-4 py-2 bg-ice-navy-700 text-white rounded-lg hover:bg-ice-navy-600 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={confirmApprove}
                className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors font-medium"
              >
                Approve
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Reject Confirmation Modal */}
      {modalType === 'reject' && selectedApproval && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          onClick={() => {
            setSelectedApproval(null);
            setModalType(null);
            setRejectComment('');
          }}
        >
          <div
            className="bg-ice-navy-800 rounded-lg p-6 max-w-md w-full mx-4 border border-ice-navy-700"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-2xl font-bold text-white mb-4">Reject</h2>
            <div className="space-y-3 mb-6">
              <div>
                <p className="text-ice-navy-400 text-sm">Type</p>
                <p className="text-white font-medium">
                  {selectedApproval.type === 'iceflow' ? 'IceFlow Pipeline' : 'IceStream Playbook'}
                </p>
              </div>
              <div>
                <p className="text-ice-navy-400 text-sm">Name</p>
                <p className="text-white font-medium">
                  {selectedApproval.type === 'iceflow'
                    ? selectedApproval.flow_name
                    : selectedApproval.playbook_name}
                </p>
              </div>
              <div>
                <label className="block text-ice-navy-400 text-sm mb-2">
                  Rejection Comment <span className="text-red-400">*</span>
                </label>
                <textarea
                  value={rejectComment}
                  onChange={(e) => setRejectComment(e.target.value)}
                  placeholder="Why are you rejecting this?"
                  className="w-full px-3 py-2 bg-ice-navy-700 text-white rounded-lg border border-ice-navy-600 focus:outline-none focus:border-red-500 resize-none"
                  rows={3}
                />
              </div>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => {
                  setSelectedApproval(null);
                  setModalType(null);
                  setRejectComment('');
                }}
                className="flex-1 px-4 py-2 bg-ice-navy-700 text-white rounded-lg hover:bg-ice-navy-600 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={confirmReject}
                disabled={!rejectComment.trim()}
                className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-red-900 disabled:cursor-not-allowed text-white rounded-lg transition-colors font-medium"
              >
                Reject
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ApprovalCenter;
