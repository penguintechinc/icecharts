/**
 * ConnectorConfigPanel - Schema-driven config form for connector nodes
 *
 * Renders configuration forms dynamically based on config_schema definitions
 * from connector manifests. Supports all field types: string, number, select,
 * multiselect, textarea, checkbox.
 */

import React from 'react';
import type { ConfigField } from '../../../types/connector';

interface ConnectorConfigPanelProps {
  /** Configuration schema from connector manifest */
  schema: ConfigField[];
  /** Current configuration values */
  config: Record<string, unknown>;
  /** Callback when config changes */
  onConfigChange: (key: string, value: unknown) => void;
  /** Connector color for styling */
  connectorColor?: string;
}

/**
 * Field wrapper with label and optional description
 */
const FieldWrapper: React.FC<{
  label: string;
  description?: string;
  required?: boolean;
  supportsVariables?: boolean;
  children: React.ReactNode;
}> = ({ label, description, required, supportsVariables, children }) => (
  <div className="mb-4">
    <label className="block text-sm text-ice-navy-300 mb-1">
      {label}
      {required && <span className="text-red-400 ml-1">*</span>}
      {supportsVariables && (
        <span className="ml-2 text-xs text-ice-navy-500" title="Supports {{variable}} interpolation">
          {'{{...}}'}
        </span>
      )}
    </label>
    {children}
    {description && (
      <p className="text-xs text-ice-navy-500 mt-1">{description}</p>
    )}
  </div>
);

/**
 * String input field
 */
const StringField: React.FC<{
  field: ConfigField;
  value: string;
  onChange: (value: string) => void;
}> = ({ field, value, onChange }) => (
  <FieldWrapper
    label={field.label}
    description={field.description}
    required={field.required}
    supportsVariables={field.supports_variables}
  >
    <input
      type="text"
      value={value || ''}
      onChange={(e) => onChange(e.target.value)}
      placeholder={field.placeholder}
      className="w-full bg-ice-navy-800 border border-ice-navy-600 rounded px-3 py-2 text-white focus:border-ice-gold-500 focus:outline-none"
    />
  </FieldWrapper>
);

/**
 * Number input field
 */
const NumberField: React.FC<{
  field: ConfigField;
  value: number | undefined;
  onChange: (value: number | undefined) => void;
}> = ({ field, value, onChange }) => (
  <FieldWrapper
    label={field.label}
    description={field.description}
    required={field.required}
  >
    <input
      type="number"
      value={value ?? (field.default as number) ?? ''}
      onChange={(e) => onChange(e.target.value ? Number(e.target.value) : undefined)}
      placeholder={field.placeholder}
      className="w-full bg-ice-navy-800 border border-ice-navy-600 rounded px-3 py-2 text-white focus:border-ice-gold-500 focus:outline-none"
    />
  </FieldWrapper>
);

/**
 * Select dropdown field
 */
const SelectField: React.FC<{
  field: ConfigField;
  value: string;
  onChange: (value: string) => void;
}> = ({ field, value, onChange }) => (
  <FieldWrapper
    label={field.label}
    description={field.description}
    required={field.required}
  >
    <select
      value={value || (field.default as string) || ''}
      onChange={(e) => onChange(e.target.value)}
      className="w-full bg-ice-navy-800 border border-ice-navy-600 rounded px-3 py-2 text-white focus:border-ice-gold-500 focus:outline-none"
    >
      <option value="">Select...</option>
      {field.options?.map((opt) => (
        <option key={opt} value={opt}>
          {opt}
        </option>
      ))}
    </select>
  </FieldWrapper>
);

/**
 * Multi-select field with checkboxes
 */
const MultiSelectField: React.FC<{
  field: ConfigField;
  value: string[];
  onChange: (value: string[]) => void;
}> = ({ field, value, onChange }) => {
  const selected = value || (field.default as string[]) || [];

  const toggleOption = (opt: string) => {
    if (selected.includes(opt)) {
      onChange(selected.filter((v) => v !== opt));
    } else {
      onChange([...selected, opt]);
    }
  };

  return (
    <FieldWrapper
      label={field.label}
      description={field.description}
      required={field.required}
    >
      <div className="space-y-1 bg-ice-navy-800 border border-ice-navy-600 rounded p-2">
        {field.options?.map((opt) => (
          <label
            key={opt}
            className="flex items-center gap-2 py-1 px-2 hover:bg-ice-navy-700 rounded cursor-pointer"
          >
            <input
              type="checkbox"
              checked={selected.includes(opt)}
              onChange={() => toggleOption(opt)}
              className="w-4 h-4 rounded border-ice-navy-600 bg-ice-navy-800 text-ice-gold-500 focus:ring-ice-gold-500"
            />
            <span className="text-sm text-white">{opt}</span>
          </label>
        ))}
      </div>
    </FieldWrapper>
  );
};

/**
 * Textarea field for longer text input
 */
const TextareaField: React.FC<{
  field: ConfigField;
  value: string;
  onChange: (value: string) => void;
}> = ({ field, value, onChange }) => (
  <FieldWrapper
    label={field.label}
    description={field.description}
    required={field.required}
    supportsVariables={field.supports_variables}
  >
    <textarea
      value={value || ''}
      onChange={(e) => onChange(e.target.value)}
      placeholder={field.placeholder}
      rows={4}
      className="w-full bg-ice-navy-800 border border-ice-navy-600 rounded px-3 py-2 text-white focus:border-ice-gold-500 focus:outline-none resize-y min-h-[80px]"
    />
  </FieldWrapper>
);

/**
 * Checkbox field for boolean values
 */
const CheckboxField: React.FC<{
  field: ConfigField;
  value: boolean;
  onChange: (value: boolean) => void;
}> = ({ field, value, onChange }) => {
  const checked = value ?? (field.default as boolean) ?? false;

  return (
    <div className="mb-4">
      <label className="flex items-center gap-2 cursor-pointer group">
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          className="w-4 h-4 rounded border-ice-navy-600 bg-ice-navy-800 text-ice-gold-500 focus:ring-ice-gold-500"
        />
        <span className="text-sm text-ice-navy-300 group-hover:text-white">
          {field.label}
          {field.required && <span className="text-red-400 ml-1">*</span>}
        </span>
      </label>
      {field.description && (
        <p className="text-xs text-ice-navy-500 mt-1 ml-6">{field.description}</p>
      )}
    </div>
  );
};

/**
 * Render a single config field based on its type
 */
const ConfigFieldRenderer: React.FC<{
  field: ConfigField;
  value: unknown;
  onChange: (value: unknown) => void;
}> = ({ field, value, onChange }) => {
  switch (field.type) {
    case 'string':
      return (
        <StringField
          field={field}
          value={value as string}
          onChange={onChange}
        />
      );
    case 'number':
      return (
        <NumberField
          field={field}
          value={value as number | undefined}
          onChange={onChange}
        />
      );
    case 'select':
      return (
        <SelectField
          field={field}
          value={value as string}
          onChange={onChange}
        />
      );
    case 'multiselect':
      return (
        <MultiSelectField
          field={field}
          value={value as string[]}
          onChange={onChange}
        />
      );
    case 'textarea':
      return (
        <TextareaField
          field={field}
          value={value as string}
          onChange={onChange}
        />
      );
    case 'checkbox':
      return (
        <CheckboxField
          field={field}
          value={value as boolean}
          onChange={onChange}
        />
      );
    default:
      // Fallback to string field for unknown types
      return (
        <StringField
          field={field}
          value={value as string}
          onChange={onChange}
        />
      );
  }
};

/**
 * ConnectorConfigPanel - Main component
 *
 * Renders a configuration form for connector nodes based on their schema.
 */
export const ConnectorConfigPanel: React.FC<ConnectorConfigPanelProps> = ({
  schema,
  config,
  onConfigChange,
  connectorColor,
}) => {
  if (!schema || schema.length === 0) {
    return (
      <div className="text-ice-navy-400 text-sm">
        <p>This node has no configuration options.</p>
      </div>
    );
  }

  return (
    <div className="space-y-1">
      {connectorColor && (
        <div
          className="h-1 rounded-full mb-4"
          style={{ backgroundColor: connectorColor }}
        />
      )}
      {schema.map((field) => (
        <ConfigFieldRenderer
          key={field.field}
          field={field}
          value={config[field.field]}
          onChange={(value) => onConfigChange(field.field, value)}
        />
      ))}
    </div>
  );
};

export default ConnectorConfigPanel;
