/**
 * IceFlowDetail - Flow details and stage configuration
 *
 * Features:
 * - Header with flow name, repository link, status badge
 * - Pipeline visualization showing stages as connected cards
 * - Tabs: Stages, Promotions, Executions, Settings
 * - Stage configuration panel (slides in when stage is selected)
 * - Action buttons: Request Promotion, Edit Flow, Export YAML
 */

import React, { useState, useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';
import apiClient from '../../lib/api';

interface IceFlowStage {
  stage_id: string;
  branch_name: string;
  display_name: string;
  stage_order: number;
  is_production: boolean;
  min_approvers: number;
  approvers_count: number;
  tests_count: number;
  calls_count: number;
}

interface IceFlow {
  flow_id: string;
  name: string;
  description: string;
  repository_url: string;
  provider: 'github' | 'gitlab';
  status: 'active' | 'paused' | 'draft';
  gitops_enabled: boolean;
  stages: IceFlowStage[];
}

export const IceFlowDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [activeTab, setActiveTab] = useState('stages');
  const [flowData, setFlowData] = useState<IceFlow | null>(null);
  const [selectedStage, setSelectedStage] = useState<IceFlowStage | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchFlow = async () => {
      if (!id) return;

      try {
        const response = await apiClient.get(`/v1/iceflows/${id}`);
        const flow = response.data.flow;

        setFlowData({
          flow_id: flow.flow_id,
          name: flow.name,
          description: flow.description,
          repository_url: flow.repository_url,
          provider: flow.repository_provider,
          status: flow.status,
          gitops_enabled: flow.gitops_enabled,
          stages: flow.stages || [],
        });
      } catch (error) {
        console.error('Error fetching flow:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchFlow();
  }, [id]);

  const handleExportYaml = async () => {
    try {
      const token = localStorage.getItem('authToken');
      const response = await fetch(`/api/v1/iceflows/${id}/export/yaml`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to export YAML');
      }

      // Get filename from Content-Disposition header or use default
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = 'flow.yaml';
      if (contentDisposition) {
        const match = contentDisposition.match(/filename="?([^";\n]+)"?/);
        if (match) {
          filename = match[1];
        }
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Failed to export YAML:', error);
      // TODO: Show error toast
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
      <div className="flex justify-between items-start mb-6">
        <div>
          <div className="flex items-center space-x-3 mb-2">
            <h1 className="text-3xl font-bold text-white">{flowData.name}</h1>
            <span className={`px-3 py-1 rounded-lg text-sm font-medium ${
              flowData.status === 'active' ? 'bg-green-500/20 text-green-400' :
              flowData.status === 'paused' ? 'bg-yellow-500/20 text-yellow-400' :
              'bg-blue-500/20 text-blue-400'
            }`}>
              {flowData.status}
            </span>
            {flowData.gitops_enabled && (
              <span className="px-3 py-1 rounded-lg text-sm font-medium bg-purple-500/20 text-purple-400">
                GitOps
              </span>
            )}
          </div>
          <a
            href={flowData.repository_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-400 hover:text-blue-300"
          >
            {flowData.repository_url}
          </a>
        </div>
        <div className="flex space-x-3">
          <button className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg">
            Request Promotion
          </button>
          <Link
            to={`/iceflows/${id}/edit`}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
          >
            Edit Flow
          </Link>
          <button
            onClick={handleExportYaml}
            className="px-4 py-2 bg-ice-navy-700 hover:bg-ice-navy-600 text-white rounded-lg"
          >
            Export YAML
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-ice-navy-700 mb-6">
        <div className="flex space-x-6">
          {['stages', 'promotions', 'executions', 'settings'].map((tab) => (
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
      {activeTab === 'stages' && (
        <div className="space-y-6">
          {/* Pipeline Visualization */}
          <div className="bg-ice-navy-800 rounded-lg p-6">
            <h2 className="text-xl font-semibold text-white mb-4">Pipeline Stages</h2>
            <div className="flex items-center space-x-4 overflow-x-auto pb-4">
              {flowData.stages.map((stage, index) => (
                <React.Fragment key={stage.stage_id}>
                  <div
                    onClick={() => setSelectedStage(stage)}
                    className={`flex-shrink-0 w-64 bg-ice-navy-700 rounded-lg p-4 cursor-pointer border-2 transition-colors ${
                      selectedStage?.stage_id === stage.stage_id
                        ? 'border-purple-500'
                        : 'border-transparent hover:border-ice-navy-500'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-white font-semibold">{stage.display_name}</h3>
                      {stage.is_production && (
                        <span className="px-2 py-1 rounded text-xs font-medium bg-red-500/20 text-red-400">
                          PROD
                        </span>
                      )}
                    </div>
                    <p className="text-ice-navy-300 text-sm mb-3">
                      <code className="bg-ice-navy-600 px-2 py-1 rounded">{stage.branch_name}</code>
                    </p>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="text-ice-navy-400">Approvers:</span>
                        <span className="text-white ml-1">{stage.approvers_count}</span>
                      </div>
                      <div>
                        <span className="text-ice-navy-400">Tests:</span>
                        <span className="text-white ml-1">{stage.tests_count}</span>
                      </div>
                      <div>
                        <span className="text-ice-navy-400">Calls:</span>
                        <span className="text-white ml-1">{stage.calls_count}</span>
                      </div>
                      <div>
                        <span className="text-ice-navy-400">Min Approvals:</span>
                        <span className="text-white ml-1">{stage.min_approvers}</span>
                      </div>
                    </div>
                  </div>
                  {index < flowData.stages.length - 1 && (
                    <div className="flex-shrink-0">
                      <svg className="w-8 h-8 text-ice-navy-500" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                      </svg>
                    </div>
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>

          {/* Stage Configuration Panel */}
          {selectedStage && (
            <div className="bg-ice-navy-800 rounded-lg p-6">
              <h2 className="text-xl font-semibold text-white mb-4">
                Stage Configuration: {selectedStage.display_name}
              </h2>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-ice-navy-400 text-sm">Branch Name</p>
                    <p className="text-white">{selectedStage.branch_name}</p>
                  </div>
                  <div>
                    <p className="text-ice-navy-400 text-sm">Stage Order</p>
                    <p className="text-white">{selectedStage.stage_order}</p>
                  </div>
                  <div>
                    <p className="text-ice-navy-400 text-sm">Minimum Approvers</p>
                    <p className="text-white">{selectedStage.min_approvers}</p>
                  </div>
                  <div>
                    <p className="text-ice-navy-400 text-sm">Production Stage</p>
                    <p className="text-white">{selectedStage.is_production ? 'Yes' : 'No'}</p>
                  </div>
                </div>
                <div className="pt-4 border-t border-ice-navy-700">
                  <h3 className="text-white font-semibold mb-2">Stage Components</h3>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="bg-ice-navy-700 rounded p-3">
                      <p className="text-ice-navy-400 text-sm">Approvers</p>
                      <p className="text-white text-2xl font-semibold">{selectedStage.approvers_count}</p>
                    </div>
                    <div className="bg-ice-navy-700 rounded p-3">
                      <p className="text-ice-navy-400 text-sm">Tests</p>
                      <p className="text-white text-2xl font-semibold">{selectedStage.tests_count}</p>
                    </div>
                    <div className="bg-ice-navy-700 rounded p-3">
                      <p className="text-ice-navy-400 text-sm">API Calls</p>
                      <p className="text-white text-2xl font-semibold">{selectedStage.calls_count}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'promotions' && (
        <div className="bg-ice-navy-800 rounded-lg p-6">
          <Link
            to={`/iceflows/${id}/promotions`}
            className="text-purple-400 hover:text-purple-300"
          >
            View all promotions →
          </Link>
        </div>
      )}

      {activeTab === 'executions' && (
        <div className="bg-ice-navy-800 rounded-lg p-6 text-ice-navy-400">
          Execution history will appear here...
        </div>
      )}

      {activeTab === 'settings' && (
        <div className="bg-ice-navy-800 rounded-lg p-6">
          <div className="space-y-4">
            <div>
              <p className="text-ice-navy-400 text-sm">Description</p>
              <p className="text-white">{flowData.description}</p>
            </div>
            <div>
              <p className="text-ice-navy-400 text-sm">Provider</p>
              <p className="text-white capitalize">{flowData.provider}</p>
            </div>
            <div>
              <p className="text-ice-navy-400 text-sm">GitOps Enabled</p>
              <p className="text-white">{flowData.gitops_enabled ? 'Yes' : 'No'}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default IceFlowDetail;
