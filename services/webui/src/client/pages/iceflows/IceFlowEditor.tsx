/**
 * IceFlowEditor - Create/Edit flow form
 *
 * Features:
 * - Basic info: name, description, repository URL, provider selection
 * - GitOps settings: enable/disable, yaml path
 * - Stage list with drag-to-reorder
 * - Add stage button
 * - Each stage has: branch name, display name, is_production flag
 * - Save and Cancel buttons
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import apiClient from '../../lib/api';

interface StageFormData {
  stage_id?: string;
  branch_name: string;
  display_name: string;
  stage_order: number;
  is_production: boolean;
  min_approvers: number;
}

interface Credential {
  credential_id: string;
  name: string;
  provider: 'github' | 'gitlab';
  access_token_preview?: string;
}

interface FlowFormData {
  name: string;
  description: string;
  repository_url: string;
  provider: 'github' | 'gitlab';
  default_branch: string;
  credential_id: string;
  status: 'active' | 'paused' | 'draft';
  gitops_enabled: boolean;
  gitops_yaml_path: string;
  stages: StageFormData[];
}

export const IceFlowEditor: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isEdit = !!id;
  const [loading, setLoading] = useState(isEdit);

  const [credentials, setCredentials] = useState<Credential[]>([]);
  const [showCredentialModal, setShowCredentialModal] = useState(false);
  const [newCredential, setNewCredential] = useState({
    name: '',
    provider: 'github' as 'github' | 'gitlab',
    access_token: '',
  });

  const [formData, setFormData] = useState<FlowFormData>({
    name: '',
    description: '',
    repository_url: '',
    provider: 'github',
    default_branch: 'main',
    credential_id: '',
    status: 'draft',
    gitops_enabled: false,
    gitops_yaml_path: '.iceflows/pipeline.yaml',
    stages: [],
  });

  useEffect(() => {
    const fetchCredentials = async () => {
      try {
        const response = await apiClient.get('/v1/iceflows/credentials');
        setCredentials(response.data.credentials || []);
      } catch (error) {
        console.error('Error fetching credentials:', error);
      }
    };

    const fetchFlow = async () => {
      if (isEdit && id) {
        try {
          const response = await apiClient.get(`/v1/iceflows/${id}`);
          const flow = response.data.flow;

          setFormData({
            name: flow.name,
            description: flow.description,
            repository_url: flow.repository_url,
            provider: flow.repository_provider,
            default_branch: flow.default_branch,
            credential_id: flow.credential?.credential_id || '',
            status: flow.status,
            gitops_enabled: flow.gitops_enabled,
            gitops_yaml_path: flow.gitops_path || '.iceflows/pipeline.yaml',
            stages: flow.stages || [],
          });
        } catch (error) {
          console.error('Error fetching flow:', error);
          alert('Failed to load pipeline');
        } finally {
          setLoading(false);
        }
      }
    };

    fetchCredentials();
    fetchFlow();
  }, [id, isEdit]);

  const handleAddStage = () => {
    setFormData({
      ...formData,
      stages: [
        ...formData.stages,
        {
          branch_name: '',
          display_name: '',
          stage_order: formData.stages.length,
          is_production: false,
          min_approvers: 1,
        },
      ],
    });
  };

  const handleRemoveStage = (index: number) => {
    const newStages = formData.stages.filter((_, i) => i !== index);
    // Reorder stages
    newStages.forEach((stage, i) => {
      stage.stage_order = i;
    });
    setFormData({ ...formData, stages: newStages });
  };

  const handleStageChange = (index: number, field: keyof StageFormData, value: any) => {
    const newStages = [...formData.stages];
    newStages[index] = { ...newStages[index], [field]: value };
    setFormData({ ...formData, stages: newStages });
  };

  const moveStage = (index: number, direction: 'up' | 'down') => {
    const newStages = [...formData.stages];
    const targetIndex = direction === 'up' ? index - 1 : index + 1;

    if (targetIndex < 0 || targetIndex >= newStages.length) return;

    // Swap stages
    [newStages[index], newStages[targetIndex]] = [newStages[targetIndex], newStages[index]];

    // Update stage_order
    newStages.forEach((stage, i) => {
      stage.stage_order = i;
    });

    setFormData({ ...formData, stages: newStages });
  };

  const handleCreateCredential = async () => {
    try {
      if (!newCredential.name || !newCredential.access_token) {
        alert('Please provide credential name and access token');
        return;
      }

      const response = await apiClient.post('/v1/iceflows/credentials', {
        name: newCredential.name,
        provider: newCredential.provider,
        access_token: newCredential.access_token,
      });

      const createdCredential = response.data.credential;
      setCredentials([...credentials, createdCredential]);
      setFormData({ ...formData, credential_id: createdCredential.credential_id });
      setShowCredentialModal(false);
      setNewCredential({ name: '', provider: 'github', access_token: '' });
    } catch (error: any) {
      console.error('Error creating credential:', error);
      alert(error.response?.data?.error || 'Failed to create credential');
    }
  };

  const handleSave = async () => {
    try {
      setLoading(true);

      if (isEdit) {
        // Update existing flow
        await apiClient.put(`/v1/iceflows/${id}`, {
          name: formData.name,
          description: formData.description,
          repository_url: formData.repository_url,
          repository_provider: formData.provider,
          default_branch: formData.default_branch,
          credential_id: formData.credential_id || null,
          status: formData.status,
          gitops_enabled: formData.gitops_enabled,
          gitops_path: formData.gitops_yaml_path,
        });

        // TODO: Update stages (requires stage deletion and re-creation)
        // For now, navigate to detail page where stages can be managed separately
        navigate(`/iceflows/${id}`);
      } else {
        // Create new flow
        const flowResponse = await apiClient.post('/v1/iceflows', {
          name: formData.name,
          description: formData.description,
          repository_url: formData.repository_url,
          repository_provider: formData.provider,
          default_branch: formData.default_branch,
          credential_id: formData.credential_id || null,
          status: formData.status,
          gitops_enabled: formData.gitops_enabled,
          gitops_path: formData.gitops_yaml_path,
        });

        const flowId = flowResponse.data.flow.flow_id;

        // Create stages for the new flow
        for (const stage of formData.stages) {
          await apiClient.post(`/v1/iceflows/${flowId}/stages`, {
            branch_name: stage.branch_name,
            display_name: stage.display_name,
            is_production: stage.is_production,
            min_approvers: stage.min_approvers,
          });
        }

        navigate(`/iceflows/${flowId}`);
      }
    } catch (error: any) {
      console.error('Error saving pipeline:', error);
      alert(error.response?.data?.error || 'Failed to save pipeline');
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-6 text-white">Loading...</div>;
  }

  return (
    <div className="p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <h1 className="text-3xl font-bold text-white mb-6">
          {isEdit ? 'Edit Pipeline' : 'Create New Pipeline'}
        </h1>

        {/* Basic Information */}
        <div className="bg-ice-navy-800 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-white mb-4">Basic Information</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-ice-navy-300 mb-2">Pipeline Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-4 py-2 bg-ice-navy-700 text-white rounded-lg border border-ice-navy-600 focus:outline-none focus:border-purple-500"
                placeholder="my-pipeline"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-ice-navy-300 mb-2">Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-4 py-2 bg-ice-navy-700 text-white rounded-lg border border-ice-navy-600 focus:outline-none focus:border-purple-500"
                rows={3}
                placeholder="Describe this pipeline..."
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-ice-navy-300 mb-2">Repository URL</label>
                <input
                  type="text"
                  value={formData.repository_url}
                  onChange={(e) => setFormData({ ...formData, repository_url: e.target.value })}
                  className="w-full px-4 py-2 bg-ice-navy-700 text-white rounded-lg border border-ice-navy-600 focus:outline-none focus:border-purple-500"
                  placeholder="https://github.com/user/repo"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-ice-navy-300 mb-2">Provider</label>
                <select
                  value={formData.provider}
                  onChange={(e) => setFormData({ ...formData, provider: e.target.value as 'github' | 'gitlab' })}
                  className="w-full px-4 py-2 bg-ice-navy-700 text-white rounded-lg border border-ice-navy-600 focus:outline-none focus:border-purple-500"
                >
                  <option value="github">GitHub</option>
                  <option value="gitlab">GitLab</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-ice-navy-300 mb-2">Access Credentials</label>
              <div className="flex gap-2">
                <select
                  value={formData.credential_id}
                  onChange={(e) => setFormData({ ...formData, credential_id: e.target.value })}
                  className="flex-1 px-4 py-2 bg-ice-navy-700 text-white rounded-lg border border-ice-navy-600 focus:outline-none focus:border-purple-500"
                >
                  <option value="">Select credential (optional)</option>
                  {credentials
                    .filter(c => c.provider === formData.provider)
                    .map((cred) => (
                      <option key={cred.credential_id} value={cred.credential_id}>
                        {cred.name} ({cred.access_token_preview})
                      </option>
                    ))}
                </select>
                <button
                  type="button"
                  onClick={() => {
                    setNewCredential({ ...newCredential, provider: formData.provider });
                    setShowCredentialModal(true);
                  }}
                  className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg"
                >
                  + New
                </button>
              </div>
              <p className="text-xs text-ice-navy-400 mt-1">
                Credentials are required for IceFlows to interact with {formData.provider === 'github' ? 'GitHub' : 'GitLab'} (create PRs, merge, etc.)
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-ice-navy-300 mb-2">Default Branch</label>
                <input
                  type="text"
                  value={formData.default_branch}
                  onChange={(e) => setFormData({ ...formData, default_branch: e.target.value })}
                  className="w-full px-4 py-2 bg-ice-navy-700 text-white rounded-lg border border-ice-navy-600 focus:outline-none focus:border-purple-500"
                  placeholder="main"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-ice-navy-300 mb-2">Status</label>
                <select
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value as 'active' | 'paused' | 'draft' })}
                  className="w-full px-4 py-2 bg-ice-navy-700 text-white rounded-lg border border-ice-navy-600 focus:outline-none focus:border-purple-500"
                >
                  <option value="draft">Draft</option>
                  <option value="active">Active</option>
                  <option value="paused">Paused</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* GitOps Settings */}
        <div className="bg-ice-navy-800 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-white mb-4">GitOps Settings</h2>
          <div className="space-y-4">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={formData.gitops_enabled}
                onChange={(e) => setFormData({ ...formData, gitops_enabled: e.target.checked })}
                className="form-checkbox h-5 w-5 text-purple-600 rounded"
              />
              <span className="text-white">Enable GitOps (store pipeline configuration in repository)</span>
            </label>

            {formData.gitops_enabled && (
              <div>
                <label className="block text-sm font-medium text-ice-navy-300 mb-2">YAML Configuration Path</label>
                <input
                  type="text"
                  value={formData.gitops_yaml_path}
                  onChange={(e) => setFormData({ ...formData, gitops_yaml_path: e.target.value })}
                  className="w-full px-4 py-2 bg-ice-navy-700 text-white rounded-lg border border-ice-navy-600 focus:outline-none focus:border-purple-500"
                  placeholder=".iceflows/pipeline.yaml"
                />
              </div>
            )}
          </div>
        </div>

        {/* Stages Configuration */}
        <div className="bg-ice-navy-800 rounded-lg p-6 mb-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-white">Pipeline Stages</h2>
            <button
              onClick={handleAddStage}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg"
            >
              + Add Stage
            </button>
          </div>

          <div className="space-y-4">
            {formData.stages.length === 0 ? (
              <p className="text-ice-navy-400 text-center py-8">
                No stages configured. Add your first stage to get started.
              </p>
            ) : (
              formData.stages.map((stage, index) => (
                <div key={index} className="bg-ice-navy-700 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-4">
                    <h3 className="text-white font-semibold">Stage {index + 1}</h3>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => moveStage(index, 'up')}
                        disabled={index === 0}
                        className="px-2 py-1 bg-ice-navy-600 text-white rounded disabled:opacity-50"
                      >
                        ↑
                      </button>
                      <button
                        onClick={() => moveStage(index, 'down')}
                        disabled={index === formData.stages.length - 1}
                        className="px-2 py-1 bg-ice-navy-600 text-white rounded disabled:opacity-50"
                      >
                        ↓
                      </button>
                      <button
                        onClick={() => handleRemoveStage(index)}
                        className="px-2 py-1 bg-red-600 text-white rounded"
                      >
                        Remove
                      </button>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-ice-navy-300 mb-2">Branch Name</label>
                      <input
                        type="text"
                        value={stage.branch_name}
                        onChange={(e) => handleStageChange(index, 'branch_name', e.target.value)}
                        className="w-full px-4 py-2 bg-ice-navy-600 text-white rounded-lg border border-ice-navy-500 focus:outline-none focus:border-purple-500"
                        placeholder="develop"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-ice-navy-300 mb-2">Display Name</label>
                      <input
                        type="text"
                        value={stage.display_name}
                        onChange={(e) => handleStageChange(index, 'display_name', e.target.value)}
                        className="w-full px-4 py-2 bg-ice-navy-600 text-white rounded-lg border border-ice-navy-500 focus:outline-none focus:border-purple-500"
                        placeholder="Development"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-ice-navy-300 mb-2">Minimum Approvers</label>
                      <input
                        type="number"
                        min="1"
                        value={stage.min_approvers}
                        onChange={(e) => handleStageChange(index, 'min_approvers', parseInt(e.target.value))}
                        className="w-full px-4 py-2 bg-ice-navy-600 text-white rounded-lg border border-ice-navy-500 focus:outline-none focus:border-purple-500"
                      />
                    </div>

                    <div className="flex items-center">
                      <label className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={stage.is_production}
                          onChange={(e) => handleStageChange(index, 'is_production', e.target.checked)}
                          className="form-checkbox h-5 w-5 text-purple-600 rounded"
                        />
                        <span className="text-white">Production Stage</span>
                      </label>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end space-x-4">
          <button
            onClick={() => navigate(isEdit ? `/iceflows/${id}` : '/iceflows')}
            className="px-6 py-2 bg-ice-navy-700 text-white rounded-lg hover:bg-ice-navy-600"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg"
          >
            {isEdit ? 'Save Changes' : 'Create Pipeline'}
          </button>
        </div>
      </div>

      {/* Credential Creation Modal */}
      {showCredentialModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-ice-navy-800 rounded-lg p-6 max-w-md w-full mx-4">
            <h2 className="text-2xl font-bold text-white mb-4">Create New Credential</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-ice-navy-300 mb-2">Credential Name</label>
                <input
                  type="text"
                  value={newCredential.name}
                  onChange={(e) => setNewCredential({ ...newCredential, name: e.target.value })}
                  className="w-full px-4 py-2 bg-ice-navy-700 text-white rounded-lg border border-ice-navy-600 focus:outline-none focus:border-purple-500"
                  placeholder="My GitHub Token"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-ice-navy-300 mb-2">Provider</label>
                <select
                  value={newCredential.provider}
                  onChange={(e) => setNewCredential({ ...newCredential, provider: e.target.value as 'github' | 'gitlab' })}
                  className="w-full px-4 py-2 bg-ice-navy-700 text-white rounded-lg border border-ice-navy-600 focus:outline-none focus:border-purple-500"
                >
                  <option value="github">GitHub</option>
                  <option value="gitlab">GitLab</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-ice-navy-300 mb-2">Access Token</label>
                <input
                  type="password"
                  value={newCredential.access_token}
                  onChange={(e) => setNewCredential({ ...newCredential, access_token: e.target.value })}
                  className="w-full px-4 py-2 bg-ice-navy-700 text-white rounded-lg border border-ice-navy-600 focus:outline-none focus:border-purple-500"
                  placeholder="ghp_..."
                />
                <p className="text-xs text-ice-navy-400 mt-1">
                  {newCredential.provider === 'github'
                    ? 'Create a Personal Access Token at: Settings → Developer settings → Personal access tokens'
                    : 'Create an Access Token at: Settings → Access Tokens'}
                </p>
              </div>
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => {
                  setShowCredentialModal(false);
                  setNewCredential({ name: '', provider: 'github', access_token: '' });
                }}
                className="px-4 py-2 bg-ice-navy-700 text-white rounded-lg hover:bg-ice-navy-600"
              >
                Cancel
              </button>
              <button
                onClick={handleCreateCredential}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg"
              >
                Create Credential
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default IceFlowEditor;
