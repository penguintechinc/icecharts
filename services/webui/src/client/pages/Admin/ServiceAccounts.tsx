import { useState, useEffect } from 'react';
import api from '../../lib/api';
import Button from '../../components/Button';
import Card from '../../components/Card';
import type {
  ServiceAccount,
  ServiceAccountToken,
  CreateServiceAccountData,
  UpdateServiceAccountData,
  CreateTokenData,
  GeneratedToken,
} from '../../types';

export default function ServiceAccountsPage() {
  const [accounts, setAccounts] = useState<ServiceAccount[]>([]);
  const [availableScopes, setAvailableScopes] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showTokensModal, setShowTokensModal] = useState(false);
  const [showGenerateTokenModal, setShowGenerateTokenModal] = useState(false);
  const [showTokenDisplay, setShowTokenDisplay] = useState(false);
  const [editingAccount, setEditingAccount] = useState<ServiceAccount | null>(null);
  const [selectedAccount, setSelectedAccount] = useState<ServiceAccount | null>(null);
  const [accountTokens, setAccountTokens] = useState<ServiceAccountToken[]>([]);
  const [generatedToken, setGeneratedToken] = useState<GeneratedToken | null>(null);
  const [formData, setFormData] = useState<CreateServiceAccountData>({
    name: '',
    description: '',
    scopes: [],
  });
  const [tokenFormData, setTokenFormData] = useState<CreateTokenData>({
    name: '',
    scopes: [],
    expires_in_days: 365,
  });
  const [isSaving, setIsSaving] = useState(false);
  const [isLoadingTokens, setIsLoadingTokens] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchAccounts();
    fetchAvailableScopes();
  }, []);

  const fetchAccounts = async () => {
    setIsLoading(true);
    try {
      const response = await api.get<{ items: ServiceAccount[] }>('/admin/service-accounts');
      setAccounts(response.data.items || []);
    } catch (err) {
      console.error('Failed to fetch service accounts:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchAvailableScopes = async () => {
    try {
      const response = await api.get<{ scopes: string[] }>('/admin/service-accounts/scopes');
      setAvailableScopes(response.data.scopes || []);
    } catch (err) {
      console.error('Failed to fetch available scopes:', err);
    }
  };

  const fetchAccountTokens = async (accountId: number) => {
    setIsLoadingTokens(true);
    try {
      const response = await api.get<{ items: ServiceAccountToken[] }>(
        `/admin/service-accounts/${accountId}/tokens`
      );
      setAccountTokens(response.data.items || []);
    } catch (err) {
      console.error('Failed to fetch tokens:', err);
    } finally {
      setIsLoadingTokens(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setError('');

    try {
      await api.post('/admin/service-accounts', formData);
      setShowCreateModal(false);
      resetForm();
      fetchAccounts();
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to create service account');
    } finally {
      setIsSaving(false);
    }
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingAccount) return;

    setIsSaving(true);
    setError('');

    try {
      const updateData: UpdateServiceAccountData = {
        name: formData.name,
        description: formData.description || undefined,
        scopes: formData.scopes,
      };
      await api.put(`/admin/service-accounts/${editingAccount.id}`, updateData);
      setShowEditModal(false);
      setEditingAccount(null);
      resetForm();
      fetchAccounts();
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to update service account');
    } finally {
      setIsSaving(false);
    }
  };

  const handleToggleActive = async (accountId: number, isActive: boolean) => {
    try {
      await api.put(`/admin/service-accounts/${accountId}`, { is_active: !isActive });
      fetchAccounts();
    } catch (err) {
      console.error('Failed to toggle service account:', err);
    }
  };

  const handleDelete = async (accountId: number) => {
    if (!confirm('Delete this service account? All associated tokens will be revoked.')) return;

    try {
      await api.delete(`/admin/service-accounts/${accountId}`);
      fetchAccounts();
    } catch (err) {
      console.error('Failed to delete service account:', err);
    }
  };

  const handleEdit = (account: ServiceAccount) => {
    setEditingAccount(account);
    setFormData({
      name: account.name,
      description: account.description || '',
      scopes: account.scopes,
    });
    setShowEditModal(true);
  };

  const handleShowTokens = (account: ServiceAccount) => {
    setSelectedAccount(account);
    setShowTokensModal(true);
    fetchAccountTokens(account.id);
  };

  const handleGenerateToken = (account: ServiceAccount) => {
    setSelectedAccount(account);
    setTokenFormData({
      name: '',
      scopes: account.scopes,
      expires_in_days: 365,
    });
    setShowGenerateTokenModal(true);
  };

  const handleCreateToken = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAccount) return;

    setIsSaving(true);
    setError('');

    try {
      const response = await api.post<GeneratedToken>(
        `/admin/service-accounts/${selectedAccount.id}/tokens`,
        tokenFormData
      );
      setGeneratedToken(response.data);
      setShowGenerateTokenModal(false);
      setShowTokenDisplay(true);
      // Refresh tokens list if modal is open
      if (showTokensModal) {
        fetchAccountTokens(selectedAccount.id);
      }
      fetchAccounts(); // Refresh to update last_used_at
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to generate token');
    } finally {
      setIsSaving(false);
    }
  };

  const handleRevokeToken = async (accountId: number, jti: string) => {
    if (!confirm('Revoke this token? This action cannot be undone.')) return;

    try {
      await api.delete(`/admin/service-accounts/${accountId}/tokens/${jti}`);
      fetchAccountTokens(accountId);
      fetchAccounts(); // Refresh accounts list
    } catch (err) {
      console.error('Failed to revoke token:', err);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      scopes: [],
    });
    setError('');
  };

  const toggleScope = (scope: string, currentScopes: string[]) => {
    if (currentScopes.includes(scope)) {
      return currentScopes.filter((s) => s !== scope);
    } else {
      return [...currentScopes, scope];
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    // You could add a toast notification here
  };

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gold-400">Service Accounts</h1>
          <p className="text-dark-400 mt-1">
            Manage service accounts and API tokens for programmatic access
          </p>
        </div>
        <Button onClick={() => setShowCreateModal(true)}>Create Service Account</Button>
      </div>

      {/* Service Accounts List */}
      {isLoading ? (
        <div className="grid grid-cols-1 gap-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="card animate-pulse">
              <div className="h-6 bg-dark-700 rounded w-1/3 mb-3"></div>
              <div className="h-4 bg-dark-700 rounded w-full mb-2"></div>
              <div className="h-4 bg-dark-700 rounded w-2/3"></div>
            </div>
          ))}
        </div>
      ) : accounts.length > 0 ? (
        <div className="grid grid-cols-1 gap-4">
          {accounts.map((account) => (
            <Card key={account.id}>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-medium text-gold-400">{account.name}</h3>
                    <span
                      className={`text-xs px-2 py-1 rounded ${
                        account.is_active
                          ? 'bg-green-900/30 text-green-400'
                          : 'bg-red-900/30 text-red-400'
                      }`}
                    >
                      {account.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>

                  {account.description && (
                    <p className="text-dark-300 text-sm mb-3">{account.description}</p>
                  )}

                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2">
                      <span className="text-dark-400 w-32">Scopes:</span>
                      <div className="flex flex-wrap gap-1">
                        {account.scopes.map((scope) => (
                          <span
                            key={scope}
                            className="px-2 py-0.5 text-xs rounded bg-dark-700 text-dark-300"
                          >
                            {scope}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-dark-400 w-32">Created by:</span>
                      <span className="text-gold-400">{account.created_by_name}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-dark-400 w-32">Last used:</span>
                      <span className="text-dark-300">
                        {account.last_used_at
                          ? new Date(account.last_used_at).toLocaleString()
                          : 'Never'}
                      </span>
                    </div>
                    <div className="text-dark-500 text-xs">
                      Created {new Date(account.created_at).toLocaleDateString()}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleShowTokens(account)}
                    className="px-3 py-1.5 text-sm text-blue-400 hover:text-blue-300"
                  >
                    Tokens
                  </button>
                  <button
                    onClick={() => handleGenerateToken(account)}
                    className="px-3 py-1.5 text-sm text-green-400 hover:text-green-300"
                  >
                    Generate Token
                  </button>
                  <button
                    onClick={() => handleEdit(account)}
                    className="px-3 py-1.5 text-sm text-gold-400 hover:text-gold-300"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleToggleActive(account.id, account.is_active)}
                    className={`px-3 py-1.5 text-sm ${
                      account.is_active
                        ? 'text-yellow-400 hover:text-yellow-300'
                        : 'text-green-400 hover:text-green-300'
                    }`}
                  >
                    {account.is_active ? 'Disable' : 'Enable'}
                  </button>
                  <button
                    onClick={() => handleDelete(account.id)}
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
          <p className="text-dark-400 mb-4">No service accounts configured</p>
          <p className="text-dark-500 text-sm mb-6">
            Create service accounts to enable programmatic API access for automation and integrations.
          </p>
          <Button onClick={() => setShowCreateModal(true)}>Create Your First Service Account</Button>
        </div>
      )}

      {/* Create Service Account Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="card max-w-lg w-full max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold text-gold-400 mb-4">Create Service Account</h2>

            <form onSubmit={handleCreate} className="space-y-4">
              {error && (
                <div className="p-3 bg-red-900/20 border border-red-500/30 rounded text-red-400 text-sm">
                  {error}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gold-400 mb-2">Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="input w-full"
                  placeholder="e.g., CI/CD Pipeline, Monitoring Bot"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gold-400 mb-2">
                  Description (optional)
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="input w-full"
                  rows={3}
                  placeholder="Describe the purpose of this service account..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gold-400 mb-2">
                  Scopes (select at least one)
                </label>
                <div className="space-y-2 max-h-48 overflow-y-auto border border-dark-700 rounded p-3">
                  {availableScopes.map((scope) => (
                    <label key={scope} className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={formData.scopes.includes(scope)}
                        onChange={() =>
                          setFormData({
                            ...formData,
                            scopes: toggleScope(scope, formData.scopes),
                          })
                        }
                        className="w-4 h-4"
                      />
                      <span className="text-dark-300 text-sm font-mono">{scope}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="flex gap-3 pt-2">
                <Button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    resetForm();
                  }}
                  className="flex-1 bg-dark-800 hover:bg-dark-700"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  className="flex-1"
                  isLoading={isSaving}
                  disabled={formData.scopes.length === 0}
                >
                  Create
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Service Account Modal */}
      {showEditModal && editingAccount && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="card max-w-lg w-full max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold text-gold-400 mb-4">Edit Service Account</h2>

            <form onSubmit={handleUpdate} className="space-y-4">
              {error && (
                <div className="p-3 bg-red-900/20 border border-red-500/30 rounded text-red-400 text-sm">
                  {error}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gold-400 mb-2">Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="input w-full"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gold-400 mb-2">
                  Description (optional)
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="input w-full"
                  rows={3}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gold-400 mb-2">Scopes</label>
                <div className="space-y-2 max-h-48 overflow-y-auto border border-dark-700 rounded p-3">
                  {availableScopes.map((scope) => (
                    <label key={scope} className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={formData.scopes.includes(scope)}
                        onChange={() =>
                          setFormData({
                            ...formData,
                            scopes: toggleScope(scope, formData.scopes),
                          })
                        }
                        className="w-4 h-4"
                      />
                      <span className="text-dark-300 text-sm font-mono">{scope}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="flex gap-3 pt-2">
                <Button
                  type="button"
                  onClick={() => {
                    setShowEditModal(false);
                    setEditingAccount(null);
                    resetForm();
                  }}
                  className="flex-1 bg-dark-800 hover:bg-dark-700"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  className="flex-1"
                  isLoading={isSaving}
                  disabled={formData.scopes.length === 0}
                >
                  Update
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Tokens Modal */}
      {showTokensModal && selectedAccount && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="card max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gold-400">
                Tokens for {selectedAccount.name}
              </h2>
              <button
                onClick={() => {
                  setShowTokensModal(false);
                  setSelectedAccount(null);
                }}
                className="text-dark-400 hover:text-gold-400"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {isLoadingTokens ? (
              <div className="space-y-3">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="h-16 bg-dark-700 rounded animate-pulse"></div>
                ))}
              </div>
            ) : accountTokens.length > 0 ? (
              <div className="space-y-3">
                {accountTokens.map((token) => (
                  <div key={token.jti} className="border border-dark-700 rounded p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-medium text-gold-400">{token.name}</h4>
                          {token.expires_at && new Date(token.expires_at) < new Date() && (
                            <span className="px-2 py-0.5 text-xs rounded bg-red-900/30 text-red-400">
                              Expired
                            </span>
                          )}
                        </div>
                        <div className="text-xs text-dark-500 space-y-1">
                          <div>JTI: {token.jti}</div>
                          <div>
                            Created: {new Date(token.created_at).toLocaleDateString()}
                          </div>
                          <div>
                            Expires:{' '}
                            {token.expires_at
                              ? new Date(token.expires_at).toLocaleDateString()
                              : 'Never'}
                          </div>
                          <div>
                            Last used:{' '}
                            {token.last_used_at
                              ? new Date(token.last_used_at).toLocaleString()
                              : 'Never'}
                          </div>
                        </div>
                      </div>
                      <button
                        onClick={() => handleRevokeToken(selectedAccount.id, token.jti)}
                        className="px-3 py-1.5 text-sm text-red-400 hover:text-red-300"
                      >
                        Revoke
                      </button>
                    </div>
                    <div className="flex flex-wrap gap-1 mt-2">
                      {token.scopes.map((scope) => (
                        <span
                          key={scope}
                          className="px-2 py-0.5 text-xs rounded bg-dark-700 text-dark-300"
                        >
                          {scope}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-dark-400">
                No tokens generated for this service account
              </div>
            )}

            <div className="mt-6 pt-4 border-t border-dark-700">
              <Button onClick={() => handleGenerateToken(selectedAccount)} className="w-full">
                Generate New Token
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Generate Token Modal */}
      {showGenerateTokenModal && selectedAccount && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="card max-w-lg w-full">
            <h2 className="text-xl font-bold text-gold-400 mb-4">
              Generate Token for {selectedAccount.name}
            </h2>

            <form onSubmit={handleCreateToken} className="space-y-4">
              {error && (
                <div className="p-3 bg-red-900/20 border border-red-500/30 rounded text-red-400 text-sm">
                  {error}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gold-400 mb-2">Token Name</label>
                <input
                  type="text"
                  value={tokenFormData.name}
                  onChange={(e) => setTokenFormData({ ...tokenFormData, name: e.target.value })}
                  className="input w-full"
                  placeholder="e.g., Production Server, Dev Environment"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gold-400 mb-2">
                  Expiration (days)
                </label>
                <input
                  type="number"
                  value={tokenFormData.expires_in_days || ''}
                  onChange={(e) =>
                    setTokenFormData({
                      ...tokenFormData,
                      expires_in_days: e.target.value ? parseInt(e.target.value) : undefined,
                    })
                  }
                  className="input w-full"
                  min="1"
                  max="3650"
                  placeholder="365 (leave empty for no expiration)"
                />
                <p className="text-xs text-dark-500 mt-1">
                  Leave empty for tokens that never expire
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gold-400 mb-2">
                  Scopes (inherits from service account)
                </label>
                <div className="space-y-2 max-h-48 overflow-y-auto border border-dark-700 rounded p-3">
                  {selectedAccount.scopes.map((scope) => (
                    <label key={scope} className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={
                          tokenFormData.scopes?.includes(scope) ?? selectedAccount.scopes.includes(scope)
                        }
                        onChange={() =>
                          setTokenFormData({
                            ...tokenFormData,
                            scopes: toggleScope(
                              scope,
                              tokenFormData.scopes || selectedAccount.scopes
                            ),
                          })
                        }
                        className="w-4 h-4"
                      />
                      <span className="text-dark-300 text-sm font-mono">{scope}</span>
                    </label>
                  ))}
                </div>
                <p className="text-xs text-dark-500 mt-1">
                  You can limit scopes, but cannot grant scopes beyond those assigned to the service account
                </p>
              </div>

              <div className="flex gap-3 pt-2">
                <Button
                  type="button"
                  onClick={() => {
                    setShowGenerateTokenModal(false);
                    setSelectedAccount(null);
                    setError('');
                  }}
                  className="flex-1 bg-dark-800 hover:bg-dark-700"
                >
                  Cancel
                </Button>
                <Button type="submit" className="flex-1" isLoading={isSaving}>
                  Generate Token
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Token Display Modal */}
      {showTokenDisplay && generatedToken && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="card max-w-2xl w-full">
            <h2 className="text-xl font-bold text-gold-400 mb-4">Token Generated Successfully</h2>

            <div className="bg-yellow-900/20 border border-yellow-500/30 rounded p-4 mb-4">
              <p className="text-yellow-400 text-sm font-medium mb-2">
                Important: Copy this token now!
              </p>
              <p className="text-yellow-300 text-sm">
                For security reasons, this token will only be shown once. Make sure to copy it to a
                secure location.
              </p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gold-400 mb-2">Token</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={generatedToken.token}
                    readOnly
                    className="input w-full font-mono text-sm"
                  />
                  <Button onClick={() => copyToClipboard(generatedToken.token)} size="sm">
                    Copy
                  </Button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gold-400 mb-2">Token Name</label>
                <p className="text-dark-300">{generatedToken.name}</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gold-400 mb-2">Token ID (JTI)</label>
                <p className="text-dark-300 font-mono text-sm">{generatedToken.jti}</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gold-400 mb-2">Scopes</label>
                <div className="flex flex-wrap gap-1">
                  {generatedToken.scopes.map((scope) => (
                    <span
                      key={scope}
                      className="px-2 py-1 text-xs rounded bg-dark-700 text-dark-300"
                    >
                      {scope}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gold-400 mb-2">Expires</label>
                <p className="text-dark-300">
                  {generatedToken.expires_at
                    ? new Date(generatedToken.expires_at).toLocaleString()
                    : 'Never'}
                </p>
              </div>
            </div>

            <div className="mt-6">
              <Button
                onClick={() => {
                  setShowTokenDisplay(false);
                  setGeneratedToken(null);
                  setSelectedAccount(null);
                }}
                className="w-full"
              >
                Close
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
