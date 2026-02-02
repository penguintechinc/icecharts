/* eslint-disable react-refresh/only-export-components */
/**
 * IceRunsNodes - IceRuns action nodes for IceStreams playbooks
 *
 * Provides:
 * - IceRunExecuteNode: Execute a serverless function
 * - IceRunWaitNode: Wait for async execution completion
 * - IceRunsNodeTypes: Node type definitions for registration
 */

import React from 'react';

/**
 * IceRunExecuteNode - Execute IceRun function node config panel
 */
export const IceRunExecuteConfigPanel: React.FC<{ data: any; onChange: (data: any) => void }> = ({
  data,
  onChange,
}) => {
  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-ice-navy-300 mb-2">
          Function
        </label>
        <select
          value={data.function_id || ''}
          onChange={(e) => onChange({ ...data, function_id: e.target.value })}
          className="w-full px-4 py-2 bg-ice-navy-700 text-white rounded-lg border border-ice-navy-600 focus:outline-none focus:border-purple-500"
        >
          <option value="">Select a function...</option>
          {/* TODO: Populate from API */}
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-ice-navy-300 mb-2">
          Input Mode
        </label>
        <select
          value={data.input_mode || 'from_previous'}
          onChange={(e) => onChange({ ...data, input_mode: e.target.value })}
          className="w-full px-4 py-2 bg-ice-navy-700 text-white rounded-lg border border-ice-navy-600 focus:outline-none focus:border-purple-500"
        >
          <option value="from_previous">From Previous Node</option>
          <option value="static">Static JSON</option>
        </select>
      </div>

      {data.input_mode === 'static' && (
        <div>
          <label className="block text-sm font-medium text-ice-navy-300 mb-2">
            Input JSON
          </label>
          <textarea
            value={data.input_json || '{}'}
            onChange={(e) => onChange({ ...data, input_json: e.target.value })}
            className="w-full px-4 py-2 bg-ice-navy-700 text-white rounded-lg border border-ice-navy-600 focus:outline-none focus:border-purple-500 font-mono text-sm"
            rows={6}
          />
        </div>
      )}

      <div>
        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={data.async || false}
            onChange={(e) => onChange({ ...data, async: e.target.checked })}
            className="form-checkbox h-5 w-5 text-purple-600"
          />
          <span className="text-white text-sm">Execute asynchronously</span>
        </label>
      </div>

      <div>
        <label className="block text-sm font-medium text-ice-navy-300 mb-2">
          Timeout Override (seconds)
        </label>
        <input
          type="number"
          min="1"
          max="900"
          value={data.timeout_override || ''}
          onChange={(e) => onChange({ ...data, timeout_override: parseInt(e.target.value) || undefined })}
          className="w-full px-4 py-2 bg-ice-navy-700 text-white rounded-lg border border-ice-navy-600 focus:outline-none focus:border-purple-500"
          placeholder="Use function default"
        />
      </div>
    </div>
  );
};

/**
 * IceRunWaitNode - Wait for async execution config panel
 */
export const IceRunWaitConfigPanel: React.FC<{ data: any; onChange: (data: any) => void }> = ({
  data,
  onChange,
}) => {
  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-ice-navy-300 mb-2">
          Activation ID Source
        </label>
        <select
          value={data.activation_id_source || 'from_previous'}
          onChange={(e) => onChange({ ...data, activation_id_source: e.target.value })}
          className="w-full px-4 py-2 bg-ice-navy-700 text-white rounded-lg border border-ice-navy-600 focus:outline-none focus:border-purple-500"
        >
          <option value="from_previous">From Previous Node</option>
          <option value="manual">Manual Entry</option>
        </select>
      </div>

      {data.activation_id_source === 'manual' && (
        <div>
          <label className="block text-sm font-medium text-ice-navy-300 mb-2">
            Activation ID
          </label>
          <input
            type="text"
            value={data.activation_id || ''}
            onChange={(e) => onChange({ ...data, activation_id: e.target.value })}
            className="w-full px-4 py-2 bg-ice-navy-700 text-white rounded-lg border border-ice-navy-600 focus:outline-none focus:border-purple-500 font-mono"
            placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
          />
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-ice-navy-300 mb-2">
          Timeout (seconds)
        </label>
        <input
          type="number"
          min="1"
          max="900"
          value={data.timeout_seconds || 300}
          onChange={(e) => onChange({ ...data, timeout_seconds: parseInt(e.target.value) })}
          className="w-full px-4 py-2 bg-ice-navy-700 text-white rounded-lg border border-ice-navy-600 focus:outline-none focus:border-purple-500"
        />
      </div>
    </div>
  );
};

/**
 * Node type definitions for registration
 */
export const IceRunsNodeTypes = {
  'iceruns.execute': {
    category: 'iceruns',
    label: 'Execute IceRun',
    icon: 'FaCode',
    color: '#9333ea', // Purple
    description: 'Execute a serverless function',
    ConfigPanel: IceRunExecuteConfigPanel,
  },
  'iceruns.wait_for_completion': {
    category: 'iceruns',
    label: 'Wait for IceRun',
    icon: 'FaClock',
    color: '#9333ea', // Purple
    description: 'Wait for async IceRun completion',
    ConfigPanel: IceRunWaitConfigPanel,
  },
};
