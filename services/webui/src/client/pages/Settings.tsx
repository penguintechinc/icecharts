import { useState, useEffect } from 'react';
import Card from '../components/Card';
import Button from '../components/Button';
import TabNavigation from '../components/TabNavigation';
import api from '../lib/api';
import { useConnectors } from '../hooks/useConnectors';
import type { Connector } from '../types/connector';

interface UserPreferences {
  dark_mode?: boolean;
  compact_view?: boolean;
  timezone?: string;
  email_notifications?: boolean;
  system_alerts?: boolean;
  weekly_reports?: boolean;
  two_factor_enabled?: boolean;
  session_timeout?: number;
  [key: string]: any;
}

export default function Settings() {
  const [activeTab, setActiveTab] = useState('general');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });

  const [preferences, setPreferences] = useState<UserPreferences>({
    dark_mode: true,
    compact_view: false,
    timezone: 'UTC',
    email_notifications: true,
    system_alerts: true,
    weekly_reports: false,
    two_factor_enabled: false,
    session_timeout: 60,
  });

  const tabs = [
    { id: 'general', label: 'General' },
    { id: 'notifications', label: 'Notifications' },
    { id: 'security', label: 'Security' },
    { id: 'connectors', label: 'Connectors' },
  ];

  // Fetch connectors for the Connectors tab
  const { connectors, loading: connectorsLoading, error: connectorsError } = useConnectors();

  // Fetch user preferences on component mount
  useEffect(() => {
    fetchPreferences();
  }, []);

  const fetchPreferences = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.get<{ preferences: UserPreferences }>(
        '/profile/preferences'
      );
      const fetchedPrefs = response.data.preferences || {};
      setPreferences({
        dark_mode: fetchedPrefs.dark_mode !== false,
        compact_view: fetchedPrefs.compact_view === true,
        timezone: fetchedPrefs.timezone || 'UTC',
        email_notifications: fetchedPrefs.email_notifications !== false,
        system_alerts: fetchedPrefs.system_alerts !== false,
        weekly_reports: fetchedPrefs.weekly_reports === true,
        two_factor_enabled: fetchedPrefs.two_factor_enabled === true,
        session_timeout: fetchedPrefs.session_timeout || 60,
      });
    } catch (err) {
      console.error('Failed to fetch preferences:', err);
      setError('Failed to load your settings. Using defaults.');
    } finally {
      setIsLoading(false);
    }
  };

  const handlePreferenceChange = (key: string, value: any) => {
    setPreferences((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const handleSavePreferences = async () => {
    setIsSaving(true);
    setError(null);
    setSuccess(null);
    try {
      await api.put('/profile/preferences', preferences);
      setSuccess('Settings saved successfully');
      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      console.error('Failed to save preferences:', err);
      setError('Failed to save settings. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  const handlePasswordChange = async () => {
    setError(null);
    setSuccess(null);

    // Validate passwords match
    if (passwordData.new_password !== passwordData.confirm_password) {
      setError('New passwords do not match');
      return;
    }

    // Validate password length
    if (passwordData.new_password.length < 8) {
      setError('New password must be at least 8 characters');
      return;
    }

    setIsSaving(true);
    try {
      await api.put('/profile/password', {
        current_password: passwordData.current_password,
        new_password: passwordData.new_password,
      });
      setSuccess('Password changed successfully');
      setPasswordData({
        current_password: '',
        new_password: '',
        confirm_password: '',
      });
      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      console.error('Failed to change password:', err);
      setError('Failed to change password. Please check your current password.');
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div>
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-ice-gold-400">Settings</h1>
          <p className="text-ice-navy-400 mt-1">Manage application settings</p>
        </div>
        <Card>
          <div className="flex items-center justify-center py-8">
            <p className="text-ice-navy-400">Loading your settings...</p>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-ice-gold-400">Settings</h1>
        <p className="text-ice-navy-400 mt-1">Manage application settings</p>
      </div>

      {/* Messages */}
      {error && (
        <div className="mb-4 p-3 bg-red-900/30 border border-red-700 rounded-lg text-red-400">
          {error}
        </div>
      )}
      {success && (
        <div className="mb-4 p-3 bg-green-900/30 border border-green-700 rounded-lg text-green-400">
          {success}
        </div>
      )}

      {/* Tab Navigation */}
      <TabNavigation tabs={tabs} activeTab={activeTab} onChange={setActiveTab} />

      {/* Tab Content */}
      <div className="mt-6">
        {activeTab === 'general' && (
          <Card title="General Settings">
            <div className="space-y-6">
              <div>
                <label className="flex items-center justify-between">
                  <div>
                    <span className="text-ice-gold-400 block">Dark Mode</span>
                    <span className="text-sm text-ice-navy-400">Use dark theme (default)</span>
                  </div>
                  <input
                    type="checkbox"
                    checked={preferences.dark_mode}
                    onChange={(e) => handlePreferenceChange('dark_mode', e.target.checked)}
                    className="w-5 h-5"
                  />
                </label>
              </div>

              <div>
                <label className="flex items-center justify-between">
                  <div>
                    <span className="text-ice-gold-400 block">Compact View</span>
                    <span className="text-sm text-ice-navy-400">Reduce spacing in tables</span>
                  </div>
                  <input
                    type="checkbox"
                    checked={preferences.compact_view}
                    onChange={(e) => handlePreferenceChange('compact_view', e.target.checked)}
                    className="w-5 h-5"
                  />
                </label>
              </div>

              <div>
                <label className="block">
                  <span className="text-ice-gold-400 block mb-2">Timezone</span>
                  <select
                    value={preferences.timezone}
                    onChange={(e) => handlePreferenceChange('timezone', e.target.value)}
                    className="input"
                  >
                    <option value="UTC">UTC</option>
                    <option value="America/New_York">Eastern Time</option>
                    <option value="America/Chicago">Central Time</option>
                    <option value="America/Denver">Mountain Time</option>
                    <option value="America/Los_Angeles">Pacific Time</option>
                  </select>
                </label>
              </div>

              <div className="flex justify-end pt-6 border-t border-ice-navy-700">
                <Button onClick={handleSavePreferences} isLoading={isSaving}>
                  Save Changes
                </Button>
              </div>
            </div>
          </Card>
        )}

        {activeTab === 'notifications' && (
          <Card title="Notification Settings">
            <div className="space-y-6">
              <div>
                <label className="flex items-center justify-between">
                  <div>
                    <span className="text-ice-gold-400 block">Email Notifications</span>
                    <span className="text-sm text-ice-navy-400">Receive email for important events</span>
                  </div>
                  <input
                    type="checkbox"
                    checked={preferences.email_notifications}
                    onChange={(e) => handlePreferenceChange('email_notifications', e.target.checked)}
                    className="w-5 h-5"
                  />
                </label>
              </div>

              <div>
                <label className="flex items-center justify-between">
                  <div>
                    <span className="text-ice-gold-400 block">System Alerts</span>
                    <span className="text-sm text-ice-navy-400">Get notified about system issues</span>
                  </div>
                  <input
                    type="checkbox"
                    checked={preferences.system_alerts}
                    onChange={(e) => handlePreferenceChange('system_alerts', e.target.checked)}
                    className="w-5 h-5"
                  />
                </label>
              </div>

              <div>
                <label className="flex items-center justify-between">
                  <div>
                    <span className="text-ice-gold-400 block">Weekly Reports</span>
                    <span className="text-sm text-ice-navy-400">Receive weekly summary email</span>
                  </div>
                  <input
                    type="checkbox"
                    checked={preferences.weekly_reports}
                    onChange={(e) => handlePreferenceChange('weekly_reports', e.target.checked)}
                    className="w-5 h-5"
                  />
                </label>
              </div>

              <div className="flex justify-end pt-6 border-t border-ice-navy-700">
                <Button onClick={handleSavePreferences} isLoading={isSaving}>
                  Save Changes
                </Button>
              </div>
            </div>
          </Card>
        )}

        {activeTab === 'security' && (
          <Card title="Security Settings">
            <div className="space-y-6">
              <div>
                <label className="block">
                  <span className="text-ice-gold-400 block mb-2">Session Timeout</span>
                  <select
                    value={preferences.session_timeout}
                    onChange={(e) => handlePreferenceChange('session_timeout', parseInt(e.target.value))}
                    className="input"
                  >
                    <option value="15">15 minutes</option>
                    <option value="30">30 minutes</option>
                    <option value="60">1 hour</option>
                    <option value="480">8 hours</option>
                  </select>
                </label>
              </div>

              <div className="pt-4 border-t border-ice-navy-700">
                <h3 className="text-ice-gold-400 mb-3">Change Password</h3>
                <div className="space-y-4">
                  <div>
                    <label className="block">
                      <span className="text-ice-navy-400 text-sm block mb-1">Current Password</span>
                      <input
                        type="password"
                        value={passwordData.current_password}
                        onChange={(e) => setPasswordData({ ...passwordData, current_password: e.target.value })}
                        className="input"
                        placeholder="Enter current password"
                      />
                    </label>
                  </div>
                  <div>
                    <label className="block">
                      <span className="text-ice-navy-400 text-sm block mb-1">New Password</span>
                      <input
                        type="password"
                        value={passwordData.new_password}
                        onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                        className="input"
                        placeholder="Enter new password (min 8 characters)"
                        minLength={8}
                      />
                    </label>
                  </div>
                  <div>
                    <label className="block">
                      <span className="text-ice-navy-400 text-sm block mb-1">Confirm New Password</span>
                      <input
                        type="password"
                        value={passwordData.confirm_password}
                        onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                        className="input"
                        placeholder="Confirm new password"
                      />
                    </label>
                  </div>
                  <div>
                    <Button
                      onClick={handlePasswordChange}
                      isLoading={isSaving}
                      disabled={!passwordData.current_password || !passwordData.new_password || !passwordData.confirm_password}
                    >
                      Change Password
                    </Button>
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-ice-navy-700">
                <h3 className="text-ice-gold-400 mb-3">Active Sessions</h3>
                <div className="text-ice-navy-400 text-sm">
                  <p>Current session: This device</p>
                  <p className="text-ice-navy-500 mt-1">Last active: Just now</p>
                </div>
              </div>

              <div className="flex justify-end pt-6 border-t border-ice-navy-700">
                <Button onClick={handleSavePreferences} isLoading={isSaving}>
                  Save Security Settings
                </Button>
              </div>
            </div>
          </Card>
        )}

        {activeTab === 'connectors' && (
          <div className="space-y-4">
            <Card>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-ice-gold-400">Connectors</h3>
                  <p className="text-sm text-ice-navy-400">
                    Configure connections to external services for workflow automation
                  </p>
                </div>
              </div>

              {connectorsLoading ? (
                <div className="flex items-center justify-center py-8">
                  <p className="text-ice-navy-400">Loading connectors...</p>
                </div>
              ) : connectorsError ? (
                <div className="p-4 bg-red-900/30 border border-red-700 rounded-lg text-red-400">
                  {connectorsError}
                </div>
              ) : connectors.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-ice-navy-400">No connectors available</p>
                  <p className="text-sm text-ice-navy-500 mt-1">
                    Connectors will appear here when installed
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {connectors.map((connector) => (
                    <ConnectorCard key={connector.id} connector={connector} />
                  ))}
                </div>
              )}
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * ConnectorCard - Display a single connector with its configuration status
 */
function ConnectorCard({ connector }: { connector: Connector }) {
  const [expanded, setExpanded] = useState(false);

  const totalNodes = connector.triggers.length + connector.actions.length + connector.transforms.length;

  return (
    <div
      className="border border-ice-navy-700 rounded-lg overflow-hidden"
      style={{ borderLeftWidth: '4px', borderLeftColor: connector.color }}
    >
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-4 hover:bg-ice-navy-800/50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="text-2xl">{connector.icon}</span>
          <div className="text-left">
            <h4 className="font-medium text-white">{connector.name}</h4>
            <p className="text-sm text-ice-navy-400">{connector.description}</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-xs text-ice-navy-500">v{connector.version}</span>
          <span
            className="px-2 py-1 text-xs rounded-full"
            style={{ backgroundColor: `${connector.color}30`, color: connector.color }}
          >
            {totalNodes} nodes
          </span>
          <svg
            className={`w-5 h-5 text-ice-navy-400 transition-transform ${expanded ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </button>

      {/* Expanded content */}
      {expanded && (
        <div className="border-t border-ice-navy-700 p-4 bg-ice-navy-800/30">
          {/* Node counts by category */}
          <div className="grid grid-cols-3 gap-4 mb-4">
            <div className="text-center p-3 bg-green-500/10 border border-green-500/30 rounded-lg">
              <div className="text-2xl font-bold text-green-400">{connector.triggers.length}</div>
              <div className="text-xs text-green-400/70">Triggers</div>
            </div>
            <div className="text-center p-3 bg-orange-500/10 border border-orange-500/30 rounded-lg">
              <div className="text-2xl font-bold text-orange-400">{connector.actions.length}</div>
              <div className="text-xs text-orange-400/70">Actions</div>
            </div>
            <div className="text-center p-3 bg-cyan-500/10 border border-cyan-500/30 rounded-lg">
              <div className="text-2xl font-bold text-cyan-400">{connector.transforms.length}</div>
              <div className="text-xs text-cyan-400/70">Transforms</div>
            </div>
          </div>

          {/* Configuration section - placeholder for future implementation */}
          <div className="p-4 bg-ice-navy-900/50 rounded-lg">
            <h5 className="text-sm font-medium text-ice-navy-300 mb-2">Connection Settings</h5>
            <p className="text-xs text-ice-navy-500 mb-3">
              Connection configuration will be available in a future update
            </p>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-yellow-500"></span>
              <span className="text-sm text-yellow-400">Not configured</span>
            </div>
          </div>

          {/* Available nodes preview */}
          <div className="mt-4">
            <h5 className="text-sm font-medium text-ice-navy-300 mb-2">Available Nodes</h5>
            <div className="flex flex-wrap gap-2">
              {connector.triggers.slice(0, 3).map((t) => (
                <span key={t.id} className="px-2 py-1 text-xs bg-green-500/20 text-green-400 rounded">
                  {t.icon || connector.icon} {t.name}
                </span>
              ))}
              {connector.actions.slice(0, 3).map((a) => (
                <span key={a.id} className="px-2 py-1 text-xs bg-orange-500/20 text-orange-400 rounded">
                  {a.icon || connector.icon} {a.name}
                </span>
              ))}
              {totalNodes > 6 && (
                <span className="px-2 py-1 text-xs bg-ice-navy-700 text-ice-navy-400 rounded">
                  +{totalNodes - 6} more
                </span>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
