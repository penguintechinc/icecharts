/**
 * Hook for Elder API integration and entity import functionality.
 *
 * Provides utilities to connect to Elder instances, browse entities,
 * and import them as shapes into IceCharts drawings.
 */

import { useState, useCallback, useRef } from 'react';
import apiClient from '../lib/api';

/**
 * Elder entity type for API responses
 */
export interface ElderEntity {
  id: number;
  unique_id: number;
  name: string;
  entity_type: string;
  description?: string;
  metadata?: Record<string, unknown>;
  owner_id?: number;
  organization_id?: number;
}

/**
 * Elder dependency/relationship type
 */
export interface ElderRelationship {
  id: number;
  source_entity_id: number;
  target_entity_id: number;
  dependency_type: string;
  description?: string;
  strength?: number;
}

/**
 * IceCharts node created from Elder entity
 */
export interface ImportedNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: Record<string, unknown>;
  style?: Record<string, unknown>;
}

/**
 * IceCharts connector created from Elder relationship
 */
export interface ImportedConnector {
  id: string;
  source: string;
  target: string;
  type: string;
  data?: Record<string, unknown>;
  animated: boolean;
  label?: string;
}

/**
 * Import result with nodes and connectors
 */
export interface ImportResult {
  nodes: ImportedNode[];
  connectors: ImportedConnector[];
  entityCount: number;
  relationshipCount: number;
}

/**
 * State for Elder import operations
 */
interface ElderImportState {
  isLoading: boolean;
  error: string | null;
  entities: ElderEntity[];
  selectedEntities: Set<number>;
  isConnected: boolean;
}

/**
 * Hook for Elder API integration
 *
 * @example
 * ```tsx
 * const {
 *   validateConnection,
 *   fetchEntities,
 *   importEntities,
 *   isLoading,
 *   error,
 *   entities,
 *   selectedEntities,
 *   toggleEntitySelection,
 * } = useElderImport();
 * ```
 */
export const useElderImport = () => {
  // State management
  const [state, setState] = useState<ElderImportState>({
    isLoading: false,
    error: null,
    entities: [],
    selectedEntities: new Set(),
    isConnected: false,
  });

  // Use ref to store current connection details
  const connectionRef = useRef<{
    baseUrl: string;
    apiKey: string;
    orgId: number;
  } | null>(null);

  /**
   * Validate connection to Elder instance
   */
  const validateConnection = useCallback(
    async (baseUrl: string, apiKey: string): Promise<boolean> => {
      setState((prev) => ({ ...prev, isLoading: true, error: null }));

      try {
        const response = await apiClient.post('/elder/validate-connection', {
          base_url: baseUrl,
          api_key: apiKey,
        });

        if (response.data.success) {
          setState((prev) => ({ ...prev, isConnected: true }));
          return true;
        } else {
          setState((prev) => ({
            ...prev,
            error: response.data.error || 'Connection validation failed',
            isConnected: false,
          }));
          return false;
        }
      } catch (err: unknown) {
        const errorMessage = err instanceof Error
          ? err.message
          : 'Failed to validate connection';
        setState((prev) => ({
          ...prev,
          error: errorMessage,
          isConnected: false,
        }));
        return false;
      } finally {
        setState((prev) => ({ ...prev, isLoading: false }));
      }
    },
    []
  );

  /**
   * Fetch entities from Elder
   */
  const fetchEntities = useCallback(
    async (
      baseUrl: string,
      apiKey: string,
      orgId: number,
      entityType?: string
    ): Promise<ElderEntity[]> => {
      setState((prev) => ({ ...prev, isLoading: true, error: null }));

      try {
        // Store connection details for later use
        connectionRef.current = { baseUrl, apiKey, orgId };

        const params = new URLSearchParams({
          base_url: baseUrl,
          api_key: apiKey,
          org_id: orgId.toString(),
          limit: '1000',
        });

        if (entityType) {
          params.append('entity_type', entityType);
        }

        const response = await apiClient.get(`/elder/entities?${params}`);

        if (response.data.success) {
          setState((prev) => ({
            ...prev,
            entities: response.data.entities,
            selectedEntities: new Set(),
          }));
          return response.data.entities;
        } else {
          setState((prev) => ({
            ...prev,
            error: response.data.error || 'Failed to fetch entities',
          }));
          return [];
        }
      } catch (err: unknown) {
        const errorMessage = err instanceof Error
          ? err.message
          : 'Failed to fetch entities';
        setState((prev) => ({ ...prev, error: errorMessage }));
        return [];
      } finally {
        setState((prev) => ({ ...prev, isLoading: false }));
      }
    },
    []
  );

  /**
   * Fetch relationships/dependencies from Elder
   */
  const fetchRelationships = useCallback(
    async (
      baseUrl: string,
      apiKey: string,
      orgId: number
    ): Promise<ElderRelationship[]> => {
      try {
        const params = new URLSearchParams({
          base_url: baseUrl,
          api_key: apiKey,
          org_id: orgId.toString(),
        });

        const response = await apiClient.get(`/elder/relationships?${params}`);

        if (response.data.success) {
          return response.data.relationships || [];
        } else {
          console.error('Failed to fetch relationships:', response.data.error);
          return [];
        }
      } catch (err: unknown) {
        const errorMessage = err instanceof Error
          ? err.message
          : 'Failed to fetch relationships';
        console.error('Error fetching relationships:', errorMessage);
        return [];
      }
    },
    []
  );

  /**
   * Toggle selection of an entity
   */
  const toggleEntitySelection = useCallback((entityId: number) => {
    setState((prev) => {
      const newSelected = new Set(prev.selectedEntities);
      if (newSelected.has(entityId)) {
        newSelected.delete(entityId);
      } else {
        newSelected.add(entityId);
      }
      return { ...prev, selectedEntities: newSelected };
    });
  }, []);

  /**
   * Toggle selection of all visible entities
   */
  const toggleSelectAll = useCallback(() => {
    setState((prev) => {
      if (prev.selectedEntities.size === prev.entities.length) {
        return { ...prev, selectedEntities: new Set() };
      }
      const newSelected = new Set(
        prev.entities.map((e) => e.id)
      );
      return { ...prev, selectedEntities: newSelected };
    });
  }, []);

  /**
   * Import selected entities into a drawing
   */
  const importEntities = useCallback(
    async (
      drawingId: string,
      includeDependencies = true,
      canvasWidth = 1600,
      canvasHeight = 900
    ): Promise<ImportResult | null> => {
      if (!connectionRef.current) {
        setState((prev) => ({
          ...prev,
          error: 'No active Elder connection',
        }));
        return null;
      }

      if (state.selectedEntities.size === 0) {
        setState((prev) => ({
          ...prev,
          error: 'No entities selected for import',
        }));
        return null;
      }

      setState((prev) => ({ ...prev, isLoading: true, error: null }));

      try {
        const response = await apiClient.post('/elder/import', {
          drawing_id: drawingId,
          base_url: connectionRef.current.baseUrl,
          api_key: connectionRef.current.apiKey,
          org_id: connectionRef.current.orgId,
          entity_ids: Array.from(state.selectedEntities),
          include_dependencies: includeDependencies,
          canvas_width: canvasWidth,
          canvas_height: canvasHeight,
        });

        if (response.data.success) {
          const result: ImportResult = {
            nodes: response.data.nodes || [],
            connectors: response.data.connectors || [],
            entityCount: response.data.entity_count || 0,
            relationshipCount: response.data.relationship_count || 0,
          };
          return result;
        } else {
          setState((prev) => ({
            ...prev,
            error: response.data.error || 'Import failed',
          }));
          return null;
        }
      } catch (err: unknown) {
        const errorMessage = err instanceof Error
          ? err.message
          : 'Failed to import entities';
        setState((prev) => ({ ...prev, error: errorMessage }));
        return null;
      } finally {
        setState((prev) => ({ ...prev, isLoading: false }));
      }
    },
    [state.selectedEntities]
  );

  /**
   * Clear selection and error state
   */
  const reset = useCallback(() => {
    setState({
      isLoading: false,
      error: null,
      entities: [],
      selectedEntities: new Set(),
      isConnected: false,
    });
    connectionRef.current = null;
  }, []);

  return {
    // State
    isLoading: state.isLoading,
    error: state.error,
    entities: state.entities,
    selectedEntities: state.selectedEntities,
    isConnected: state.isConnected,

    // Actions
    validateConnection,
    fetchEntities,
    fetchRelationships,
    toggleEntitySelection,
    toggleSelectAll,
    importEntities,
    reset,
  };
};
