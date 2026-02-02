/**
 * React hooks for IceCharts Connector Framework
 *
 * Provides hooks for fetching and managing connector data in the UI.
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import api from '../lib/api';
import type {
  Connector,
  ConnectorNode,
  ConnectorsResponse,
  ConnectorNodesResponse,
} from '../types/connector';

/**
 * Hook state for useConnectors
 */
interface UseConnectorsState {
  /** List of available connectors */
  connectors: Connector[];
  /** Loading state */
  loading: boolean;
  /** Error message if fetch failed */
  error: string | null;
  /** Refetch connectors */
  refetch: () => Promise<void>;
}

/**
 * Hook to fetch available connectors.
 *
 * @returns {UseConnectorsState} Connector data and state
 *
 * @example
 * ```tsx
 * const { connectors, loading, error } = useConnectors();
 *
 * if (loading) return <Spinner />;
 * if (error) return <Error message={error} />;
 *
 * return connectors.map(c => <ConnectorCard connector={c} />);
 * ```
 */
export function useConnectors(): UseConnectorsState {
  const [connectors, setConnectors] = useState<Connector[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchConnectors = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.get<ConnectorsResponse>('/connectors');
      setConnectors(response.data.connectors || []);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load connectors';
      setError(message);
      console.error('Failed to fetch connectors:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchConnectors();
  }, [fetchConnectors]);

  return {
    connectors,
    loading,
    error,
    refetch: fetchConnectors,
  };
}

/**
 * Hook state for useConnectorNodes
 */
interface UseConnectorNodesState {
  /** List of all connector nodes */
  nodes: ConnectorNode[];
  /** Nodes grouped by connector */
  nodesByConnector: Record<string, ConnectorNode[]>;
  /** Nodes grouped by category */
  nodesByCategory: Record<string, ConnectorNode[]>;
  /** Loading state */
  loading: boolean;
  /** Error message if fetch failed */
  error: string | null;
  /** Refetch nodes */
  refetch: () => Promise<void>;
}

/**
 * Hook to fetch all connector nodes across all connectors.
 *
 * @param category Optional category filter ('triggers' | 'actions' | 'transforms')
 * @returns {UseConnectorNodesState} Node data and state
 *
 * @example
 * ```tsx
 * const { nodes, nodesByConnector, loading } = useConnectorNodes();
 *
 * // Render nodes grouped by connector
 * Object.entries(nodesByConnector).map(([connectorId, nodes]) => (
 *   <ConnectorSection key={connectorId} nodes={nodes} />
 * ));
 * ```
 */
export function useConnectorNodes(
  category?: 'triggers' | 'actions' | 'transforms'
): UseConnectorNodesState {
  const [nodes, setNodes] = useState<ConnectorNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchNodes = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const url = category
        ? `/connectors/nodes?category=${category}`
        : '/connectors/nodes';

      const response = await api.get<ConnectorNodesResponse>(url);
      setNodes(response.data.nodes || []);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load connector nodes';
      setError(message);
      console.error('Failed to fetch connector nodes:', err);
    } finally {
      setLoading(false);
    }
  }, [category]);

  useEffect(() => {
    fetchNodes();
  }, [fetchNodes]);

  // Group nodes by connector
  const nodesByConnector = useMemo(() => {
    return nodes.reduce<Record<string, ConnectorNode[]>>((acc, node) => {
      const connectorId = node.connector_id;
      if (!acc[connectorId]) {
        acc[connectorId] = [];
      }
      acc[connectorId].push(node);
      return acc;
    }, {});
  }, [nodes]);

  // Group nodes by category
  const nodesByCategory = useMemo(() => {
    return nodes.reduce<Record<string, ConnectorNode[]>>((acc, node) => {
      const cat = node.category;
      if (!acc[cat]) {
        acc[cat] = [];
      }
      acc[cat].push(node);
      return acc;
    }, {});
  }, [nodes]);

  return {
    nodes,
    nodesByConnector,
    nodesByCategory,
    loading,
    error,
    refetch: fetchNodes,
  };
}

/**
 * Hook to get a single connector by ID
 */
export function useConnector(connectorId: string | null) {
  const { connectors, loading, error } = useConnectors();

  const connector = useMemo(() => {
    if (!connectorId) return null;
    return connectors.find((c) => c.id === connectorId) || null;
  }, [connectors, connectorId]);

  return {
    connector,
    loading,
    error,
  };
}

/**
 * Hook to get config schema for a specific node type
 */
export function useConnectorNodeSchema(nodeType: string | null) {
  const { nodes, loading, error } = useConnectorNodes();

  const node = useMemo(() => {
    if (!nodeType) return null;
    return nodes.find((n) => n.node_type === nodeType) || null;
  }, [nodes, nodeType]);

  return {
    node,
    configSchema: node?.config_schema || [],
    inputs: node?.inputs || [],
    outputs: node?.outputs || [],
    loading,
    error,
  };
}

/**
 * Build palette nodes from connectors for the PlaybookEditor.
 *
 * This transforms connector data into the format expected by the editor's node palette.
 */
export function buildPaletteNodesFromConnectors(connectors: Connector[]): {
  triggers: Array<{ id: string; label: string; icon: string; description: string; connectorId: string; connectorColor: string }>;
  actions: Array<{ id: string; label: string; icon: string; description: string; connectorId: string; connectorColor: string }>;
  transforms: Array<{ id: string; label: string; icon: string; description: string; connectorId: string; connectorColor: string }>;
} {
  const result = {
    triggers: [] as Array<{ id: string; label: string; icon: string; description: string; connectorId: string; connectorColor: string }>,
    actions: [] as Array<{ id: string; label: string; icon: string; description: string; connectorId: string; connectorColor: string }>,
    transforms: [] as Array<{ id: string; label: string; icon: string; description: string; connectorId: string; connectorColor: string }>,
  };

  for (const connector of connectors) {
    // Add triggers
    for (const trigger of connector.triggers) {
      result.triggers.push({
        id: `trigger_${connector.id}_${trigger.id}`,
        label: `${connector.name}: ${trigger.name}`,
        icon: trigger.icon || connector.icon,
        description: trigger.description,
        connectorId: connector.id,
        connectorColor: connector.color,
      });
    }

    // Add actions
    for (const action of connector.actions) {
      result.actions.push({
        id: `action_${connector.id}_${action.id}`,
        label: `${connector.name}: ${action.name}`,
        icon: action.icon || connector.icon,
        description: action.description,
        connectorId: connector.id,
        connectorColor: connector.color,
      });
    }

    // Add transforms
    for (const transform of connector.transforms) {
      result.transforms.push({
        id: `transform_${connector.id}_${transform.id}`,
        label: `${connector.name}: ${transform.name}`,
        icon: transform.icon || connector.icon,
        description: transform.description,
        connectorId: connector.id,
        connectorColor: connector.color,
      });
    }
  }

  return result;
}
