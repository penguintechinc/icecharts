/**
 * TypeScript types for IceCharts Connector Framework
 *
 * These types mirror the backend connector manifest schema and are used
 * throughout the frontend for type-safe connector handling.
 */

/**
 * Configuration field schema for UI rendering
 */
export interface ConfigField {
  /** Field identifier (key in config dict) */
  field: string;
  /** Field type for rendering */
  type: 'string' | 'number' | 'select' | 'multiselect' | 'textarea' | 'checkbox';
  /** Human-readable label */
  label: string;
  /** Placeholder text for input fields */
  placeholder?: string;
  /** Available options for select/multiselect fields */
  options?: string[];
  /** Whether the field is required */
  required?: boolean;
  /** Default value */
  default?: unknown;
  /** Whether the field supports {{variable}} interpolation */
  supports_variables?: boolean;
  /** Help text for the field */
  description?: string;
}

/**
 * Input/output port definition for workflow nodes
 */
export interface PortDefinition {
  /** Port identifier (e.g., "in", "out", "true", "false") */
  name: string;
  /** Data type hint */
  type: 'any' | 'string' | 'number' | 'bool' | 'object' | 'array';
  /** Human-readable description */
  description?: string;
  /** Whether this input port is required */
  required?: boolean;
}

/**
 * Trigger definition from connector manifest
 */
export interface TriggerDefinition {
  /** Trigger identifier */
  id: string;
  /** Display name */
  name: string;
  /** Human-readable description */
  description: string;
  /** Emoji or icon identifier */
  icon?: string;
  /** Output port definitions */
  outputs: PortDefinition[];
  /** Configuration field schemas */
  config_schema: ConfigField[];
}

/**
 * Action definition from connector manifest
 */
export interface ActionDefinition {
  /** Action identifier */
  id: string;
  /** Display name */
  name: string;
  /** Human-readable description */
  description: string;
  /** Emoji or icon identifier */
  icon?: string;
  /** Input port definitions */
  inputs: PortDefinition[];
  /** Output port definitions */
  outputs: PortDefinition[];
  /** Configuration field schemas */
  config_schema: ConfigField[];
}

/**
 * Transform definition from connector manifest
 */
export interface TransformDefinition {
  /** Transform identifier */
  id: string;
  /** Display name */
  name: string;
  /** Human-readable description */
  description: string;
  /** Emoji or icon identifier */
  icon?: string;
  /** Input port definitions */
  inputs: PortDefinition[];
  /** Output port definitions */
  outputs: PortDefinition[];
  /** Configuration field schemas */
  config_schema: ConfigField[];
}

/**
 * Complete connector definition
 */
export interface Connector {
  /** Unique connector identifier */
  id: string;
  /** Display name */
  name: string;
  /** Human-readable description */
  description: string;
  /** Emoji or icon identifier */
  icon: string;
  /** UI color (hex code) */
  color: string;
  /** Connector version */
  version: string;
  /** Vendor category: 'penguintech' for internal products, 'external' for third-party */
  vendor?: 'penguintech' | 'external';
  /** Trigger definitions */
  triggers: TriggerDefinition[];
  /** Action definitions */
  actions: ActionDefinition[];
  /** Transform definitions */
  transforms: TransformDefinition[];
}

/**
 * Connector node definition (flattened for UI rendering)
 */
export interface ConnectorNode {
  /** Full node type (e.g., "trigger_waddlebot_command") */
  node_type: string;
  /** Node category */
  category: 'triggers' | 'actions' | 'transforms';
  /** Display name */
  name: string;
  /** Human-readable description */
  description: string;
  /** Emoji or icon identifier */
  icon: string;
  /** Input port definitions */
  inputs: PortDefinition[];
  /** Output port definitions */
  outputs: PortDefinition[];
  /** Configuration field schemas */
  config_schema: ConfigField[];
  /** Parent connector ID */
  connector_id: string;
  /** Parent connector name */
  connector_name?: string;
  /** Parent connector color */
  connector_color: string;
}

/**
 * Connector configuration stored per-user
 */
export interface ConnectorConfig {
  /** Connector identifier */
  connector_id: string;
  /** Base URL for API calls */
  base_url: string;
  /** Authentication type */
  auth_type: 'none' | 'api_key' | 'oauth';
  /** API key (for api_key auth) - should be masked in UI */
  api_key?: string;
  /** Whether the connector is currently active/enabled */
  is_active: boolean;
  /** Last successful connection test timestamp */
  last_verified?: string;
}

/**
 * API response for listing connectors
 */
export interface ConnectorsResponse {
  connectors: Connector[];
}

/**
 * API response for getting a single connector
 */
export interface ConnectorResponse {
  connector: Connector;
}

/**
 * API response for listing connector nodes
 */
export interface ConnectorNodesResponse {
  nodes: ConnectorNode[];
}

/**
 * Helper to get node handles from a connector node definition
 */
export function getConnectorNodeHandles(node: ConnectorNode): {
  inputs: string[];
  outputs: string[];
} {
  return {
    inputs: node.inputs.map((p) => p.name),
    outputs: node.outputs.map((p) => p.name),
  };
}

/**
 * Helper to determine if a node type belongs to a connector
 */
export function isConnectorNode(nodeType: string): boolean {
  // Connector nodes follow the pattern: {category}_{connector_id}_{action_id}
  const parts = nodeType.split('_');
  if (parts.length < 3) return false;

  const category = parts[0];
  return ['trigger', 'action', 'transform'].includes(category);
}

/**
 * Extract connector ID from a connector node type
 */
export function getConnectorIdFromNodeType(nodeType: string): string | null {
  const parts = nodeType.split('_');
  if (parts.length < 3) return null;

  // Format: {category}_{connector_id}_{action_id}
  // e.g., "trigger_waddlebot_command" -> "waddlebot"
  return parts[1];
}
