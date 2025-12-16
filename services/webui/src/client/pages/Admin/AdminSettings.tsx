import { useState, useEffect } from 'react';
import api from '../../lib/api';
import Button from '../../components/Button';
import Card from '../../components/Card';

interface AdminSetting {
  key: string;
  value: string;
  description: string;
  type: 'string' | 'number' | 'boolean';
  category: string;
}

interface SettingsByCategory {
  [category: string]: AdminSetting[];
}

export default function AdminSettings() {
  const [settings, setSettings] = useState<SettingsByCategory>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingSettings, setEditingSettings] = useState<Record<string, string>>({});
  const [isSaving, setIsSaving] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.get<{ settings: AdminSetting[] }>('/admin/settings');

      // Group settings by category
      const grouped: SettingsByCategory = {};
      response.data.settings.forEach((setting) => {
        if (!grouped[setting.category]) {
          grouped[setting.category] = [];
        }
        grouped[setting.category].push(setting);
      });

      setSettings(grouped);

      // Initialize editing state
      const initialEditing: Record<string, string> = {};
      response.data.settings.forEach((setting) => {
        initialEditing[setting.key] = setting.value;
      });
      setEditingSettings(initialEditing);
    } catch (err: any) {
      console.error('Failed to fetch settings:', err);
      setError(err.response?.data?.message || 'Failed to load settings');
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (key: string, value: string) => {
    setEditingSettings({
      ...editingSettings,
      [key]: value,
    });
  };

  const handleSaveSettings = async () => {
    setIsSaving(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const updates = Object.entries(editingSettings).map(([key, value]) => ({
        key,
        value,
      }));

      await api.put('/admin/settings', { updates });
      setSuccessMessage('Settings saved successfully!');

      setTimeout(() => {
        setSuccessMessage(null);
      }, 3000);
    } catch (err: any) {
      console.error('Failed to save settings:', err);
      setError(err.response?.data?.message || 'Failed to save settings');
    } finally {
      setIsSaving(false);
    }
  };

  const handleResetSettings = () => {
    if (confirm('Are you sure you want to reset all settings to defaults?')) {
      // Re-fetch to reset
      fetchSettings();
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-ice-gold-400 text-xl">Loading settings...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-ice-gold-400">Admin Settings</h1>
          <p className="text-ice-navy-400 mt-1">Configure system-wide application settings</p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={handleResetSettings}
            variant="secondary"
          >
            Reset to Defaults
          </Button>
        </div>
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

      {/* Settings by Category */}
      {Object.keys(settings).length > 0 ? (
        Object.entries(settings).map(([category, categorySettings]) => (
          <Card key={category}>
            <h2 className="text-xl font-bold text-ice-gold-400 mb-6 pb-4 border-b border-ice-navy-700">
              {category}
            </h2>

            <div className="space-y-6">
              {categorySettings.map((setting) => (
                <div key={setting.key} className="space-y-2">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <label className="block text-sm font-semibold text-ice-gold-400 mb-1">
                        {setting.key}
                      </label>
                      <p className="text-xs text-ice-navy-400 mb-2">{setting.description}</p>
                    </div>
                    <span className="text-xs text-ice-navy-500 bg-ice-navy-800 px-2 py-1 rounded">
                      {setting.type}
                    </span>
                  </div>

                  {setting.type === 'boolean' ? (
                    <div className="flex items-center gap-3">
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={editingSettings[setting.key] === 'true' || editingSettings[setting.key] === '1'}
                          onChange={(e) =>
                            handleInputChange(setting.key, e.target.checked ? 'true' : 'false')
                          }
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-ice-navy-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-ice-gold-400 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-ice-gold-400" />
                      </label>
                      <span className="text-ice-navy-300">
                        {editingSettings[setting.key] === 'true' || editingSettings[setting.key] === '1' ? 'Enabled' : 'Disabled'}
                      </span>
                    </div>
                  ) : (
                    <input
                      type={setting.type === 'number' ? 'number' : 'text'}
                      value={editingSettings[setting.key] || ''}
                      onChange={(e) => handleInputChange(setting.key, e.target.value)}
                      className="w-full px-4 py-2 bg-ice-navy-800 text-ice-gold-400 border border-ice-navy-700 rounded-lg focus:outline-none focus:border-ice-gold-600"
                    />
                  )}
                </div>
              ))}
            </div>
          </Card>
        ))
      ) : (
        <Card>
          <div className="text-center py-8">
            <div className="text-ice-navy-400">No settings found</div>
          </div>
        </Card>
      )}

      {/* Save Button */}
      <div className="flex justify-end gap-2 sticky bottom-0 bg-ice-navy-900 py-4">
        <Button
          onClick={handleSaveSettings}
          disabled={isSaving}
        >
          {isSaving ? 'Saving...' : 'Save Settings'}
        </Button>
      </div>
    </div>
  );
}
