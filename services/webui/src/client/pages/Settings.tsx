import { useState, useEffect } from 'react';
import Card from '../components/Card';
import Button from '../components/Button';
import TabNavigation from '../components/TabNavigation';
import api from '../lib/api';

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
  ];

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
                <label className="flex items-center justify-between">
                  <div>
                    <span className="text-ice-gold-400 block">Two-Factor Authentication</span>
                    <span className="text-sm text-ice-navy-400">Add extra security to your account</span>
                  </div>
                  <input
                    type="checkbox"
                    checked={preferences.two_factor_enabled}
                    onChange={(e) => handlePreferenceChange('two_factor_enabled', e.target.checked)}
                    className="w-5 h-5"
                  />
                </label>
              </div>

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
                <h3 className="text-ice-gold-400 mb-3">Active Sessions</h3>
                <div className="text-ice-navy-400 text-sm">
                  <p>Current session: This device</p>
                  <p className="text-ice-navy-500 mt-1">Last active: Just now</p>
                </div>
              </div>

              <div className="flex justify-end pt-6 border-t border-ice-navy-700">
                <Button onClick={handleSavePreferences} isLoading={isSaving}>
                  Save Changes
                </Button>
              </div>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}
