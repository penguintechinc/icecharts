import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import Button from '../components/Button';
import TabNavigation from '../components/TabNavigation';

interface SAMLConfig {
  idp_name: string;
  idp_entity_id: string;
  sso_url: string;
  slo_url?: string;
  name_id_format?: string;
  metadata_url?: string;
}

interface OIDCConfig {
  issuer: string;
  client_id: string;
  authorization_endpoint: string;
  token_endpoint: string;
  userinfo_endpoint: string;
}

interface SAMLFormData {
  metadata_url?: string;
  idp_name?: string;
  idp_entity_id?: string;
  sso_url?: string;
  slo_url?: string;
  x509_cert?: string;
  jit_enabled: boolean;
  auto_assign_role: string;
}

interface OIDCFormData {
  issuer: string;
  client_id: string;
  client_secret: string;
  jit_enabled: boolean;
  auto_assign_role: string;
}

export default function SSOConfiguration() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'saml' | 'oidc'>('saml');

  // SAML state
  const [samlConfig, setSAMLConfig] = useState<SAMLConfig | null>(null);
  const [samlFormData, setSAMLFormData] = useState<SAMLFormData>({
    jit_enabled: true,
    auto_assign_role: 'viewer',
  });
  const [samlLoading, setSAMLLoading] = useState(false);
  const [samlError, setSAMLError] = useState<string | null>(null);
  const [samlSuccess, setSAMLSuccess] = useState(false);

  // OIDC state
  const [oidcConfig, setOIDCConfig] = useState<OIDCConfig | null>(null);
  const [oidcFormData, setOIDCFormData] = useState<OIDCFormData>({
    issuer: '',
    client_id: '',
    client_secret: '',
    jit_enabled: true,
    auto_assign_role: 'viewer',
  });
  const [oidcLoading, setOIDCLoading] = useState(false);
  const [oidcError, setOIDCError] = useState<string | null>(null);
  const [oidcSuccess, setOIDCSuccess] = useState(false);

  // Check authorization
  if (user?.role !== 'admin') {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="p-4 bg-red-900/30 border border-red-700 rounded-lg text-red-400">
          Admin access required to configure SSO.
        </div>
      </div>
    );
  }

  useEffect(() => {
    if (activeTab === 'saml') {
      fetchSAMLConfig();
    } else {
      fetchOIDCConfig();
    }
  }, [activeTab]);

  // SAML Functions
  const fetchSAMLConfig = async () => {
    try {
      setSAMLLoading(true);
      const response = await fetch('/api/v1/sso/saml/config', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('accessToken')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch SAML configuration');
      }

      const data = await response.json();
      setSAMLConfig(data.config);
      setSAMLError(null);
    } catch (err) {
      setSAMLError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setSAMLLoading(false);
    }
  };

  const handleSAMLSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSAMLLoading(true);
    setSAMLError(null);
    setSAMLSuccess(false);

    try {
      const response = await fetch('/api/v1/sso/saml/config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('accessToken')}`,
        },
        body: JSON.stringify(samlFormData),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to save SAML configuration');
      }

      const data = await response.json();
      setSAMLConfig(data.config);
      setSAMLSuccess(true);
      setTimeout(() => setSAMLSuccess(false), 3000);
    } catch (err) {
      setSAMLError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setSAMLLoading(false);
    }
  };

  // OIDC Functions
  const fetchOIDCConfig = async () => {
    try {
      setOIDCLoading(true);
      const response = await fetch('/api/v1/sso/oidc/config', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('accessToken')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch OIDC configuration');
      }

      const data = await response.json();
      setOIDCConfig(data.config);
      setOIDCError(null);
    } catch (err) {
      setOIDCError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setOIDCLoading(false);
    }
  };

  const handleOIDCSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setOIDCLoading(true);
    setOIDCError(null);
    setOIDCSuccess(false);

    try {
      const response = await fetch('/api/v1/sso/oidc/config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('accessToken')}`,
        },
        body: JSON.stringify(oidcFormData),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to save OIDC configuration');
      }

      const data = await response.json();
      setOIDCConfig(data.config);
      setOIDCSuccess(true);
      setTimeout(() => setOIDCSuccess(false), 3000);
    } catch (err) {
      setOIDCError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setOIDCLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gold-gradient mb-2">
          SSO Configuration
        </h1>
        <p className="text-ice-navy-400">
          Configure enterprise SAML 2.0 and OpenID Connect authentication
        </p>
      </div>

      <TabNavigation
        tabs={[
          { id: 'saml', label: 'SAML 2.0' },
          { id: 'oidc', label: 'OpenID Connect' },
        ]}
        activeTab={activeTab}
        onChange={(tab) => setActiveTab(tab as 'saml' | 'oidc')}
      />

      {/* SAML Configuration */}
      {activeTab === 'saml' && (
        <div className="card mt-6">
          {samlConfig && (
            <div className="mb-6 p-4 bg-green-900/20 border border-green-700 rounded-lg">
              <h3 className="font-semibold text-green-400 mb-2">
                SAML is configured
              </h3>
              <p className="text-sm text-green-300">
                IdP: {samlConfig.idp_name}
              </p>
            </div>
          )}

          {samlSuccess && (
            <div className="mb-6 p-4 bg-blue-900/20 border border-blue-700 rounded-lg text-blue-400">
              SAML configuration saved successfully
            </div>
          )}

          {samlError && (
            <div className="mb-6 p-4 bg-red-900/20 border border-red-700 rounded-lg text-red-400">
              {samlError}
            </div>
          )}

          <form onSubmit={handleSAMLSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-ice-gold-400 mb-2">
                Metadata URL
              </label>
              <input
                type="url"
                placeholder="https://idp.example.com/metadata"
                value={samlFormData.metadata_url || ''}
                onChange={(e) =>
                  setSAMLFormData({
                    ...samlFormData,
                    metadata_url: e.target.value,
                  })
                }
                className="input"
              />
              <p className="text-xs text-ice-navy-500 mt-1">
                Provide metadata URL for automatic configuration, or fill in manual fields below
              </p>
            </div>

            <div className="border-t border-ice-navy-700 pt-6">
              <p className="text-sm text-ice-navy-400 mb-4">Manual Configuration</p>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-ice-gold-400 mb-2">
                    IdP Name
                  </label>
                  <input
                    type="text"
                    placeholder="e.g., Okta, AzureAD"
                    value={samlFormData.idp_name || ''}
                    onChange={(e) =>
                      setSAMLFormData({
                        ...samlFormData,
                        idp_name: e.target.value,
                      })
                    }
                    className="input"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-ice-gold-400 mb-2">
                    Entity ID
                  </label>
                  <input
                    type="text"
                    placeholder="https://idp.example.com"
                    value={samlFormData.idp_entity_id || ''}
                    onChange={(e) =>
                      setSAMLFormData({
                        ...samlFormData,
                        idp_entity_id: e.target.value,
                      })
                    }
                    className="input"
                  />
                </div>
              </div>

              <div className="mt-4 grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-ice-gold-400 mb-2">
                    SSO URL
                  </label>
                  <input
                    type="url"
                    placeholder="https://idp.example.com/sso"
                    value={samlFormData.sso_url || ''}
                    onChange={(e) =>
                      setSAMLFormData({
                        ...samlFormData,
                        sso_url: e.target.value,
                      })
                    }
                    className="input"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-ice-gold-400 mb-2">
                    SLO URL (Optional)
                  </label>
                  <input
                    type="url"
                    placeholder="https://idp.example.com/slo"
                    value={samlFormData.slo_url || ''}
                    onChange={(e) =>
                      setSAMLFormData({
                        ...samlFormData,
                        slo_url: e.target.value,
                      })
                    }
                    className="input"
                  />
                </div>
              </div>

              <div className="mt-4">
                <label className="block text-sm font-medium text-ice-gold-400 mb-2">
                  X.509 Certificate
                </label>
                <textarea
                  placeholder="-----BEGIN CERTIFICATE-----
...
-----END CERTIFICATE-----"
                  value={samlFormData.x509_cert || ''}
                  onChange={(e) =>
                    setSAMLFormData({
                      ...samlFormData,
                      x509_cert: e.target.value,
                    })
                  }
                  rows={6}
                  className="input font-mono text-xs"
                />
              </div>
            </div>

            <div className="border-t border-ice-navy-700 pt-6">
              <p className="text-sm text-ice-navy-400 mb-4">
                Just-In-Time Provisioning
              </p>

              <label className="flex items-center mb-4">
                <input
                  type="checkbox"
                  checked={samlFormData.jit_enabled}
                  onChange={(e) =>
                    setSAMLFormData({
                      ...samlFormData,
                      jit_enabled: e.target.checked,
                    })
                  }
                  className="mr-3"
                />
                <span className="text-sm text-ice-gold-400">
                  Enable JIT user provisioning
                </span>
              </label>

              <div>
                <label className="block text-sm font-medium text-ice-gold-400 mb-2">
                  Default Role for New Users
                </label>
                <select
                  value={samlFormData.auto_assign_role}
                  onChange={(e) =>
                    setSAMLFormData({
                      ...samlFormData,
                      auto_assign_role: e.target.value,
                    })
                  }
                  className="input"
                >
                  <option value="viewer">Viewer (read-only)</option>
                  <option value="maintainer">Maintainer (read/write)</option>
                  <option value="admin">Admin (full access)</option>
                </select>
              </div>
            </div>

            <div className="flex gap-4">
              <Button type="submit" isLoading={samlLoading}>
                Save SAML Configuration
              </Button>
              {samlConfig && (
                <Button type="button" variant="secondary">
                  View SP Metadata
                </Button>
              )}
            </div>
          </form>
        </div>
      )}

      {/* OIDC Configuration */}
      {activeTab === 'oidc' && (
        <div className="card mt-6">
          {oidcConfig && (
            <div className="mb-6 p-4 bg-green-900/20 border border-green-700 rounded-lg">
              <h3 className="font-semibold text-green-400 mb-2">
                OIDC is configured
              </h3>
              <p className="text-sm text-green-300">
                Provider: {oidcConfig.issuer}
              </p>
            </div>
          )}

          {oidcSuccess && (
            <div className="mb-6 p-4 bg-blue-900/20 border border-blue-700 rounded-lg text-blue-400">
              OIDC configuration saved successfully
            </div>
          )}

          {oidcError && (
            <div className="mb-6 p-4 bg-red-900/20 border border-red-700 rounded-lg text-red-400">
              {oidcError}
            </div>
          )}

          <form onSubmit={handleOIDCSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-ice-gold-400 mb-2">
                Issuer URL
              </label>
              <input
                type="url"
                placeholder="https://accounts.google.com or https://your-oidc-provider.com"
                value={oidcFormData.issuer}
                onChange={(e) =>
                  setOIDCFormData({
                    ...oidcFormData,
                    issuer: e.target.value,
                  })
                }
                className="input"
                required
              />
              <p className="text-xs text-ice-navy-500 mt-1">
                The OIDC provider's issuer URL
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-ice-gold-400 mb-2">
                  Client ID
                </label>
                <input
                  type="text"
                  placeholder="your-client-id"
                  value={oidcFormData.client_id}
                  onChange={(e) =>
                    setOIDCFormData({
                      ...oidcFormData,
                      client_id: e.target.value,
                    })
                  }
                  className="input"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-ice-gold-400 mb-2">
                  Client Secret
                </label>
                <input
                  type="password"
                  placeholder="your-client-secret"
                  value={oidcFormData.client_secret}
                  onChange={(e) =>
                    setOIDCFormData({
                      ...oidcFormData,
                      client_secret: e.target.value,
                    })
                  }
                  className="input"
                  required
                />
              </div>
            </div>

            <div className="border-t border-ice-navy-700 pt-6">
              <p className="text-sm text-ice-navy-400 mb-4">
                Just-In-Time Provisioning
              </p>

              <label className="flex items-center mb-4">
                <input
                  type="checkbox"
                  checked={oidcFormData.jit_enabled}
                  onChange={(e) =>
                    setOIDCFormData({
                      ...oidcFormData,
                      jit_enabled: e.target.checked,
                    })
                  }
                  className="mr-3"
                />
                <span className="text-sm text-ice-gold-400">
                  Enable JIT user provisioning
                </span>
              </label>

              <div>
                <label className="block text-sm font-medium text-ice-gold-400 mb-2">
                  Default Role for New Users
                </label>
                <select
                  value={oidcFormData.auto_assign_role}
                  onChange={(e) =>
                    setOIDCFormData({
                      ...oidcFormData,
                      auto_assign_role: e.target.value,
                    })
                  }
                  className="input"
                >
                  <option value="viewer">Viewer (read-only)</option>
                  <option value="maintainer">Maintainer (read/write)</option>
                  <option value="admin">Admin (full access)</option>
                </select>
              </div>
            </div>

            <Button type="submit" isLoading={oidcLoading}>
              Save OIDC Configuration
            </Button>
          </form>
        </div>
      )}

      <div className="card mt-8 bg-ice-navy-900/50">
        <h3 className="font-semibold text-ice-gold-400 mb-3">
          Security & Compliance
        </h3>
        <ul className="space-y-2 text-sm text-ice-navy-400">
          <li className="flex items-start">
            <span className="text-green-400 mr-2">✓</span>
            <span>All SSO communications are encrypted with TLS 1.2+</span>
          </li>
          <li className="flex items-start">
            <span className="text-green-400 mr-2">✓</span>
            <span>SAML responses are cryptographically validated</span>
          </li>
          <li className="flex items-start">
            <span className="text-green-400 mr-2">✓</span>
            <span>OIDC uses PKCE for maximum security</span>
          </li>
          <li className="flex items-start">
            <span className="text-green-400 mr-2">✓</span>
            <span>JWT tokens include role-based access control</span>
          </li>
        </ul>
      </div>
    </div>
  );
}
