import { useState, useEffect } from 'react';
import api from '../../lib/api';
import Button from '../../components/Button';
import Card from '../../components/Card';
import type { SSOConfiguration } from '../../types';

export default function SSOConfigurationPage() {
  const [configs, setConfigs] = useState<SSOConfiguration[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingConfig, setEditingConfig] = useState<SSOConfiguration | null>(null);
  const [formData, setFormData] = useState({
    provider: 'google' as 'google' | 'saml' | 'oauth2',
    enabled: true,
    client_id: '',
    client_secret: '',
    metadata_url: '',
  });
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    fetchConfigs();
  }, []);

  const fetchConfigs = async () => {
    setIsLoading(true);
    try {
      const response = await api.get<{ items: SSOConfiguration[] }>('/admin/sso');
      setConfigs(response.data.items);
    } catch (err) {
      console.error('Failed to fetch SSO configs:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);

    try {
      if (editingConfig) {
        await api.put(`/admin/sso/${editingConfig.id}`, formData);
      } else {
        await api.post('/admin/sso', formData);
      }

      setShowCreateModal(false);
      setEditingConfig(null);
      setFormData({
        provider: 'google',
        enabled: true,
        client_id: '',
        client_secret: '',
        metadata_url: '',
      });
      fetchConfigs();
    } catch (err) {
      console.error('Failed to save SSO config:', err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleEdit = (config: SSOConfiguration) => {
    setEditingConfig(config);
    setFormData({
      provider: config.provider,
      enabled: config.enabled,
      client_id: config.client_id,
      client_secret: '',
      metadata_url: config.metadata_url || '',
    });
    setShowCreateModal(true);
  };

  const handleToggleEnabled = async (configId: number, enabled: boolean) => {
    try {
      await api.patch(`/admin/sso/${configId}`, { enabled: !enabled });
      fetchConfigs();
    } catch (err) {
      console.error('Failed to toggle SSO config:', err);
    }
  };

  const handleDelete = async (configId: number) => {
    if (!confirm('Delete this SSO configuration?')) return;

    try {
      await api.delete(`/admin/sso/${configId}`);
      fetchConfigs();
    } catch (err) {
      console.error('Failed to delete SSO config:', err);
    }
  };

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gold-400">SSO Configuration</h1>
          <p className="text-dark-400 mt-1">
            Configure Single Sign-On providers (Enterprise feature)
          </p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>
          Add SSO Provider
        </Button>
      </div>

      {/* SSO Configurations */}
      {isLoading ? (
        <div className="grid grid-cols-1 gap-4">
          {[...Array(2)].map((_, i) => (
            <div key={i} className="card animate-pulse">
              <div className="h-6 bg-dark-700 rounded w-1/3 mb-3"></div>
              <div className="h-4 bg-dark-700 rounded w-full mb-2"></div>
              <div className="h-4 bg-dark-700 rounded w-2/3"></div>
            </div>
          ))}
        </div>
      ) : configs.length > 0 ? (
        <div className="grid grid-cols-1 gap-4">
          {configs.map((config) => (
            <Card key={config.id}>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-3">
                    <h3 className="text-lg font-medium text-gold-400">
                      {config.provider.toUpperCase()}
                    </h3>
                    <span
                      className={`text-xs px-2 py-1 rounded ${
                        config.enabled
                          ? 'bg-green-900/30 text-green-400'
                          : 'bg-red-900/30 text-red-400'
                      }`}
                    >
                      {config.enabled ? 'Enabled' : 'Disabled'}
                    </span>
                  </div>

                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2">
                      <span className="text-dark-400 w-32">Client ID:</span>
                      <span className="text-gold-400 font-mono">
                        {config.client_id}
                      </span>
                    </div>
                    {config.metadata_url && (
                      <div className="flex items-center gap-2">
                        <span className="text-dark-400 w-32">Metadata URL:</span>
                        <span className="text-gold-400 font-mono text-xs truncate">
                          {config.metadata_url}
                        </span>
                      </div>
                    )}
                    <div className="flex items-center gap-2 text-dark-500 text-xs">
                      <span>
                        Created {new Date(config.created_at).toLocaleDateString()}
                      </span>
                      <span>•</span>
                      <span>
                        Updated {new Date(config.updated_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleEdit(config)}
                    className="px-3 py-1.5 text-sm text-gold-400 hover:text-gold-300"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleToggleEnabled(config.id, config.enabled)}
                    className={`px-3 py-1.5 text-sm ${
                      config.enabled
                        ? 'text-yellow-400 hover:text-yellow-300'
                        : 'text-green-400 hover:text-green-300'
                    }`}
                  >
                    {config.enabled ? 'Disable' : 'Enable'}
                  </button>
                  <button
                    onClick={() => handleDelete(config.id)}
                    className="px-3 py-1.5 text-sm text-red-400 hover:text-red-300"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      ) : (
        <div className="card text-center py-12">
          <p className="text-dark-400 mb-4">No SSO providers configured</p>
          <Button onClick={() => setShowCreateModal(true)}>
            Add Your First SSO Provider
          </Button>
        </div>
      )}

      {/* Create/Edit Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="card max-w-lg w-full max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold text-gold-400 mb-4">
              {editingConfig ? 'Edit SSO Provider' : 'Add SSO Provider'}
            </h2>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gold-400 mb-2">
                  Provider Type
                </label>
                <select
                  value={formData.provider}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      provider: e.target.value as 'google' | 'saml' | 'oauth2',
                    })
                  }
                  className="input w-full"
                  disabled={!!editingConfig}
                >
                  <option value="google">Google OAuth</option>
                  <option value="saml">SAML 2.0</option>
                  <option value="oauth2">Generic OAuth2</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gold-400 mb-2">
                  Client ID
                </label>
                <input
                  type="text"
                  value={formData.client_id}
                  onChange={(e) =>
                    setFormData({ ...formData, client_id: e.target.value })
                  }
                  className="input w-full font-mono text-sm"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gold-400 mb-2">
                  Client Secret
                </label>
                <input
                  type="password"
                  value={formData.client_secret}
                  onChange={(e) =>
                    setFormData({ ...formData, client_secret: e.target.value })
                  }
                  className="input w-full font-mono text-sm"
                  required={!editingConfig}
                  placeholder={editingConfig ? '(unchanged)' : ''}
                />
              </div>

              {(formData.provider === 'saml' || formData.provider === 'oauth2') && (
                <div>
                  <label className="block text-sm font-medium text-gold-400 mb-2">
                    Metadata URL
                  </label>
                  <input
                    type="url"
                    value={formData.metadata_url}
                    onChange={(e) =>
                      setFormData({ ...formData, metadata_url: e.target.value })
                    }
                    className="input w-full font-mono text-sm"
                    placeholder="https://..."
                  />
                </div>
              )}

              <div>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.enabled}
                    onChange={(e) =>
                      setFormData({ ...formData, enabled: e.target.checked })
                    }
                    className="w-5 h-5"
                  />
                  <span className="text-gold-400">Enable this provider</span>
                </label>
              </div>

              <div className="flex gap-3 pt-2">
                <Button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    setEditingConfig(null);
                    setFormData({
                      provider: 'google',
                      enabled: true,
                      client_id: '',
                      client_secret: '',
                      metadata_url: '',
                    });
                  }}
                  className="flex-1 bg-dark-800 hover:bg-dark-700"
                >
                  Cancel
                </Button>
                <Button type="submit" className="flex-1" isLoading={isSaving}>
                  {editingConfig ? 'Update' : 'Create'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
