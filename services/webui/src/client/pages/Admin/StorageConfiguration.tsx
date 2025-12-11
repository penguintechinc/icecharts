import { useState, useEffect } from 'react';
import api from '../../lib/api';
import Button from '../../components/Button';
import Card from '../../components/Card';

export interface StorageProviderConfig {
  id: number;
  provider: 'gdrive' | 'onedrive' | 's3';
  name: string;
  enabled: boolean;
  client_id: string;
  client_secret?: string;
  tenant_id?: string; // For OneDrive
  bucket?: string; // For S3
  region?: string; // For S3
  endpoint?: string; // For custom S3 endpoints
  created_at: string;
  updated_at: string;
}

const providerInfo = {
  gdrive: {
    name: 'Google Drive',
    description: 'Allow users to save/load drawings from Google Drive',
    fields: ['client_id', 'client_secret'],
    icon: 'M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5',
  },
  onedrive: {
    name: 'OneDrive',
    description: 'Allow users to save/load drawings from Microsoft OneDrive',
    fields: ['client_id', 'client_secret', 'tenant_id'],
    icon: 'M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z',
  },
  s3: {
    name: 'External S3',
    description: 'Allow users to connect to AWS S3 or S3-compatible storage',
    fields: ['bucket', 'region', 'endpoint'],
    icon: 'M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01',
  },
};

type ProviderType = keyof typeof providerInfo;

export default function StorageConfigurationPage() {
  const [configs, setConfigs] = useState<StorageProviderConfig[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingConfig, setEditingConfig] = useState<StorageProviderConfig | null>(null);
  const [formData, setFormData] = useState({
    provider: 'gdrive' as ProviderType,
    name: '',
    enabled: true,
    client_id: '',
    client_secret: '',
    tenant_id: '',
    bucket: '',
    region: 'us-east-1',
    endpoint: '',
  });
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchConfigs();
  }, []);

  const fetchConfigs = async () => {
    setIsLoading(true);
    try {
      const response = await api.get<{ items: StorageProviderConfig[] }>('/admin/storage');
      setConfigs(response.data.items || []);
    } catch (err) {
      console.error('Failed to fetch storage configs:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setError('');

    try {
      const payload = {
        provider: formData.provider,
        name: formData.name || providerInfo[formData.provider].name,
        enabled: formData.enabled,
        ...(formData.provider === 'gdrive' && {
          client_id: formData.client_id,
          client_secret: formData.client_secret || undefined,
        }),
        ...(formData.provider === 'onedrive' && {
          client_id: formData.client_id,
          client_secret: formData.client_secret || undefined,
          tenant_id: formData.tenant_id,
        }),
        ...(formData.provider === 's3' && {
          bucket: formData.bucket,
          region: formData.region,
          endpoint: formData.endpoint || undefined,
        }),
      };

      if (editingConfig) {
        await api.put(`/admin/storage/${editingConfig.id}`, payload);
      } else {
        await api.post('/admin/storage', payload);
      }

      setShowCreateModal(false);
      setEditingConfig(null);
      resetForm();
      fetchConfigs();
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to save storage config');
    } finally {
      setIsSaving(false);
    }
  };

  const resetForm = () => {
    setFormData({
      provider: 'gdrive',
      name: '',
      enabled: true,
      client_id: '',
      client_secret: '',
      tenant_id: '',
      bucket: '',
      region: 'us-east-1',
      endpoint: '',
    });
  };

  const handleEdit = (config: StorageProviderConfig) => {
    setEditingConfig(config);
    setFormData({
      provider: config.provider,
      name: config.name,
      enabled: config.enabled,
      client_id: config.client_id || '',
      client_secret: '',
      tenant_id: config.tenant_id || '',
      bucket: config.bucket || '',
      region: config.region || 'us-east-1',
      endpoint: config.endpoint || '',
    });
    setShowCreateModal(true);
  };

  const handleToggleEnabled = async (configId: number, enabled: boolean) => {
    try {
      await api.patch(`/admin/storage/${configId}`, { enabled: !enabled });
      fetchConfigs();
    } catch (err) {
      console.error('Failed to toggle storage config:', err);
    }
  };

  const handleDelete = async (configId: number) => {
    if (!confirm('Delete this storage configuration? Users will no longer be able to use this provider.')) return;

    try {
      await api.delete(`/admin/storage/${configId}`);
      fetchConfigs();
    } catch (err) {
      console.error('Failed to delete storage config:', err);
    }
  };

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-ice-gold-400">Storage Providers</h1>
          <p className="text-ice-navy-400 mt-1">
            Configure external storage providers for user drawings
          </p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>
          Add Storage Provider
        </Button>
      </div>

      {/* Default MinIO Info */}
      <Card className="mb-6 border-ice-gold-500/30 bg-ice-gold-500/5">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-lg bg-ice-gold-500/20 flex items-center justify-center">
            <svg className="w-6 h-6 text-ice-gold-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
            </svg>
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h3 className="font-medium text-ice-gold-400">IceCharts Cloud Storage</h3>
              <span className="px-2 py-0.5 text-xs rounded-full bg-green-500/20 text-green-400">
                Active
              </span>
              <span className="px-2 py-0.5 text-xs rounded-full bg-ice-gold-500/20 text-ice-gold-400">
                Default
              </span>
            </div>
            <p className="text-sm text-ice-navy-400">
              Built-in S3-compatible storage (MinIO). This is always enabled and serves as the default storage for all users.
            </p>
          </div>
        </div>
      </Card>

      {/* External Storage Configurations */}
      <h2 className="text-lg font-semibold text-ice-gold-400 mb-4">External Storage Providers</h2>

      {isLoading ? (
        <div className="grid grid-cols-1 gap-4">
          {[...Array(2)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <div className="h-6 bg-ice-navy-700 rounded w-1/3 mb-3"></div>
              <div className="h-4 bg-ice-navy-700 rounded w-full mb-2"></div>
              <div className="h-4 bg-ice-navy-700 rounded w-2/3"></div>
            </Card>
          ))}
        </div>
      ) : configs.length > 0 ? (
        <div className="grid grid-cols-1 gap-4">
          {configs.map((config) => {
            const info = providerInfo[config.provider];
            return (
              <Card key={config.id}>
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 rounded-lg bg-ice-navy-700 flex items-center justify-center">
                      <svg className="w-6 h-6 text-ice-navy-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={info.icon} />
                      </svg>
                    </div>
                    <div>
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-lg font-medium text-ice-gold-400">
                          {config.name}
                        </h3>
                        <span className="text-xs px-2 py-0.5 rounded-full bg-ice-navy-700 text-ice-navy-300">
                          {info.name}
                        </span>
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

                      <div className="space-y-1 text-sm">
                        {config.client_id && (
                          <div className="flex items-center gap-2">
                            <span className="text-ice-navy-500 w-24">Client ID:</span>
                            <span className="text-ice-navy-300 font-mono text-xs">
                              {config.client_id.slice(0, 20)}...
                            </span>
                          </div>
                        )}
                        {config.bucket && (
                          <div className="flex items-center gap-2">
                            <span className="text-ice-navy-500 w-24">Bucket:</span>
                            <span className="text-ice-navy-300 font-mono text-xs">
                              {config.bucket}
                            </span>
                          </div>
                        )}
                        {config.region && (
                          <div className="flex items-center gap-2">
                            <span className="text-ice-navy-500 w-24">Region:</span>
                            <span className="text-ice-navy-300 font-mono text-xs">
                              {config.region}
                            </span>
                          </div>
                        )}
                        <div className="text-ice-navy-600 text-xs pt-1">
                          Updated {new Date(config.updated_at).toLocaleDateString()}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleEdit(config)}
                      className="px-3 py-1.5 text-sm text-ice-gold-400 hover:text-ice-gold-300"
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
            );
          })}
        </div>
      ) : (
        <Card className="text-center py-12">
          <p className="text-ice-navy-400 mb-4">No external storage providers configured</p>
          <p className="text-ice-navy-500 text-sm mb-6">
            Users can only save to IceCharts Cloud. Add Google Drive or OneDrive to let users save to their personal accounts.
          </p>
          <Button onClick={() => setShowCreateModal(true)}>
            Add External Storage Provider
          </Button>
        </Card>
      )}

      {/* Create/Edit Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-ice-navy-800 border border-ice-navy-700 rounded-lg max-w-lg w-full max-h-[90vh] overflow-y-auto">
            <div className="px-6 py-4 border-b border-ice-navy-700">
              <h2 className="text-xl font-bold text-ice-gold-400">
                {editingConfig ? 'Edit Storage Provider' : 'Add Storage Provider'}
              </h2>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              {error && (
                <div className="p-3 bg-red-900/20 border border-red-500/30 rounded-lg text-red-400 text-sm">
                  {error}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-ice-gold-400 mb-2">
                  Provider Type
                </label>
                <select
                  value={formData.provider}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      provider: e.target.value as ProviderType,
                      name: providerInfo[e.target.value as ProviderType].name,
                    })
                  }
                  className="w-full px-4 py-2 bg-ice-navy-700 border border-ice-navy-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-ice-gold-400"
                  disabled={!!editingConfig}
                >
                  <option value="gdrive">Google Drive</option>
                  <option value="onedrive">OneDrive</option>
                  <option value="s3">External S3</option>
                </select>
                <p className="mt-1 text-xs text-ice-navy-500">
                  {providerInfo[formData.provider].description}
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-ice-gold-400 mb-2">
                  Display Name
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                  className="w-full px-4 py-2 bg-ice-navy-700 border border-ice-navy-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-ice-gold-400"
                  placeholder={providerInfo[formData.provider].name}
                />
              </div>

              {/* Google Drive / OneDrive fields */}
              {(formData.provider === 'gdrive' || formData.provider === 'onedrive') && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-ice-gold-400 mb-2">
                      Client ID
                    </label>
                    <input
                      type="text"
                      value={formData.client_id}
                      onChange={(e) =>
                        setFormData({ ...formData, client_id: e.target.value })
                      }
                      className="w-full px-4 py-2 bg-ice-navy-700 border border-ice-navy-600 rounded-lg text-white font-mono text-sm focus:outline-none focus:ring-2 focus:ring-ice-gold-400"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-ice-gold-400 mb-2">
                      Client Secret
                    </label>
                    <input
                      type="password"
                      value={formData.client_secret}
                      onChange={(e) =>
                        setFormData({ ...formData, client_secret: e.target.value })
                      }
                      className="w-full px-4 py-2 bg-ice-navy-700 border border-ice-navy-600 rounded-lg text-white font-mono text-sm focus:outline-none focus:ring-2 focus:ring-ice-gold-400"
                      required={!editingConfig}
                      placeholder={editingConfig ? '(unchanged)' : ''}
                    />
                  </div>
                </>
              )}

              {/* OneDrive tenant ID */}
              {formData.provider === 'onedrive' && (
                <div>
                  <label className="block text-sm font-medium text-ice-gold-400 mb-2">
                    Tenant ID
                  </label>
                  <input
                    type="text"
                    value={formData.tenant_id}
                    onChange={(e) =>
                      setFormData({ ...formData, tenant_id: e.target.value })
                    }
                    className="w-full px-4 py-2 bg-ice-navy-700 border border-ice-navy-600 rounded-lg text-white font-mono text-sm focus:outline-none focus:ring-2 focus:ring-ice-gold-400"
                    placeholder="common (for multi-tenant)"
                  />
                  <p className="mt-1 text-xs text-ice-navy-500">
                    Use "common" for multi-tenant, or your specific tenant ID
                  </p>
                </div>
              )}

              {/* S3 fields */}
              {formData.provider === 's3' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-ice-gold-400 mb-2">
                      Bucket Name
                    </label>
                    <input
                      type="text"
                      value={formData.bucket}
                      onChange={(e) =>
                        setFormData({ ...formData, bucket: e.target.value })
                      }
                      className="w-full px-4 py-2 bg-ice-navy-700 border border-ice-navy-600 rounded-lg text-white font-mono text-sm focus:outline-none focus:ring-2 focus:ring-ice-gold-400"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-ice-gold-400 mb-2">
                      Region
                    </label>
                    <input
                      type="text"
                      value={formData.region}
                      onChange={(e) =>
                        setFormData({ ...formData, region: e.target.value })
                      }
                      className="w-full px-4 py-2 bg-ice-navy-700 border border-ice-navy-600 rounded-lg text-white font-mono text-sm focus:outline-none focus:ring-2 focus:ring-ice-gold-400"
                      placeholder="us-east-1"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-ice-gold-400 mb-2">
                      Custom Endpoint (optional)
                    </label>
                    <input
                      type="text"
                      value={formData.endpoint}
                      onChange={(e) =>
                        setFormData({ ...formData, endpoint: e.target.value })
                      }
                      className="w-full px-4 py-2 bg-ice-navy-700 border border-ice-navy-600 rounded-lg text-white font-mono text-sm focus:outline-none focus:ring-2 focus:ring-ice-gold-400"
                      placeholder="https://s3.example.com"
                    />
                    <p className="mt-1 text-xs text-ice-navy-500">
                      Leave empty for AWS S3, or enter URL for S3-compatible services
                    </p>
                  </div>
                </>
              )}

              <div>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.enabled}
                    onChange={(e) =>
                      setFormData({ ...formData, enabled: e.target.checked })
                    }
                    className="w-5 h-5 rounded border-ice-navy-600 bg-ice-navy-700 text-ice-gold-500 focus:ring-ice-gold-400"
                  />
                  <span className="text-ice-gold-400">Enable this provider for users</span>
                </label>
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    setEditingConfig(null);
                    resetForm();
                    setError('');
                  }}
                  className="flex-1 px-4 py-2 bg-ice-navy-700 hover:bg-ice-navy-600 text-white rounded-lg transition-colors"
                >
                  Cancel
                </button>
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
