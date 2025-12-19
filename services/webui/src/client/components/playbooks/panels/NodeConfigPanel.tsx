import React, { useState, useEffect } from 'react';
import type { Node } from '@xyflow/react';

interface NodeConfigPanelProps {
  node: Node | null;
  onClose: () => void;
  onUpdate: (nodeId: string, data: Record<string, any>) => void;
}

const NodeConfigPanel: React.FC<NodeConfigPanelProps> = ({ node, onClose, onUpdate }) => {
  const [config, setConfig] = useState<Record<string, any>>({});

  useEffect(() => {
    if (node?.data) {
      setConfig(node.data.config || {});
    }
  }, [node]);

  if (!node) return null;

  const nodeData = node.data as { label: string; nodeType: string; category: string };

  // Get category color
  const getCategoryColor = () => {
    switch (nodeData.category) {
      case 'triggers': return 'text-green-400 border-green-500';
      case 'conditionals': return 'text-purple-400 border-purple-500';
      case 'actions': return 'text-orange-400 border-orange-500';
      default: return 'text-blue-400 border-blue-500';
    }
  };

  const handleSave = () => {
    onUpdate(node.id, { ...node.data, config });
    onClose();
  };

  // Render config fields based on node type
  const renderConfigFields = () => {
    const nodeType = nodeData.nodeType;

    // HTTP Request node
    if (nodeType === 'action_http') {
      return (
        <>
          <div className="mb-4">
            <label className="block text-sm text-ice-navy-300 mb-1">Method</label>
            <select
              value={config.method || 'GET'}
              onChange={(e) => setConfig({ ...config, method: e.target.value })}
              className="w-full bg-ice-navy-800 border border-ice-navy-600 rounded px-3 py-2 text-white"
            >
              <option value="GET">GET</option>
              <option value="POST">POST</option>
              <option value="PUT">PUT</option>
              <option value="DELETE">DELETE</option>
              <option value="PATCH">PATCH</option>
            </select>
          </div>
          <div className="mb-4">
            <label className="block text-sm text-ice-navy-300 mb-1">URL</label>
            <input
              type="text"
              value={config.url || ''}
              onChange={(e) => setConfig({ ...config, url: e.target.value })}
              placeholder="https://api.example.com/endpoint"
              className="w-full bg-ice-navy-800 border border-ice-navy-600 rounded px-3 py-2 text-white"
            />
          </div>
          <div className="mb-4">
            <label className="block text-sm text-ice-navy-300 mb-1">Headers (JSON)</label>
            <textarea
              value={config.headers || '{}'}
              onChange={(e) => setConfig({ ...config, headers: e.target.value })}
              rows={3}
              className="w-full bg-ice-navy-800 border border-ice-navy-600 rounded px-3 py-2 text-white font-mono text-sm"
            />
          </div>
          <div className="mb-4">
            <label className="block text-sm text-ice-navy-300 mb-1">Body Template</label>
            <textarea
              value={config.body || ''}
              onChange={(e) => setConfig({ ...config, body: e.target.value })}
              rows={4}
              placeholder='{"key": "{{input.value}}"}'
              className="w-full bg-ice-navy-800 border border-ice-navy-600 rounded px-3 py-2 text-white font-mono text-sm"
            />
          </div>
        </>
      );
    }

    // If/Then conditional
    if (nodeType === 'conditional_if_then') {
      return (
        <>
          <div className="mb-4">
            <label className="block text-sm text-ice-navy-300 mb-1">Condition Field</label>
            <input
              type="text"
              value={config.field || ''}
              onChange={(e) => setConfig({ ...config, field: e.target.value })}
              placeholder="input.status"
              className="w-full bg-ice-navy-800 border border-ice-navy-600 rounded px-3 py-2 text-white"
            />
          </div>
          <div className="mb-4">
            <label className="block text-sm text-ice-navy-300 mb-1">Operator</label>
            <select
              value={config.operator || 'equals'}
              onChange={(e) => setConfig({ ...config, operator: e.target.value })}
              className="w-full bg-ice-navy-800 border border-ice-navy-600 rounded px-3 py-2 text-white"
            >
              <option value="equals">Equals</option>
              <option value="not_equals">Not Equals</option>
              <option value="contains">Contains</option>
              <option value="greater_than">Greater Than</option>
              <option value="less_than">Less Than</option>
              <option value="is_empty">Is Empty</option>
              <option value="is_not_empty">Is Not Empty</option>
            </select>
          </div>
          <div className="mb-4">
            <label className="block text-sm text-ice-navy-300 mb-1">Compare Value</label>
            <input
              type="text"
              value={config.value || ''}
              onChange={(e) => setConfig({ ...config, value: e.target.value })}
              placeholder="success"
              className="w-full bg-ice-navy-800 border border-ice-navy-600 rounded px-3 py-2 text-white"
            />
          </div>
        </>
      );
    }

    // Webhook trigger
    if (nodeType === 'trigger_webhook') {
      return (
        <>
          <div className="mb-4">
            <label className="block text-sm text-ice-navy-300 mb-1">Webhook Path</label>
            <input
              type="text"
              value={config.path || ''}
              onChange={(e) => setConfig({ ...config, path: e.target.value })}
              placeholder="/my-webhook"
              className="w-full bg-ice-navy-800 border border-ice-navy-600 rounded px-3 py-2 text-white"
            />
          </div>
          <div className="mb-4">
            <label className="block text-sm text-ice-navy-300 mb-1">HTTP Method</label>
            <select
              value={config.method || 'POST'}
              onChange={(e) => setConfig({ ...config, method: e.target.value })}
              className="w-full bg-ice-navy-800 border border-ice-navy-600 rounded px-3 py-2 text-white"
            >
              <option value="POST">POST</option>
              <option value="GET">GET</option>
              <option value="PUT">PUT</option>
            </select>
          </div>
        </>
      );
    }

    // Default: show generic key-value config
    return (
      <div className="mb-4">
        <label className="block text-sm text-ice-navy-300 mb-1">Configuration (JSON)</label>
        <textarea
          value={JSON.stringify(config, null, 2)}
          onChange={(e) => {
            try {
              setConfig(JSON.parse(e.target.value));
            } catch {}
          }}
          rows={8}
          className="w-full bg-ice-navy-800 border border-ice-navy-600 rounded px-3 py-2 text-white font-mono text-sm"
        />
        <p className="text-xs text-ice-navy-400 mt-1">
          Use {'{{input.field}}'} to reference input data
        </p>
      </div>
    );
  };

  return (
    <div className="w-80 bg-ice-navy-900 border-l border-ice-navy-700 h-full overflow-y-auto">
      {/* Header */}
      <div className={`p-4 border-b border-ice-navy-700 ${getCategoryColor()}`}>
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">{nodeData.label}</h3>
          <button
            onClick={onClose}
            className="text-ice-navy-400 hover:text-white"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <p className="text-xs text-ice-navy-400 mt-1 capitalize">{nodeData.category}</p>
      </div>

      {/* Config Form */}
      <div className="p-4">
        <h4 className="text-sm font-medium text-white mb-3">Configuration</h4>
        {renderConfigFields()}
      </div>

      {/* Field Mapping Section */}
      <div className="p-4 border-t border-ice-navy-700">
        <h4 className="text-sm font-medium text-white mb-3">Input Mapping</h4>
        <p className="text-xs text-ice-navy-400 mb-2">
          Map fields from the previous node's output
        </p>
        <div className="space-y-2">
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Field name"
              className="flex-1 bg-ice-navy-800 border border-ice-navy-600 rounded px-2 py-1 text-sm text-white"
            />
            <input
              type="text"
              placeholder="{{input.field}}"
              className="flex-1 bg-ice-navy-800 border border-ice-navy-600 rounded px-2 py-1 text-sm text-white font-mono"
            />
          </div>
        </div>
        <button className="mt-2 text-xs text-ice-gold-400 hover:text-ice-gold-300">
          + Add mapping
        </button>
      </div>

      {/* Actions */}
      <div className="p-4 border-t border-ice-navy-700">
        <div className="flex gap-2">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 bg-ice-navy-700 text-white rounded hover:bg-ice-navy-600"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="flex-1 px-4 py-2 bg-ice-gold-500 text-ice-navy-900 rounded hover:bg-ice-gold-400 font-medium"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
};

export default NodeConfigPanel;
