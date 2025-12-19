import React, { useState, useEffect } from 'react';
import type { Node } from '@xyflow/react';

interface NodeConfigPanelProps {
  node: Node | null;
  onClose: () => void;
  onUpdate: (nodeId: string, data: Record<string, any>) => void;
}

interface FieldProps {
  label: string;
  value: any;
  onChange: (value: any) => void;
  placeholder?: string;
  type?: string;
}

interface SelectFieldProps {
  label: string;
  value: any;
  onChange: (value: any) => void;
  options: Array<{ value: string; label: string }>;
}

interface TextAreaFieldProps {
  label: string;
  value: any;
  onChange: (value: any) => void;
  placeholder?: string;
  rows?: number;
  mono?: boolean;
}

interface CheckboxFieldProps {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}

// Helper components
const Field: React.FC<FieldProps> = ({ label, value, onChange, placeholder, type = 'text' }) => (
  <div className="mb-4">
    <label className="block text-sm text-ice-navy-300 mb-1">{label}</label>
    <input
      type={type}
      value={value || ''}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      className="w-full bg-ice-navy-800 border border-ice-navy-600 rounded px-3 py-2 text-white focus:border-ice-gold-500 focus:outline-none"
    />
  </div>
);

const SelectField: React.FC<SelectFieldProps> = ({ label, value, onChange, options }) => (
  <div className="mb-4">
    <label className="block text-sm text-ice-navy-300 mb-1">{label}</label>
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full bg-ice-navy-800 border border-ice-navy-600 rounded px-3 py-2 text-white focus:border-ice-gold-500 focus:outline-none"
    >
      {options.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
    </select>
  </div>
);

const TextAreaField: React.FC<TextAreaFieldProps> = ({ label, value, onChange, placeholder, rows = 3, mono = false }) => (
  <div className="mb-4">
    <label className="block text-sm text-ice-navy-300 mb-1">{label}</label>
    <textarea
      value={value || ''}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      rows={rows}
      className={`w-full bg-ice-navy-800 border border-ice-navy-600 rounded px-3 py-2 text-white focus:border-ice-gold-500 focus:outline-none ${mono ? 'font-mono text-sm' : ''}`}
    />
  </div>
);

const CheckboxField: React.FC<CheckboxFieldProps> = ({ label, checked, onChange }) => (
  <div className="mb-4 flex items-center gap-2">
    <input
      type="checkbox"
      checked={checked || false}
      onChange={(e) => onChange(e.target.checked)}
      className="w-4 h-4 rounded border-ice-navy-600 bg-ice-navy-800 text-ice-gold-500 focus:ring-ice-gold-500"
    />
    <label className="text-sm text-ice-navy-300">{label}</label>
  </div>
);

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

  // Helper function to update config
  const updateConfig = (key: string, value: any) => {
    setConfig(prev => ({ ...prev, [key]: value }));
  };

  // Render config fields based on node type
  const renderConfigFields = () => {
    const nodeType = nodeData.nodeType;

    // === TRIGGERS ===
    if (nodeType === 'trigger_webhook') {
      return (
        <>
          <Field label="Webhook Path" value={config.path} onChange={(v) => updateConfig('path', v)} placeholder="/my-webhook" />
          <SelectField label="HTTP Method" value={config.method || 'POST'} onChange={(v) => updateConfig('method', v)}
            options={[{ value: 'POST', label: 'POST' }, { value: 'GET', label: 'GET' }, { value: 'PUT', label: 'PUT' }]} />
          <CheckboxField label="Require Authentication" checked={config.requireAuth} onChange={(v) => updateConfig('requireAuth', v)} />
        </>
      );
    }

    if (nodeType === 'trigger_schedule') {
      return (
        <>
          <Field label="Cron Expression" value={config.cron} onChange={(v) => updateConfig('cron', v)} placeholder="0 9 * * *" />
          <Field label="Timezone" value={config.timezone || 'UTC'} onChange={(v) => updateConfig('timezone', v)} placeholder="UTC" />
          <p className="text-xs text-ice-navy-400 mt-1">Format: minute hour day month weekday</p>
        </>
      );
    }

    if (nodeType === 'trigger_manual') {
      return (
        <p className="text-ice-navy-400 text-sm">This trigger is activated manually via the Run button.</p>
      );
    }

    if (nodeType === 'trigger_mock_data') {
      return (
        <>
          <TextAreaField
            label="Mock Data (JSON)"
            value={config.mockData}
            onChange={(v) => updateConfig('mockData', v)}
            placeholder='{"id": 1, "name": "Test User", "status": "active"}'
            rows={8}
            mono
          />
          <p className="text-xs text-ice-navy-400 mt-1">Enter JSON data to use as input for testing the workflow</p>
          <Field label="Repeat Count" value={config.repeatCount || '1'} onChange={(v) => updateConfig('repeatCount', v)} placeholder="1" type="number" />
          <p className="text-xs text-ice-navy-400 mt-1">Number of times to emit the mock data (for testing loops)</p>
        </>
      );
    }

    // === TRANSFORMS ===
    if (nodeType === 'transform_filter' || nodeType === 'Filter') {
      return (
        <>
          <Field label="Field to Check" value={config.field} onChange={(v) => updateConfig('field', v)} placeholder="data.status" />
          <SelectField label="Condition" value={config.condition || 'equals'} onChange={(v) => updateConfig('condition', v)}
            options={[
              { value: 'equals', label: 'Equals' },
              { value: 'not_equals', label: 'Not Equals' },
              { value: 'contains', label: 'Contains' },
              { value: 'not_contains', label: 'Does Not Contain' },
              { value: 'greater_than', label: 'Greater Than' },
              { value: 'less_than', label: 'Less Than' },
              { value: 'is_empty', label: 'Is Empty' },
              { value: 'is_not_empty', label: 'Is Not Empty' },
              { value: 'regex', label: 'Matches Regex' },
            ]} />
          <Field label="Compare Value" value={config.value} onChange={(v) => updateConfig('value', v)} placeholder="active" />
        </>
      );
    }

    if (nodeType === 'transform_map' || nodeType === 'Map') {
      return (
        <>
          <TextAreaField label="Field Mappings" value={config.mappings} onChange={(v) => updateConfig('mappings', v)}
            placeholder="newField: {{input.oldField}}&#10;status: {{input.data.status}}" rows={5} />
          <p className="text-xs text-ice-navy-400 mt-1">One mapping per line: outputField: {'{{input.path}}'}</p>
        </>
      );
    }

    if (nodeType === 'transform_delay' || nodeType === 'Delay') {
      return (
        <>
          <Field label="Delay (seconds)" value={config.seconds} onChange={(v) => updateConfig('seconds', v)} placeholder="5" type="number" />
        </>
      );
    }

    // === CONDITIONALS ===
    if (nodeType === 'conditional_if_then') {
      return (
        <>
          <Field label="Field to Check" value={config.field} onChange={(v) => updateConfig('field', v)} placeholder="input.status" />
          <SelectField label="Operator" value={config.operator || 'equals'} onChange={(v) => updateConfig('operator', v)}
            options={[
              { value: 'equals', label: 'Equals' },
              { value: 'not_equals', label: 'Not Equals' },
              { value: 'contains', label: 'Contains' },
              { value: 'greater_than', label: 'Greater Than' },
              { value: 'less_than', label: 'Less Than' },
              { value: 'is_empty', label: 'Is Empty' },
              { value: 'is_not_empty', label: 'Is Not Empty' },
            ]} />
          <Field label="Compare Value" value={config.value} onChange={(v) => updateConfig('value', v)} placeholder="success" />
        </>
      );
    }

    if (nodeType === 'conditional_switch') {
      return (
        <>
          <Field label="Switch Field" value={config.field} onChange={(v) => updateConfig('field', v)} placeholder="input.type" />
          <Field label="Case 1 Value" value={config.case1} onChange={(v) => updateConfig('case1', v)} placeholder="type_a" />
          <Field label="Case 2 Value" value={config.case2} onChange={(v) => updateConfig('case2', v)} placeholder="type_b" />
          <Field label="Case 3 Value" value={config.case3} onChange={(v) => updateConfig('case3', v)} placeholder="type_c" />
          <p className="text-xs text-ice-navy-400 mt-1">Unmatched values go to "default" output</p>
        </>
      );
    }

    if (nodeType === 'conditional_for_each') {
      return (
        <>
          <Field label="Array Field" value={config.arrayField} onChange={(v) => updateConfig('arrayField', v)} placeholder="input.items" />
          <Field label="Item Variable Name" value={config.itemVar || 'item'} onChange={(v) => updateConfig('itemVar', v)} placeholder="item" />
        </>
      );
    }

    // === ACTIONS ===
    if (nodeType === 'action_http') {
      return (
        <>
          <SelectField label="Method" value={config.method || 'GET'} onChange={(v) => updateConfig('method', v)}
            options={[
              { value: 'GET', label: 'GET' },
              { value: 'POST', label: 'POST' },
              { value: 'PUT', label: 'PUT' },
              { value: 'DELETE', label: 'DELETE' },
              { value: 'PATCH', label: 'PATCH' },
            ]} />
          <Field label="URL" value={config.url} onChange={(v) => updateConfig('url', v)} placeholder="https://api.example.com/endpoint" />
          <TextAreaField label="Headers (JSON)" value={config.headers} onChange={(v) => updateConfig('headers', v)} placeholder='{"Content-Type": "application/json"}' rows={3} mono />
          <TextAreaField label="Body Template" value={config.body} onChange={(v) => updateConfig('body', v)} placeholder='{"key": "{{input.value}}"}' rows={4} mono />
        </>
      );
    }

    if (nodeType === 'action_log') {
      return (
        <>
          <SelectField label="Log Level" value={config.level || 'info'} onChange={(v) => updateConfig('level', v)}
            options={[
              { value: 'debug', label: 'Debug' },
              { value: 'info', label: 'Info' },
              { value: 'warn', label: 'Warning' },
              { value: 'error', label: 'Error' },
            ]} />
          <Field label="Message Template" value={config.message} onChange={(v) => updateConfig('message', v)} placeholder="Processing: {{input.id}}" />
        </>
      );
    }

    // Default fallback - show helpful message
    return (
      <div className="text-ice-navy-400 text-sm">
        <p>Configuration for this node type coming soon.</p>
        <p className="mt-2">Node Type: <code className="text-ice-gold-400">{nodeType}</code></p>
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
