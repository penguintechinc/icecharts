/**
 * IceRunDetail - Function details view
 *
 * Features:
 * - Overview card (name, status, runtime, execution count)
 * - Tabs: Configuration, Executions, Webhook, Versions, Metrics
 * - Action buttons: Execute, Edit, Pause/Activate, Delete
 */

import React, { useState, useEffect } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { WebhookConfig } from './components/WebhookConfig';

export const IceRunDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  void navigate; // Will be used for navigation
  const [activeTab, setActiveTab] = useState('overview');
  const [functionData, setFunctionData] = useState<unknown>(null);
  void functionData; // Will be used when API is connected
  void setFunctionData; // Will be used when API is connected
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // TODO: Fetch function details from API
    setLoading(false);
  }, [id]);

  if (loading) {
    return <div className="p-6 text-white">Loading...</div>;
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-3xl font-bold text-white">Function Details</h1>
          <p className="text-ice-navy-300 mt-1">function_id: {id}</p>
        </div>
        <div className="flex space-x-3">
          <button className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg">
            Execute
          </button>
          <Link
            to={`/iceruns/${id}/edit`}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
          >
            Edit
          </Link>
          <button className="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg">
            Pause
          </button>
          <button className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg">
            Delete
          </button>
        </div>
      </div>

      {/* Overview Card */}
      <div className="bg-ice-navy-800 rounded-lg p-6 mb-6">
        <div className="grid grid-cols-4 gap-6">
          <div>
            <p className="text-ice-navy-400 text-sm">Status</p>
            <p className="text-white text-xl font-semibold">Active</p>
          </div>
          <div>
            <p className="text-ice-navy-400 text-sm">Runtime</p>
            <p className="text-white text-xl font-semibold">Python 3.13</p>
          </div>
          <div>
            <p className="text-ice-navy-400 text-sm">Executions</p>
            <p className="text-white text-xl font-semibold">1,234</p>
          </div>
          <div>
            <p className="text-ice-navy-400 text-sm">Last Executed</p>
            <p className="text-white text-xl font-semibold">2 hours ago</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-ice-navy-700 mb-6">
        <div className="flex space-x-6">
          {['overview', 'executions', 'webhook', 'versions', 'metrics'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`pb-3 border-b-2 transition-colors ${
                activeTab === tab
                  ? 'border-purple-500 text-purple-400'
                  : 'border-transparent text-ice-navy-400 hover:text-white'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div className="bg-ice-navy-800 rounded-lg p-6">
        {activeTab === 'overview' && (
          <div className="space-y-4">
            <div>
              <p className="text-ice-navy-400 text-sm">Description</p>
              <p className="text-white">Function description goes here...</p>
            </div>
            <div>
              <p className="text-ice-navy-400 text-sm">Entrypoint</p>
              <p className="text-white font-mono">main.py</p>
            </div>
            <div>
              <p className="text-ice-navy-400 text-sm">Handler</p>
              <p className="text-white font-mono">handler</p>
            </div>
          </div>
        )}

        {activeTab === 'executions' && (
          <div>
            <Link
              to={`/iceruns/${id}/executions`}
              className="text-purple-400 hover:text-purple-300"
            >
              View all executions →
            </Link>
          </div>
        )}

        {activeTab === 'webhook' && (
          <WebhookConfig functionId={id!} />
        )}

        {activeTab === 'versions' && (
          <div className="text-ice-navy-400">Version history will appear here...</div>
        )}

        {activeTab === 'metrics' && (
          <div className="text-ice-navy-400">Execution metrics and charts will appear here...</div>
        )}
      </div>
    </div>
  );
};

export default IceRunDetail;
