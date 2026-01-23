/**
 * IceFlowsList - Main list view for IceFlows pipelines
 *
 * Features:
 * - Paginated table with filters (status, provider)
 * - Search by name/repository
 * - Quick actions: Edit, View Promotions, Delete
 * - Create button (top-right)
 */

import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';

interface IceFlow {
  flow_id: string;
  name: string;
  description: string;
  repository_url: string;
  provider: 'github' | 'gitlab';
  default_branch: string;
  status: 'active' | 'paused' | 'draft';
  gitops_enabled: boolean;
  stages_count: number;
  last_promotion_at: string | null;
  created_at: string;
}

export const IceFlowsList: React.FC = () => {
  const navigate = useNavigate();
  const [flows, _setFlows] = useState<IceFlow[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [providerFilter, setProviderFilter] = useState('all');

  useEffect(() => {
    // TODO: Fetch flows from API
    setLoading(false);
  }, []);

  const filteredFlows = flows.filter((flow) => {
    const matchesSearch = flow.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         flow.repository_url.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || flow.status === statusFilter;
    const matchesProvider = providerFilter === 'all' || flow.provider === providerFilter;
    return matchesSearch && matchesStatus && matchesProvider;
  });

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-white">IceFlows Pipelines</h1>
          <p className="text-ice-navy-300 mt-1">Manage GitOps promotion workflows</p>
        </div>
        <Link
          to="/iceflows/create"
          className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
        >
          + Create Pipeline
        </Link>
      </div>

      {/* Filters */}
      <div className="bg-ice-navy-800 rounded-lg p-4 mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
        <input
          type="text"
          placeholder="Search pipelines..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="px-4 py-2 bg-ice-navy-700 text-white rounded-lg border border-ice-navy-600 focus:outline-none focus:border-purple-500"
        />
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2 bg-ice-navy-700 text-white rounded-lg border border-ice-navy-600 focus:outline-none focus:border-purple-500"
        >
          <option value="all">All Statuses</option>
          <option value="active">Active</option>
          <option value="paused">Paused</option>
          <option value="draft">Draft</option>
        </select>
        <select
          value={providerFilter}
          onChange={(e) => setProviderFilter(e.target.value)}
          className="px-4 py-2 bg-ice-navy-700 text-white rounded-lg border border-ice-navy-600 focus:outline-none focus:border-purple-500"
        >
          <option value="all">All Providers</option>
          <option value="github">GitHub</option>
          <option value="gitlab">GitLab</option>
        </select>
      </div>

      {/* Flows Table */}
      <div className="bg-ice-navy-800 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-ice-navy-700">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-ice-navy-300 uppercase tracking-wider">
                Pipeline
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-ice-navy-300 uppercase tracking-wider">
                Repository
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-ice-navy-300 uppercase tracking-wider">
                Stages
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-ice-navy-300 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-ice-navy-300 uppercase tracking-wider">
                Last Promotion
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-ice-navy-300 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ice-navy-700">
            {filteredFlows.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-8 text-center text-ice-navy-400">
                  {loading ? 'Loading...' : 'No pipelines found. Create your first pipeline to get started.'}
                </td>
              </tr>
            ) : (
              filteredFlows.map((flow) => (
                <tr
                  key={flow.flow_id}
                  className="hover:bg-ice-navy-700 transition-colors cursor-pointer"
                  onClick={() => navigate(`/iceflows/${flow.flow_id}`)}
                >
                  <td className="px-6 py-4">
                    <div className="text-purple-400 hover:text-purple-300 font-medium">
                      {flow.name}
                    </div>
                    <p className="text-sm text-ice-navy-400">{flow.description}</p>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        flow.provider === 'github' ? 'bg-gray-500/20 text-gray-300' :
                        'bg-orange-500/20 text-orange-400'
                      }`}>
                        {flow.provider}
                      </span>
                      <a
                        href={flow.repository_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300 text-sm"
                        onClick={(e) => e.stopPropagation()}
                      >
                        {flow.repository_url.split('/').slice(-2).join('/')}
                      </a>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-white">{flow.stages_count}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      flow.status === 'active' ? 'bg-green-500/20 text-green-400' :
                      flow.status === 'paused' ? 'bg-yellow-500/20 text-yellow-400' :
                      'bg-blue-500/20 text-blue-400'
                    }`}>
                      {flow.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-ice-navy-300">
                    {flow.last_promotion_at ? new Date(flow.last_promotion_at).toLocaleString() : 'Never'}
                  </td>
                  <td className="px-6 py-4 text-right space-x-2">
                    <Link
                      to={`/iceflows/${flow.flow_id}/edit`}
                      className="text-blue-400 hover:text-blue-300"
                      onClick={(e) => e.stopPropagation()}
                    >
                      Edit
                    </Link>
                    <Link
                      to={`/iceflows/${flow.flow_id}/promotions`}
                      className="text-purple-400 hover:text-purple-300"
                      onClick={(e) => e.stopPropagation()}
                    >
                      Promotions
                    </Link>
                    <button
                      className="text-red-400 hover:text-red-300"
                      onClick={(e) => {
                        e.stopPropagation();
                        // TODO: Delete confirmation
                      }}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default IceFlowsList;
