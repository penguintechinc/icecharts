import { useState, useEffect } from 'react';
import Modal from '../common/Modal';
import api from '../../lib/api';

export type StorageProvider = 'minio' | 'gdrive' | 'onedrive' | 's3';

export interface StorageConnection {
  id: number;
  provider: StorageProvider;
  name: string;
  isConnected: boolean;
  isDefault: boolean;
  isSystemProvider: boolean;
}

interface StoragePickerDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (provider: StorageProvider, connectionId?: number) => void;
  mode: 'save' | 'open';
  currentProvider?: StorageProvider;
}

const providerInfo: Record<StorageProvider, { name: string; icon: string; description: string }> = {
  minio: {
    name: 'IceCharts Cloud',
    icon: 'M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01',
    description: 'Default cloud storage (S3-compatible)',
  },
  gdrive: {
    name: 'Google Drive',
    icon: 'M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5',
    description: 'Save to your Google Drive account',
  },
  onedrive: {
    name: 'OneDrive',
    icon: 'M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z',
    description: 'Save to your Microsoft OneDrive',
  },
  s3: {
    name: 'Amazon S3',
    icon: 'M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01',
    description: 'Connect to AWS S3 bucket',
  },
};

export default function StoragePickerDialog({
  isOpen,
  onClose,
  onSelect,
  mode,
  currentProvider = 'minio',
}: StoragePickerDialogProps) {
  const [selectedProvider, setSelectedProvider] = useState<StorageProvider>(currentProvider);
  const [connections, setConnections] = useState<StorageConnection[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchConnections = async () => {
      if (!isOpen) return;

      setIsLoading(true);
      setError('');

      try {
        // Fetch available storage providers from API
        const response = await api.get<{ providers: any[] }>('/storage/providers');
        const providers = response.data.providers || [];

        // Transform API response to connections
        const transformed: StorageConnection[] = [
          // Always include MinIO as the default
          {
            id: 0,
            provider: 'minio',
            name: 'IceCharts Cloud',
            isConnected: true,
            isDefault: true,
            isSystemProvider: true,
          },
        ];

        // Add configured providers
        providers.forEach((p: any) => {
          if (p.provider_type !== 'minio') {
            transformed.push({
              id: p.id,
              provider: p.provider_type as StorageProvider,
              name: p.name,
              isConnected: p.is_active,
              isDefault: p.is_system_default,
              isSystemProvider: p.is_system_default,
            });
          }
        });

        setConnections(transformed);
      } catch (err: any) {
        console.error('Failed to fetch storage providers:', err);
        // Fallback to just MinIO
        setConnections([
          {
            id: 0,
            provider: 'minio',
            name: 'IceCharts Cloud',
            isConnected: true,
            isDefault: true,
            isSystemProvider: true,
          },
        ]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchConnections();
  }, [isOpen]);

  const handleConnect = async (provider: StorageProvider) => {
    setIsConnecting(true);
    setError('');

    try {
      if (provider === 'gdrive') {
        // Redirect to Google OAuth flow
        window.location.href = `/api/v1/storage/connect/gdrive?redirect=${encodeURIComponent(window.location.href)}`;
      } else if (provider === 'onedrive') {
        // Redirect to Microsoft OAuth flow
        window.location.href = `/api/v1/storage/connect/onedrive?redirect=${encodeURIComponent(window.location.href)}`;
      } else if (provider === 's3') {
        // For S3, show that they need to add their own
        setError('External S3 not configured. Contact your administrator or add your own S3 bucket in Settings.');
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to connect');
    } finally {
      setIsConnecting(false);
    }
  };

  const handleSelect = () => {
    const connection = connections.find((c) => c.provider === selectedProvider);
    onSelect(selectedProvider, connection?.id);
    onClose();
  };

  const isProviderConnected = (provider: StorageProvider): boolean => {
    return connections.some((c) => c.provider === provider && c.isConnected);
  };

  const isProviderAvailable = (provider: StorageProvider): boolean => {
    // MinIO is always available
    if (provider === 'minio') return true;
    // Other providers need to be configured by admin
    return connections.some((c) => c.provider === provider);
  };

  const availableProviders = (Object.keys(providerInfo) as StorageProvider[]).filter(
    (provider) => isProviderAvailable(provider)
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={mode === 'save' ? 'Save Drawing' : 'Open Drawing'}
      size="lg"
      footer={
        <>
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-ice-navy-300 hover:text-white transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSelect}
            disabled={!isProviderConnected(selectedProvider)}
            className="px-4 py-2 text-sm font-medium bg-ice-gold-500 hover:bg-ice-gold-600 text-ice-navy-900 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {mode === 'save' ? 'Save Here' : 'Browse'}
          </button>
        </>
      }
    >
      <div className="space-y-4">
        <p className="text-sm text-ice-navy-300">
          {mode === 'save'
            ? 'Choose where to save your drawing:'
            : 'Choose where to open a drawing from:'}
        </p>

        {error && (
          <div className="p-3 bg-red-900/20 border border-red-500/30 rounded-lg text-red-400 text-sm">
            {error}
          </div>
        )}

        {isLoading ? (
          <div className="space-y-3">
            {[1, 2].map((i) => (
              <div key={i} className="animate-pulse flex items-center gap-4 p-4 rounded-lg bg-ice-navy-700/50">
                <div className="w-12 h-12 rounded-lg bg-ice-navy-600"></div>
                <div className="flex-1">
                  <div className="h-4 bg-ice-navy-600 rounded w-1/3 mb-2"></div>
                  <div className="h-3 bg-ice-navy-600 rounded w-2/3"></div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="grid gap-3">
            {availableProviders.map((provider) => {
              const info = providerInfo[provider];
              const isConnected = isProviderConnected(provider);
              const isSelected = selectedProvider === provider;
              const connection = connections.find((c) => c.provider === provider);

              return (
                <div
                  key={provider}
                  onClick={() => isConnected && setSelectedProvider(provider)}
                  className={`
                    flex items-center gap-4 p-4 rounded-lg border-2 transition-all cursor-pointer
                    ${isSelected
                      ? 'border-ice-gold-500 bg-ice-gold-500/10'
                      : 'border-ice-navy-600 hover:border-ice-navy-500 bg-ice-navy-700/50'
                    }
                    ${!isConnected ? 'opacity-70' : ''}
                  `}
                >
                  {/* Icon */}
                  <div className={`
                    w-12 h-12 rounded-lg flex items-center justify-center
                    ${isSelected ? 'bg-ice-gold-500/20' : 'bg-ice-navy-600'}
                  `}>
                    <svg
                      className={`w-6 h-6 ${isSelected ? 'text-ice-gold-400' : 'text-ice-navy-300'}`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d={info.icon}
                      />
                    </svg>
                  </div>

                  {/* Info */}
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className={`font-medium ${isSelected ? 'text-ice-gold-400' : 'text-white'}`}>
                        {connection?.name || info.name}
                      </h3>
                      {provider === 'minio' && (
                        <span className="px-2 py-0.5 text-xs rounded-full bg-ice-gold-500/20 text-ice-gold-400">
                          Default
                        </span>
                      )}
                      {isConnected && provider !== 'minio' && (
                        <span className="px-2 py-0.5 text-xs rounded-full bg-green-500/20 text-green-400">
                          Connected
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-ice-navy-400">{info.description}</p>
                  </div>

                  {/* Connect/Select button */}
                  {!isConnected ? (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleConnect(provider);
                      }}
                      disabled={isConnecting}
                      className="px-3 py-1.5 text-sm font-medium bg-ice-navy-600 hover:bg-ice-navy-500 text-white rounded-lg transition-colors"
                    >
                      {isConnecting ? 'Connecting...' : 'Connect'}
                    </button>
                  ) : (
                    <div className="w-6 h-6 flex items-center justify-center">
                      {isSelected && (
                        <svg className="w-5 h-5 text-ice-gold-400" fill="currentColor" viewBox="0 0 20 20">
                          <path
                            fillRule="evenodd"
                            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                            clipRule="evenodd"
                          />
                        </svg>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Recent files hint */}
        {mode === 'open' && !isLoading && (
          <div className="pt-2 border-t border-ice-navy-700">
            <p className="text-xs text-ice-navy-400">
              Tip: Your recent drawings are automatically saved to IceCharts Cloud.
            </p>
          </div>
        )}
      </div>
    </Modal>
  );
}
