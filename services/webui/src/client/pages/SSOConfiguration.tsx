import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import Button from '../components/Button';
import apiClient from '../../lib/api';

interface SSOProvider {
  id: string;
  name: string;
  description: string;
  available: boolean;
  premium: boolean;
}

interface SSOConfig {
  id: number;
  provider: string;
  name: string;
  enabled: boolean;
  client_id: string;
  metadata_url: string;
}

interface GoogleFormData {
  client_id: string;
  client_secret: string;
  enabled: boolean;
}

interface SAMLFormData {
  name: string;
  metadata_url: string;
  entity_id: string;
  sso_url: string;
  slo_url: string;
  x509_cert: string;
  enabled: boolean;
}

interface OIDCFormData {
  name: string;
  issuer: string;
  client_id: string;
  client_secret: string;
  enabled: boolean;
}

export default function SSOConfiguration() {
  const { user } = useAuth();

  // Provider selection state
  const [providers, setProviders] = useState<SSOProvider[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>('google');
  const [hasPremium, setHasPremium] = useState(false);
  const [providersLoading, setProvidersLoading] = useState(true);

  // Existing configs
  const [existingConfigs, setExistingConfigs] = useState<SSOConfig[]>([]);

  // Form states
  const [googleForm, setGoogleForm] = useState<GoogleFormData>({
    client_id: '',
    client_secret: '',
    enabled: true,
  });

  const [samlForm, setSamlForm] = useState<SAMLFormData>({
    name: '',
    metadata_url: '',
    entity_id: '',
    sso_url: '',
    slo_url: '',
    x509_cert: '',
    enabled: true,
  });

  const [oidcForm, setOidcForm] = useState<OIDCFormData>({
    name: '',
    issuer: '',
    client_id: '',
    client_secret: '',
    enabled: true,
  });

  // UI states
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

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

  // Fetch available providers on mount
  useEffect(() => {
    fetchProviders();
    fetchExistingConfigs();
  }, []);

  const fetchProviders = async () => {
    try {
      setProvidersLoading(true);
      const response = await apiClient.get('/admin/sso/providers');
      setProviders(response.data.providers);
      setHasPremium(response.data.has_premium);
    } catch (err) {
      console.error('Failed to fetch providers:', err);
      // Default to Google only if fetch fails
      setProviders([{
        id: 'google',
        name: 'Google OAuth 2.0',
        description: 'Sign in with Google accounts',
        available: true,
        premium: false,
      }]);
    } finally {
      setProvidersLoading(false);
    }
  };

  const fetchExistingConfigs = async () => {
    try {
      const response = await apiClient.get('/admin/sso');
      setExistingConfigs(response.data.items || []);
    } catch (err) {
      console.error('Failed to fetch existing configs:', err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      let payload: Record<string, unknown>;

      if (selectedProvider === 'google') {
        payload = {
          provider: 'google',
          client_id: googleForm.client_id,
          client_secret: googleForm.client_secret,
          enabled: googleForm.enabled,
        };
      } else if (selectedProvider === 'saml') {
        payload = {
          provider: 'saml',
          name: samlForm.name,
          metadata_url: samlForm.metadata_url,
          client_id: samlForm.entity_id,
          sso_url: samlForm.sso_url,
          enabled: samlForm.enabled,
        };
      } else {
        payload = {
          provider: 'oauth2',
          name: oidcForm.name,
          metadata_url: oidcForm.issuer,
          client_id: oidcForm.client_id,
          client_secret: oidcForm.client_secret,
          enabled: oidcForm.enabled,
        };
      }

      await apiClient.post('/admin/sso', payload);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 3000);
      fetchExistingConfigs();

      // Reset form
      if (selectedProvider === 'google') {
        setGoogleForm({ client_id: '', client_secret: '', enabled: true });
      } else if (selectedProvider === 'saml') {
        setSamlForm({ name: '', metadata_url: '', entity_id: '', sso_url: '', slo_url: '', x509_cert: '', enabled: true });
      } else {
        setOidcForm({ name: '', issuer: '', client_id: '', client_secret: '', enabled: true });
      }
    } catch (err) {
      const error = err as { response?: { data?: { error?: string; message?: string } } };
      setError(error.response?.data?.error || error.response?.data?.message || 'Failed to save configuration');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (configId: number) => {
    if (!confirm('Are you sure you want to delete this SSO configuration?')) {
      return;
    }

    try {
      await apiClient.delete(`/admin/sso/${configId}`);
      fetchExistingConfigs();
    } catch (err) {
      const error = err as { response?: { data?: { error?: string } } };
      setError(error.response?.data?.error || 'Failed to delete configuration');
    }
  };

  const handleToggle = async (configId: number, currentEnabled: boolean) => {
    try {
      await apiClient.patch(`/admin/sso/${configId}`, { enabled: !currentEnabled });
      fetchExistingConfigs();
    } catch (err) {
      const error = err as { response?: { data?: { error?: string } } };
      setError(error.response?.data?.error || 'Failed to update configuration');
    }
  };

  const selectedProviderInfo = providers.find(p => p.id === selectedProvider);

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gold-gradient mb-2">
          SSO Configuration
        </h1>
        <p className="text-ice-navy-400">
          Configure single sign-on authentication for your organization
        </p>
      </div>

      {/* Existing Configurations */}
      {existingConfigs.length > 0 && (
        <div className="card mb-8">
          <h2 className="text-xl font-semibold text-ice-gold-400 mb-4">
            Configured Providers
          </h2>
          <div className="space-y-3">
            {existingConfigs.map((config) => (
              <div
                key={config.id}
                className="flex items-center justify-between p-4 bg-ice-navy-800/50 rounded-lg border border-ice-navy-700"
              >
                <div className="flex items-center gap-4">
                  <div className={`w-3 h-3 rounded-full ${config.enabled ? 'bg-green-500' : 'bg-gray-500'}`} />
                  <div>
                    <p className="font-medium text-white">{config.name}</p>
                    <p className="text-sm text-ice-navy-400">
                      {config.provider === 'oidc' && config.name === 'Google OAuth' ? 'Google' : config.provider.toUpperCase()}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleToggle(config.id, config.enabled)}
                    className={`px-3 py-1 text-sm rounded ${
                      config.enabled
                        ? 'bg-yellow-600/20 text-yellow-400 hover:bg-yellow-600/30'
                        : 'bg-green-600/20 text-green-400 hover:bg-green-600/30'
                    }`}
                  >
                    {config.enabled ? 'Disable' : 'Enable'}
                  </button>
                  <button
                    onClick={() => handleDelete(config.id)}
                    className="px-3 py-1 text-sm rounded bg-red-600/20 text-red-400 hover:bg-red-600/30"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Add New Configuration */}
      <div className="card">
        <h2 className="text-xl font-semibold text-ice-gold-400 mb-6">
          Add SSO Provider
        </h2>

        {success && (
          <div className="mb-6 p-4 bg-green-900/20 border border-green-700 rounded-lg text-green-400">
            SSO configuration saved successfully!
          </div>
        )}

        {error && (
          <div className="mb-6 p-4 bg-red-900/20 border border-red-700 rounded-lg text-red-400">
            {error}
          </div>
        )}

        {/* Provider Dropdown */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-ice-gold-400 mb-2">
            SSO Provider
          </label>
          <select
            value={selectedProvider}
            onChange={(e) => setSelectedProvider(e.target.value)}
            className="input"
            disabled={providersLoading}
          >
            {providers.map((provider) => (
              <option
                key={provider.id}
                value={provider.id}
                disabled={!provider.available}
              >
                {provider.name}
                {provider.premium && !provider.available && ' (Premium License Required)'}
                {provider.premium && provider.available && ' (Premium)'}
              </option>
            ))}
          </select>
          {selectedProviderInfo && (
            <p className="text-xs text-ice-navy-500 mt-1">
              {selectedProviderInfo.description}
            </p>
          )}
        </div>

        {/* Provider-specific forms */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Google OAuth Form */}
          {selectedProvider === 'google' && (
            <>
              <div className="p-4 bg-blue-900/20 border border-blue-700 rounded-lg mb-4">
                <p className="text-sm text-blue-300">
                  To set up Google OAuth, create credentials in the{' '}
                  <a
                    href="https://console.cloud.google.com/apis/credentials"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="underline hover:text-blue-200"
                  >
                    Google Cloud Console
                  </a>
                  . Add your callback URL:{' '}
                  <code className="bg-blue-900/50 px-1 rounded">
                    {window.location.origin}/api/v1/auth/google/callback
                  </code>
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-ice-gold-400 mb-2">
                    Client ID
                  </label>
                  <input
                    type="text"
                    placeholder="your-client-id.apps.googleusercontent.com"
                    value={googleForm.client_id}
                    onChange={(e) => setGoogleForm({ ...googleForm, client_id: e.target.value })}
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
                    placeholder="GOCSPX-..."
                    value={googleForm.client_secret}
                    onChange={(e) => setGoogleForm({ ...googleForm, client_secret: e.target.value })}
                    className="input"
                    required
                  />
                </div>
              </div>

              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={googleForm.enabled}
                  onChange={(e) => setGoogleForm({ ...googleForm, enabled: e.target.checked })}
                  className="mr-3"
                />
                <span className="text-sm text-ice-gold-400">Enable immediately after saving</span>
              </label>
            </>
          )}

          {/* SAML Form */}
          {selectedProvider === 'saml' && (
            <>
              {!hasPremium ? (
                <div className="p-6 bg-yellow-900/20 border border-yellow-700 rounded-lg text-center">
                  <svg className="w-12 h-12 mx-auto text-yellow-500 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                  <h3 className="text-lg font-semibold text-yellow-400 mb-2">Premium Feature</h3>
                  <p className="text-yellow-300/80">
                    SAML 2.0 SSO requires a premium license. Contact sales to upgrade.
                  </p>
                </div>
              ) : (
                <>
                  <div>
                    <label className="block text-sm font-medium text-ice-gold-400 mb-2">
                      Provider Name
                    </label>
                    <input
                      type="text"
                      placeholder="e.g., Okta, Azure AD, OneLogin"
                      value={samlForm.name}
                      onChange={(e) => setSamlForm({ ...samlForm, name: e.target.value })}
                      className="input"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-ice-gold-400 mb-2">
                      Metadata URL
                    </label>
                    <input
                      type="url"
                      placeholder="https://idp.example.com/metadata.xml"
                      value={samlForm.metadata_url}
                      onChange={(e) => setSamlForm({ ...samlForm, metadata_url: e.target.value })}
                      className="input"
                    />
                    <p className="text-xs text-ice-navy-500 mt-1">
                      Provide metadata URL for auto-configuration, or fill in manual fields below
                    </p>
                  </div>

                  <div className="border-t border-ice-navy-700 pt-4">
                    <p className="text-sm text-ice-navy-400 mb-4">Manual Configuration</p>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-ice-gold-400 mb-2">
                          Entity ID
                        </label>
                        <input
                          type="text"
                          placeholder="https://idp.example.com"
                          value={samlForm.entity_id}
                          onChange={(e) => setSamlForm({ ...samlForm, entity_id: e.target.value })}
                          className="input"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-ice-gold-400 mb-2">
                          SSO URL
                        </label>
                        <input
                          type="url"
                          placeholder="https://idp.example.com/sso"
                          value={samlForm.sso_url}
                          onChange={(e) => setSamlForm({ ...samlForm, sso_url: e.target.value })}
                          className="input"
                        />
                      </div>
                    </div>
                  </div>

                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={samlForm.enabled}
                      onChange={(e) => setSamlForm({ ...samlForm, enabled: e.target.checked })}
                      className="mr-3"
                    />
                    <span className="text-sm text-ice-gold-400">Enable immediately after saving</span>
                  </label>
                </>
              )}
            </>
          )}

          {/* OIDC Form */}
          {selectedProvider === 'oidc' && (
            <>
              {!hasPremium ? (
                <div className="p-6 bg-yellow-900/20 border border-yellow-700 rounded-lg text-center">
                  <svg className="w-12 h-12 mx-auto text-yellow-500 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                  <h3 className="text-lg font-semibold text-yellow-400 mb-2">Premium Feature</h3>
                  <p className="text-yellow-300/80">
                    OpenID Connect SSO requires a premium license. Contact sales to upgrade.
                  </p>
                </div>
              ) : (
                <>
                  <div>
                    <label className="block text-sm font-medium text-ice-gold-400 mb-2">
                      Provider Name
                    </label>
                    <input
                      type="text"
                      placeholder="e.g., Auth0, Keycloak"
                      value={oidcForm.name}
                      onChange={(e) => setOidcForm({ ...oidcForm, name: e.target.value })}
                      className="input"
                      required
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-ice-gold-400 mb-2">
                      Issuer URL
                    </label>
                    <input
                      type="url"
                      placeholder="https://your-domain.auth0.com"
                      value={oidcForm.issuer}
                      onChange={(e) => setOidcForm({ ...oidcForm, issuer: e.target.value })}
                      className="input"
                      required
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-ice-gold-400 mb-2">
                        Client ID
                      </label>
                      <input
                        type="text"
                        placeholder="your-client-id"
                        value={oidcForm.client_id}
                        onChange={(e) => setOidcForm({ ...oidcForm, client_id: e.target.value })}
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
                        value={oidcForm.client_secret}
                        onChange={(e) => setOidcForm({ ...oidcForm, client_secret: e.target.value })}
                        className="input"
                        required
                      />
                    </div>
                  </div>

                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={oidcForm.enabled}
                      onChange={(e) => setOidcForm({ ...oidcForm, enabled: e.target.checked })}
                      className="mr-3"
                    />
                    <span className="text-sm text-ice-gold-400">Enable immediately after saving</span>
                  </label>
                </>
              )}
            </>
          )}

          {/* Submit Button */}
          {(selectedProvider === 'google' || hasPremium) && (
            <Button type="submit" isLoading={loading}>
              Save Configuration
            </Button>
          )}
        </form>
      </div>

      {/* Security Info */}
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
            <span>OAuth 2.0 uses secure state parameters to prevent CSRF</span>
          </li>
          <li className="flex items-start">
            <span className="text-green-400 mr-2">✓</span>
            <span>JWT tokens include role-based access control</span>
          </li>
          {hasPremium && (
            <>
              <li className="flex items-start">
                <span className="text-green-400 mr-2">✓</span>
                <span>SAML responses are cryptographically validated</span>
              </li>
              <li className="flex items-start">
                <span className="text-green-400 mr-2">✓</span>
                <span>OIDC uses PKCE for enhanced security</span>
              </li>
            </>
          )}
        </ul>
      </div>
    </div>
  );
}
