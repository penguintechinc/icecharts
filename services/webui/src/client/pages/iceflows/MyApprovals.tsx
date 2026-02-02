/**
 * MyApprovals - Centralized dashboard for pending approvals across IceFlows
 *
 * Features:
 * - Grid of approval cards showing pending promotions
 * - Each card shows flow name, branch promotion, requester, and timestamp
 * - Day restriction warning badges
 * - Approve/Reject/Details action buttons
 * - Empty state when no pending approvals
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

interface PendingApproval {
  promotion_id: string;
  flow_name: string;
  repository_url: string;
  source_branch: string;
  target_branch: string;
  requested_by: string;
  requested_at: string;
  is_day_blocked: boolean;
}

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

export const MyApprovals: React.FC = () => {
  const navigate = useNavigate();
  const [approvals, setApprovals] = useState<PendingApproval[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedApproval, setSelectedApproval] = useState<PendingApproval | null>(null);
  const [modalType, setModalType] = useState<'approve' | 'reject' | null>(null);
  const [rejectComment, setRejectComment] = useState('');

  useEffect(() => {
    // TODO: Fetch pending approvals from API
    // Mock data for now
    const mockApprovals: PendingApproval[] = [
      {
        promotion_id: 'promo-001',
        flow_name: 'Production Deployment',
        repository_url: 'https://github.com/company/api-service',
        source_branch: 'staging',
        target_branch: 'production',
        requested_by: 'Alice Johnson',
        requested_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        is_day_blocked: false,
      },
      {
        promotion_id: 'promo-002',
        flow_name: 'Canary Release',
        repository_url: 'https://github.com/company/frontend-app',
        source_branch: 'develop',
        target_branch: 'canary',
        requested_by: 'Bob Smith',
        requested_at: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
        is_day_blocked: true,
      },
      {
        promotion_id: 'promo-003',
        flow_name: 'Hotfix Release',
        repository_url: 'https://github.com/company/backend-service',
        source_branch: 'hotfix/critical-bug',
        target_branch: 'main',
        requested_by: 'Charlie Davis',
        requested_at: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
        is_day_blocked: false,
      },
    ];
    setApprovals(mockApprovals);
    setLoading(false);
  }, []);

  const handleApprove = (approval: PendingApproval) => {
    setSelectedApproval(approval);
    setModalType('approve');
  };

  const handleReject = (approval: PendingApproval) => {
    setSelectedApproval(approval);
    setModalType('reject');
  };

  const confirmApprove = () => {
    if (selectedApproval) {
      // TODO: Call API to approve
      console.log('Approved:', selectedApproval.promotion_id);
      setApprovals(approvals.filter(a => a.promotion_id !== selectedApproval.promotion_id));
      setSelectedApproval(null);
      setModalType(null);
    }
  };

  const confirmReject = () => {
    if (selectedApproval && rejectComment.trim()) {
      // TODO: Call API to reject with comment
      console.log('Rejected:', selectedApproval.promotion_id, 'Comment:', rejectComment);
      setApprovals(approvals.filter(a => a.promotion_id !== selectedApproval.promotion_id));
      setSelectedApproval(null);
      setModalType(null);
      setRejectComment('');
    }
  };

  const handleViewDetails = (approval: PendingApproval) => {
    // TODO: Navigate to promotion detail page once route is available
    navigate(`/iceflows/promotions/${approval.promotion_id}`);
  };

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
        <h1 className="text-3xl font-bold text-white mb-2">My Pending Approvals</h1>
        <p className="text-ice-navy-300">
          You have {approvals.length} promotion{approvals.length !== 1 ? 's' : ''} awaiting your approval
        </p>
      </div>

      {/* Approvals Grid or Empty State */}
      {approvals.length === 0 ? (
        <div className="flex flex-col items-center justify-center min-h-64 bg-ice-navy-800 rounded-lg border border-ice-navy-700">
          <div className="text-6xl mb-4">✓</div>
          <h2 className="text-2xl font-bold text-white mb-2">All caught up!</h2>
          <p className="text-ice-navy-300">No pending approvals right now</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {approvals.map((approval) => (
            <div
              key={approval.promotion_id}
              className="bg-ice-navy-800 rounded-lg border border-ice-navy-700 hover:border-purple-500 transition-colors p-4"
            >
              {/* Card Header */}
              <div className="mb-4">
                <h3 className="text-lg font-bold text-white truncate">{approval.flow_name}</h3>
                <a
                  href={approval.repository_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-blue-400 hover:text-blue-300 truncate inline-block"
                  onClick={(e) => e.stopPropagation()}
                >
                  {approval.repository_url.split('/').slice(-2).join('/')}
                </a>
              </div>

              {/* Branch Promotion */}
              <div className="bg-ice-navy-700 rounded-lg p-3 mb-4">
                <div className="flex items-center justify-center space-x-3 text-sm">
                  <code className="bg-ice-navy-600 px-2 py-1 rounded text-ice-navy-200">
                    {approval.source_branch}
                  </code>
                  <span className="text-ice-navy-400">→</span>
                  <code className="bg-ice-navy-600 px-2 py-1 rounded text-ice-navy-200">
                    {approval.target_branch}
                  </code>
                </div>
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

              {/* Day Restriction Warning */}
              {approval.is_day_blocked && (
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
                <p className="text-ice-navy-400 text-sm">Pipeline</p>
                <p className="text-white font-medium">{selectedApproval.flow_name}</p>
              </div>
              <div>
                <p className="text-ice-navy-400 text-sm">Promotion</p>
                <p className="text-white font-medium">
                  {selectedApproval.source_branch} → {selectedApproval.target_branch}
                </p>
              </div>
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
            <h2 className="text-2xl font-bold text-white mb-4">Reject Promotion</h2>
            <div className="space-y-3 mb-6">
              <div>
                <p className="text-ice-navy-400 text-sm">Pipeline</p>
                <p className="text-white font-medium">{selectedApproval.flow_name}</p>
              </div>
              <div>
                <p className="text-ice-navy-400 text-sm">Promotion</p>
                <p className="text-white font-medium">
                  {selectedApproval.source_branch} → {selectedApproval.target_branch}
                </p>
              </div>
              <div>
                <label className="block text-ice-navy-400 text-sm mb-2">
                  Rejection Comment <span className="text-red-400">*</span>
                </label>
                <textarea
                  value={rejectComment}
                  onChange={(e) => setRejectComment(e.target.value)}
                  placeholder="Why are you rejecting this promotion?"
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

export default MyApprovals;
