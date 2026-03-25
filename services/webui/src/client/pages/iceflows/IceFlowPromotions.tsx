/**
 * IceFlowPromotions - Promotions history for a flow
 *
 * Features:
 * - Header with flow name and "Request Promotion" button
 * - Filters: status (pending/approved/merged/rejected/cancelled)
 * - Table: Source->Target, Requester, Status, Approvals, Created, Actions
 * - Click row to see promotion details with approvals
 */

import React, { useState, useEffect } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';

interface IceFlowPromotion {
  promotion_id: string;
  source_stage: {
    stage_id: string;
    branch_name: string;
    display_name: string;
  };
  target_stage: {
    stage_id: string;
    branch_name: string;
    display_name: string;
  };
  status: 'pending' | 'approved' | 'merged' | 'rejected' | 'cancelled';
  requested_by: {
    id: string;
    name: string;
    email: string;
  };
  approval_status: {
    approvals_received: number;
    min_approvers: number;
    can_merge: boolean;
  };
  created_at: string;
  merged_at: string | null;
}

interface IceFlow {
  flow_id: string;
  name: string;
  repository_url: string;
}

export const IceFlowPromotions: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  void navigate; // Will be used for navigation
  const [flowData, setFlowData] = useState<IceFlow | null>(null);
  void setFlowData; // Will be used when API is connected
  const [promotions, setPromotions] = useState<IceFlowPromotion[]>([]);
  void setPromotions; // Will be used when API is connected
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedPromotion, setSelectedPromotion] = useState<IceFlowPromotion | null>(null);

  useEffect(() => {
    // TODO: Fetch flow and promotions from API
    setLoading(false);
  }, [id]);

  const filteredPromotions = promotions.filter((promotion) => {
    return statusFilter === 'all' || promotion.status === statusFilter;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-500/20 text-yellow-400';
      case 'approved':
        return 'bg-blue-500/20 text-blue-400';
      case 'merged':
        return 'bg-green-500/20 text-green-400';
      case 'rejected':
        return 'bg-red-500/20 text-red-400';
      case 'cancelled':
        return 'bg-gray-500/20 text-gray-400';
      default:
        return 'bg-ice-navy-500/20 text-ice-navy-400';
    }
  };

  if (loading) {
    return <div className="p-6 text-white">Loading...</div>;
  }

  if (!flowData) {
    return <div className="p-6 text-white">Flow not found</div>;
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <div className="flex items-center space-x-3 mb-2">
            <Link
              to={`/iceflows/${id}`}
              className="text-ice-navy-400 hover:text-white"
            >
              ← Back to Pipeline
            </Link>
          </div>
          <h1 className="text-3xl font-bold text-white">{flowData.name} - Promotions</h1>
          <a
            href={flowData.repository_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-400 hover:text-blue-300 text-sm"
          >
            {flowData.repository_url}
          </a>
        </div>
        <button className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg">
          + Request Promotion
        </button>
      </div>

      {/* Filters */}
      <div className="bg-ice-navy-800 rounded-lg p-4 mb-6">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2 bg-ice-navy-700 text-white rounded-lg border border-ice-navy-600 focus:outline-none focus:border-purple-500"
        >
          <option value="all">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="merged">Merged</option>
          <option value="rejected">Rejected</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>

      {/* Promotions Table */}
      <div className="bg-ice-navy-800 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-ice-navy-700">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-ice-navy-300 uppercase tracking-wider">
                Promotion
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-ice-navy-300 uppercase tracking-wider">
                Requester
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-ice-navy-300 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-ice-navy-300 uppercase tracking-wider">
                Approvals
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-ice-navy-300 uppercase tracking-wider">
                Created
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-ice-navy-300 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ice-navy-700">
            {filteredPromotions.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-8 text-center text-ice-navy-400">
                  No promotions found. Request your first promotion to get started.
                </td>
              </tr>
            ) : (
              filteredPromotions.map((promotion) => (
                <tr
                  key={promotion.promotion_id}
                  className="hover:bg-ice-navy-700 transition-colors cursor-pointer"
                  onClick={() => setSelectedPromotion(promotion)}
                >
                  <td className="px-6 py-4">
                    <div className="flex items-center space-x-2">
                      <span className="text-white font-medium">
                        {promotion.source_stage.display_name}
                      </span>
                      <span className="text-ice-navy-400">→</span>
                      <span className="text-white font-medium">
                        {promotion.target_stage.display_name}
                      </span>
                    </div>
                    <div className="flex items-center space-x-2 mt-1 text-sm text-ice-navy-400">
                      <code className="bg-ice-navy-600 px-2 py-0.5 rounded">
                        {promotion.source_stage.branch_name}
                      </code>
                      <span>→</span>
                      <code className="bg-ice-navy-600 px-2 py-0.5 rounded">
                        {promotion.target_stage.branch_name}
                      </code>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-white">{promotion.requested_by.name}</div>
                    <div className="text-sm text-ice-navy-400">{promotion.requested_by.email}</div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(promotion.status)}`}>
                      {promotion.status}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-white">
                      {promotion.approval_status.approvals_received} / {promotion.approval_status.min_approvers}
                    </div>
                    {promotion.approval_status.can_merge && (
                      <div className="text-sm text-green-400">Ready to merge</div>
                    )}
                  </td>
                  <td className="px-6 py-4 text-ice-navy-300">
                    {new Date(promotion.created_at).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 text-right space-x-2">
                    {promotion.status === 'pending' && (
                      <>
                        <button
                          className="text-green-400 hover:text-green-300"
                          onClick={(e) => {
                            e.stopPropagation();
                            // TODO: Approve
                          }}
                        >
                          Approve
                        </button>
                        <button
                          className="text-red-400 hover:text-red-300"
                          onClick={(e) => {
                            e.stopPropagation();
                            // TODO: Reject
                          }}
                        >
                          Reject
                        </button>
                      </>
                    )}
                    {promotion.status === 'approved' && promotion.approval_status.can_merge && (
                      <button
                        className="text-purple-400 hover:text-purple-300"
                        onClick={(e) => {
                          e.stopPropagation();
                          // TODO: Merge
                        }}
                      >
                        Merge
                      </button>
                    )}
                    <button
                      className="text-blue-400 hover:text-blue-300"
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedPromotion(promotion);
                      }}
                    >
                      Details
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Promotion Detail Modal */}
      {selectedPromotion && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          onClick={() => setSelectedPromotion(null)}
        >
          <div
            className="bg-ice-navy-800 rounded-lg p-6 max-w-2xl w-full mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-start mb-4">
              <h2 className="text-2xl font-bold text-white">Promotion Details</h2>
              <button
                onClick={() => setSelectedPromotion(null)}
                className="text-ice-navy-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <p className="text-ice-navy-400 text-sm">Promotion</p>
                <div className="flex items-center space-x-2 text-white">
                  <span className="font-medium">{selectedPromotion.source_stage.display_name}</span>
                  <span className="text-ice-navy-400">→</span>
                  <span className="font-medium">{selectedPromotion.target_stage.display_name}</span>
                </div>
                <div className="flex items-center space-x-2 mt-1 text-sm">
                  <code className="bg-ice-navy-700 px-2 py-1 rounded text-ice-navy-300">
                    {selectedPromotion.source_stage.branch_name}
                  </code>
                  <span className="text-ice-navy-400">→</span>
                  <code className="bg-ice-navy-700 px-2 py-1 rounded text-ice-navy-300">
                    {selectedPromotion.target_stage.branch_name}
                  </code>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-ice-navy-400 text-sm">Status</p>
                  <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${getStatusColor(selectedPromotion.status)}`}>
                    {selectedPromotion.status}
                  </span>
                </div>
                <div>
                  <p className="text-ice-navy-400 text-sm">Requested By</p>
                  <p className="text-white">{selectedPromotion.requested_by.name}</p>
                </div>
                <div>
                  <p className="text-ice-navy-400 text-sm">Created At</p>
                  <p className="text-white">{new Date(selectedPromotion.created_at).toLocaleString()}</p>
                </div>
                {selectedPromotion.merged_at && (
                  <div>
                    <p className="text-ice-navy-400 text-sm">Merged At</p>
                    <p className="text-white">{new Date(selectedPromotion.merged_at).toLocaleString()}</p>
                  </div>
                )}
              </div>

              <div>
                <p className="text-ice-navy-400 text-sm mb-2">Approval Status</p>
                <div className="bg-ice-navy-700 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-white">
                      {selectedPromotion.approval_status.approvals_received} of {selectedPromotion.approval_status.min_approvers} required approvals
                    </span>
                    {selectedPromotion.approval_status.can_merge && (
                      <span className="px-3 py-1 bg-green-500/20 text-green-400 rounded text-sm font-medium">
                        Ready to merge
                      </span>
                    )}
                  </div>
                  <div className="mt-2 bg-ice-navy-600 rounded-full h-2">
                    <div
                      className="bg-purple-600 h-2 rounded-full transition-all"
                      style={{
                        width: `${(selectedPromotion.approval_status.approvals_received / selectedPromotion.approval_status.min_approvers) * 100}%`
                      }}
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t border-ice-navy-700">
                <button
                  onClick={() => setSelectedPromotion(null)}
                  className="px-4 py-2 bg-ice-navy-700 text-white rounded-lg hover:bg-ice-navy-600"
                >
                  Close
                </button>
                {selectedPromotion.status === 'approved' && selectedPromotion.approval_status.can_merge && (
                  <button className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg">
                    Merge Now
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default IceFlowPromotions;
