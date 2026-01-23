/**
 * WebhookConfig - Webhook settings form
 */

import React, { useState, useEffect } from 'react';

interface WebhookConfigProps {
  functionId: string;
}

export const WebhookConfig: React.FC<WebhookConfigProps> = ({ functionId }) => {
  const [config, setConfig] = useState({
    webhook_url: '',
    webhook_token: '',
    validate_signature: false,
    allowed_methods: ['POST'],
    ip_whitelist: [] as string[],
  });

  useEffect(() => {
    // TODO: Fetch webhook config from API
    setConfig({
      webhook_url: `https://icecharts.example.com/api/v1/iceruns/hook/abc123...`,
      webhook_token: 'abc123...',
      validate_signature: false,
      allowed_methods: ['POST'],
      ip_whitelist: [],
    });
  }, [functionId]);

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="space-y-6">
      {/* Webhook URL */}
      <div>
        <label className="block text-sm font-medium text-ice-navy-300 mb-2">
          Webhook URL
        </label>
        <div className="flex">
          <input
            type="text"
            value={config.webhook_url}
            readOnly
            className="flex-1 px-4 py-2 bg-ice-navy-700 text-white rounded-l-lg border border-ice-navy-600 font-mono text-sm"
          />
          <button
            onClick={() => handleCopy(config.webhook_url)}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-r-lg"
          >
            Copy
          </button>
        </div>
      </div>

      {/* Bearer Token */}
      <div>
        <label className="block text-sm font-medium text-ice-navy-300 mb-2">
          Bearer Token
        </label>
        <div className="flex">
          <input
            type="text"
            value={config.webhook_token}
            readOnly
            className="flex-1 px-4 py-2 bg-ice-navy-700 text-white rounded-l-lg border border-ice-navy-600 font-mono text-sm"
          />
          <button
            onClick={() => handleCopy(config.webhook_token)}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-r-lg"
          >
            Copy
          </button>
        </div>
        <button className="mt-2 text-sm text-red-400 hover:text-red-300">
          Regenerate Token
        </button>
      </div>

      {/* Example cURL */}
      <div>
        <label className="block text-sm font-medium text-ice-navy-300 mb-2">
          Example cURL
        </label>
        <pre className="bg-ice-navy-900 p-4 rounded text-sm text-ice-navy-300 overflow-x-auto">
{`curl -X POST ${config.webhook_url} \\
  -H "Content-Type: application/json" \\
  -d '{"example": "data"}'`}
        </pre>
      </div>

      {/* Advanced Settings */}
      <div>
        <h3 className="text-lg font-semibold text-white mb-4">Advanced Settings</h3>
        <label className="flex items-center space-x-2 mb-4">
          <input
            type="checkbox"
            checked={config.validate_signature}
            onChange={(e) => setConfig({ ...config, validate_signature: e.target.checked })}
            className="form-checkbox h-5 w-5 text-purple-600"
          />
          <span className="text-white">Validate HMAC signature</span>
        </label>
      </div>
    </div>
  );
};
