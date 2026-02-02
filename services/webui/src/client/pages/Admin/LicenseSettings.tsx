import { useState, useEffect } from 'react';
import api from '../../lib/api';
import Button from '../../components/Button';
import Card from '../../components/Card';

interface LicenseFeature {
  name: string;
  display_name?: string;
  entitled: boolean;
  description?: string;
  required_tier?: string;
  units?: number;
}

interface LicenseLimits {
  max_users?: number;
  max_servers?: number;
  data_retention_days?: number;
}

interface LicenseStatus {
  configured: boolean;
  license_key_masked: string | null;
  valid: boolean;
  tier: string | null;
  customer: string | null;
  expires_at: string | null;
  features: LicenseFeature[];
  limits: LicenseLimits | null;
  grace_period: boolean;
  error: string | null;
}

interface ValidationResult {
  valid: boolean;
  tier?: string;
  customer?: string;
  expires_at?: string;
  features?: LicenseFeature[];
  limits?: LicenseLimits;
  error?: string;
}

export default function LicenseSettings() {
  const [license, setLicense] = useState<LicenseStatus | null>(null);
  const [allFeatures, setAllFeatures] = useState<LicenseFeature[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [newLicenseKey, setNewLicenseKey] = useState('');
  const [isValidating, setIsValidating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    fetchLicenseStatus();
    fetchAllFeatures();
  }, []);

  const fetchLicenseStatus = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.get<{ license: LicenseStatus }>('/admin/license');
      setLicense(response.data.license);
    } catch (err: any) {
      console.error('Failed to fetch license status:', err);
      setError(err.response?.data?.error || 'Failed to load license status');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchAllFeatures = async () => {
    try {
      const response = await api.get<{ features: LicenseFeature[] }>('/admin/license/features');
      setAllFeatures(response.data.features || []);
    } catch (err) {
      console.error('Failed to fetch features:', err);
    }
  };

  const handleValidate = async () => {
    if (!newLicenseKey.trim()) {
      setError('Please enter a license key');
      return;
    }

    setIsValidating(true);
    setValidationResult(null);
    setError(null);

    try {
      const response = await api.post<ValidationResult>('/admin/license/validate', {
        license_key: newLicenseKey.trim(),
      });
      setValidationResult(response.data);
    } catch (err: any) {
      console.error('Failed to validate license:', err);
      setError(err.response?.data?.error || 'Failed to validate license key');
    } finally {
      setIsValidating(false);
    }
  };

  const handleSave = async () => {
    if (!newLicenseKey.trim()) {
      setError('Please enter a license key');
      return;
    }

    setIsSaving(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const response = await api.put<{ license: LicenseStatus; message: string }>(
        '/admin/license',
        { license_key: newLicenseKey.trim() }
      );
      setLicense(response.data.license);
      setNewLicenseKey('');
      setValidationResult(null);
      setSuccessMessage('License key updated successfully');
      fetchAllFeatures();

      setTimeout(() => setSuccessMessage(null), 5000);
    } catch (err: any) {
      console.error('Failed to save license:', err);
      setError(err.response?.data?.error || 'Failed to save license key');
    } finally {
      setIsSaving(false);
    }
  };

  const handleRemove = async () => {
    if (!confirm('Are you sure you want to remove the license key? This will disable premium features.')) {
      return;
    }

    setIsSaving(true);
    setError(null);

    try {
      const response = await api.delete<{ license: LicenseStatus }>('/admin/license');
      setLicense(response.data.license);
      setSuccessMessage('License key removed');
      fetchAllFeatures();

      setTimeout(() => setSuccessMessage(null), 5000);
    } catch (err: any) {
      console.error('Failed to remove license:', err);
      setError(err.response?.data?.error || 'Failed to remove license key');
    } finally {
      setIsSaving(false);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    setError(null);

    try {
      const response = await api.post<{ license: LicenseStatus }>('/admin/license/refresh');
      setLicense(response.data.license);
      setSuccessMessage('License refreshed successfully');
      fetchAllFeatures();

      setTimeout(() => setSuccessMessage(null), 5000);
    } catch (err: any) {
      console.error('Failed to refresh license:', err);
      setError(err.response?.data?.error || 'Failed to refresh license');
    } finally {
      setIsRefreshing(false);
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'N/A';
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      });
    } catch {
      return dateStr;
    }
  };

  const getTierBadgeColor = (tier: string | null) => {
    switch (tier?.toLowerCase()) {
      case 'enterprise':
        return 'bg-purple-900 text-purple-300 border-purple-700';
      case 'professional':
        return 'bg-blue-900 text-blue-300 border-blue-700';
      case 'community':
        return 'bg-gray-800 text-gray-300 border-gray-600';
      default:
        return 'bg-ice-navy-800 text-ice-navy-400 border-ice-navy-600';
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-ice-gold-400 text-xl">Loading license information...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-ice-gold-400">License Settings</h1>
          <p className="text-ice-navy-400 mt-1">Manage your IceCharts license key and view entitled features</p>
        </div>
        <Button
          onClick={handleRefresh}
          variant="secondary"
          disabled={isRefreshing || !license?.configured}
        >
          {isRefreshing ? 'Refreshing...' : 'Refresh License'}
        </Button>
      </div>

      {/* Status Messages */}
      {error && (
        <div className="p-4 bg-red-900 border border-red-700 rounded-lg text-red-400">
          {error}
        </div>
      )}

      {successMessage && (
        <div className="p-4 bg-green-900 border border-green-700 rounded-lg text-green-400">
          {successMessage}
        </div>
      )}

      {/* Current License Status */}
      <Card>
        <h2 className="text-xl font-bold text-ice-gold-400 mb-6 pb-4 border-b border-ice-navy-700">
          Current License Status
        </h2>

        {license?.configured ? (
          <div className="space-y-4">
            {/* Status Row */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className={`w-3 h-3 rounded-full ${license.valid ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-ice-navy-300">
                  {license.valid ? 'License Valid' : 'License Invalid'}
                </span>
                {license.grace_period && (
                  <span className="px-2 py-1 text-xs bg-yellow-900 text-yellow-300 rounded border border-yellow-700">
                    Grace Period
                  </span>
                )}
              </div>
              {license.tier && (
                <span className={`px-3 py-1 text-sm font-medium rounded border ${getTierBadgeColor(license.tier)}`}>
                  {license.tier.charAt(0).toUpperCase() + license.tier.slice(1)}
                </span>
              )}
            </div>

            {/* License Details */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
              <div>
                <label className="block text-sm text-ice-navy-400 mb-1">License Key</label>
                <p className="text-ice-navy-200 font-mono">{license.license_key_masked || 'Not configured'}</p>
              </div>
              <div>
                <label className="block text-sm text-ice-navy-400 mb-1">Customer</label>
                <p className="text-ice-navy-200">{license.customer || 'N/A'}</p>
              </div>
              <div>
                <label className="block text-sm text-ice-navy-400 mb-1">Expires</label>
                <p className="text-ice-navy-200">{formatDate(license.expires_at)}</p>
              </div>
              {license.limits && (
                <div>
                  <label className="block text-sm text-ice-navy-400 mb-1">Limits</label>
                  <p className="text-ice-navy-200 text-sm">
                    {license.limits.max_users !== undefined && (
                      <span>Users: {license.limits.max_users === -1 ? 'Unlimited' : license.limits.max_users}</span>
                    )}
                  </p>
                </div>
              )}
            </div>

            {license.error && (
              <div className="mt-4 p-3 bg-red-900/50 border border-red-800 rounded-lg">
                <p className="text-red-400 text-sm">{license.error}</p>
              </div>
            )}

            {/* Remove License Button */}
            <div className="mt-6 pt-4 border-t border-ice-navy-700">
              <Button onClick={handleRemove} variant="danger" disabled={isSaving}>
                Remove License Key
              </Button>
            </div>
          </div>
        ) : (
          <div className="text-center py-8">
            <div className="text-ice-navy-400 mb-2">No license key configured</div>
            <p className="text-ice-navy-500 text-sm">
              Enter a license key below to enable premium features.
            </p>
          </div>
        )}
      </Card>

      {/* Update License Key */}
      <Card>
        <h2 className="text-xl font-bold text-ice-gold-400 mb-6 pb-4 border-b border-ice-navy-700">
          {license?.configured ? 'Update License Key' : 'Enter License Key'}
        </h2>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-ice-gold-400 mb-2">
              License Key
            </label>
            <input
              type="text"
              value={newLicenseKey}
              onChange={(e) => {
                setNewLicenseKey(e.target.value.toUpperCase());
                setValidationResult(null);
              }}
              placeholder="PENG-XXXX-XXXX-XXXX-XXXX-ABCD"
              className="w-full px-4 py-3 bg-ice-navy-800 text-ice-gold-400 border border-ice-navy-700 rounded-lg focus:outline-none focus:border-ice-gold-600 font-mono"
            />
            <p className="mt-2 text-sm text-ice-navy-500">
              Format: PENG-XXXX-XXXX-XXXX-XXXX-ABCD
            </p>
          </div>

          {/* Validation Result */}
          {validationResult && (
            <div className={`p-4 rounded-lg border ${
              validationResult.valid
                ? 'bg-green-900/50 border-green-700'
                : 'bg-red-900/50 border-red-700'
            }`}>
              <div className="flex items-center gap-2 mb-2">
                <div className={`w-2 h-2 rounded-full ${validationResult.valid ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className={validationResult.valid ? 'text-green-400' : 'text-red-400'}>
                  {validationResult.valid ? 'License Valid' : 'License Invalid'}
                </span>
              </div>
              {validationResult.valid && (
                <div className="text-sm text-ice-navy-300 space-y-1 mt-3">
                  <p><span className="text-ice-navy-500">Tier:</span> {validationResult.tier}</p>
                  <p><span className="text-ice-navy-500">Customer:</span> {validationResult.customer}</p>
                  <p><span className="text-ice-navy-500">Expires:</span> {formatDate(validationResult.expires_at || null)}</p>
                  {validationResult.features && validationResult.features.length > 0 && (
                    <div className="mt-2">
                      <span className="text-ice-navy-500">Features: </span>
                      <span className="text-green-400">
                        {validationResult.features.filter(f => f.entitled).map(f => f.name).join(', ') || 'None'}
                      </span>
                    </div>
                  )}
                </div>
              )}
              {validationResult.error && (
                <p className="text-red-400 text-sm mt-2">{validationResult.error}</p>
              )}
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-3">
            <Button
              onClick={handleValidate}
              variant="secondary"
              disabled={isValidating || !newLicenseKey.trim()}
            >
              {isValidating ? 'Validating...' : 'Validate'}
            </Button>
            <Button
              onClick={handleSave}
              disabled={isSaving || !newLicenseKey.trim()}
            >
              {isSaving ? 'Saving...' : 'Save License Key'}
            </Button>
          </div>
        </div>
      </Card>

      {/* Features List */}
      <Card>
        <h2 className="text-xl font-bold text-ice-gold-400 mb-6 pb-4 border-b border-ice-navy-700">
          Licensed Features
        </h2>

        <div className="space-y-3">
          {allFeatures.length > 0 ? (
            allFeatures.map((feature) => (
              <div
                key={feature.name}
                className="flex items-center justify-between p-4 bg-ice-navy-800/50 rounded-lg border border-ice-navy-700"
              >
                <div>
                  <div className="flex items-center gap-3">
                    <span className="text-ice-gold-400 font-medium">
                      {feature.display_name || feature.name}
                    </span>
                    {feature.required_tier && (
                      <span className="px-2 py-0.5 text-xs bg-ice-navy-700 text-ice-navy-400 rounded">
                        {feature.required_tier}
                      </span>
                    )}
                  </div>
                  {feature.description && (
                    <p className="text-sm text-ice-navy-400 mt-1">{feature.description}</p>
                  )}
                </div>
                <div className={`px-3 py-1 rounded text-sm font-medium ${
                  feature.entitled
                    ? 'bg-green-900/50 text-green-400 border border-green-700'
                    : 'bg-ice-navy-700 text-ice-navy-400 border border-ice-navy-600'
                }`}>
                  {feature.entitled ? 'Enabled' : 'Not Available'}
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-8 text-ice-navy-400">
              No features defined
            </div>
          )}
        </div>
      </Card>

      {/* Help Section */}
      <Card>
        <h2 className="text-xl font-bold text-ice-gold-400 mb-4">Need a License?</h2>
        <p className="text-ice-navy-300 mb-4">
          Contact PenguinTech to purchase or upgrade your IceCharts license.
        </p>
        <div className="space-y-2 text-sm text-ice-navy-400">
          <p><span className="text-ice-navy-500">Sales:</span> sales@penguintech.io</p>
          <p><span className="text-ice-navy-500">Support:</span> support@penguintech.io</p>
          <p><span className="text-ice-navy-500">License Status:</span> status.penguintech.io</p>
        </div>
      </Card>
    </div>
  );
}
