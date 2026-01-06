/**
 * Elder API integration utilities
 *
 * Provides helper functions for Elder API integration with IceCharts.
 */

import apiClient from './api';

/**
 * Elder entity interface
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
 * Elder relationship interface
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
 * Import result interface
 */
export interface ImportResult {
  success: boolean;
  message: string;
  nodes: any[];
  connectors: any[];
  entity_count: number;
  relationship_count: number;
}

/**
 * Validate connection to Elder instance
 *
 * @param baseUrl - Elder instance URL
 * @param apiKey - Elder API key
 * @returns Promise resolving to true if connection is valid
 */
export async function validateElderConnection(
  baseUrl: string,
  apiKey: string
): Promise<boolean> {
  try {
    const response = await apiClient.post('/elder/validate-connection', {
      base_url: baseUrl,
      api_key: apiKey,
    });

    return response.data.success === true;
  } catch (error) {
    console.error('Failed to validate Elder connection:', error);
    return false;
  }
}

/**
 * Fetch entities from Elder instance
 *
 * @param baseUrl - Elder instance URL
 * @param apiKey - Elder API key
 * @param orgId - Organization ID
 * @param entityType - Optional entity type filter
 * @param limit - Maximum results (default: 100)
 * @param offset - Pagination offset (default: 0)
 * @returns Promise resolving to array of entities
 */
export async function fetchElderEntities(
  baseUrl: string,
  apiKey: string,
  orgId: number,
  entityType?: string,
  limit = 100,
  offset = 0
): Promise<ElderEntity[]> {
  try {
    const params = new URLSearchParams({
      base_url: baseUrl,
      api_key: apiKey,
      org_id: orgId.toString(),
      limit: limit.toString(),
      offset: offset.toString(),
    });

    if (entityType) {
      params.append('entity_type', entityType);
    }

    const response = await apiClient.get(`/elder/entities?${params}`);

    if (response.data.success) {
      return response.data.entities || [];
    }

    throw new Error(response.data.error || 'Failed to fetch entities');
  } catch (error) {
    console.error('Error fetching Elder entities:', error);
    throw error;
  }
}

/**
 * Fetch relationships from Elder instance
 *
 * @param baseUrl - Elder instance URL
 * @param apiKey - Elder API key
 * @param orgId - Organization ID
 * @param sourceEntityId - Optional source entity filter
 * @param targetEntityId - Optional target entity filter
 * @returns Promise resolving to array of relationships
 */
export async function fetchElderRelationships(
  baseUrl: string,
  apiKey: string,
  orgId: number,
  sourceEntityId?: number,
  targetEntityId?: number
): Promise<ElderRelationship[]> {
  try {
    const params = new URLSearchParams({
      base_url: baseUrl,
      api_key: apiKey,
      org_id: orgId.toString(),
    });

    if (sourceEntityId) {
      params.append('source_entity_id', sourceEntityId.toString());
    }

    if (targetEntityId) {
      params.append('target_entity_id', targetEntityId.toString());
    }

    const response = await apiClient.get(`/elder/relationships?${params}`);

    if (response.data.success) {
      return response.data.relationships || [];
    }

    throw new Error(response.data.error || 'Failed to fetch relationships');
  } catch (error) {
    console.error('Error fetching Elder relationships:', error);
    throw error;
  }
}

/**
 * Fetch dependency graph from Elder instance
 *
 * @param baseUrl - Elder instance URL
 * @param apiKey - Elder API key
 * @param orgId - Organization ID
 * @param entityId - Optional starting entity ID
 * @param depth - Graph traversal depth (default: 2)
 * @returns Promise resolving to graph object
 */
export async function fetchElderGraph(
  baseUrl: string,
  apiKey: string,
  orgId: number,
  entityId?: number,
  depth = 2
): Promise<any> {
  try {
    const params = new URLSearchParams({
      base_url: baseUrl,
      api_key: apiKey,
      org_id: orgId.toString(),
      depth: depth.toString(),
    });

    if (entityId) {
      params.append('entity_id', entityId.toString());
    }

    const response = await apiClient.get(`/elder/graph?${params}`);

    if (response.data.success) {
      return response.data.graph || {};
    }

    throw new Error(response.data.error || 'Failed to fetch graph');
  } catch (error) {
    console.error('Error fetching Elder graph:', error);
    throw error;
  }
}

/**
 * Import Elder entities into a drawing
 *
 * @param drawingId - Target drawing ID
 * @param baseUrl - Elder instance URL
 * @param apiKey - Elder API key
 * @param orgId - Organization ID
 * @param entityIds - Array of entity IDs to import
 * @param includeDependencies - Whether to include relationships (default: true)
 * @param canvasWidth - Canvas width for layout (default: 1600)
 * @param canvasHeight - Canvas height for layout (default: 900)
 * @returns Promise resolving to import result
 */
export async function importElderEntities(
  drawingId: string,
  baseUrl: string,
  apiKey: string,
  orgId: number,
  entityIds: number[],
  includeDependencies = true,
  canvasWidth = 1600,
  canvasHeight = 900
): Promise<ImportResult> {
  try {
    const response = await apiClient.post('/elder/import', {
      drawing_id: drawingId,
      base_url: baseUrl,
      api_key: apiKey,
      org_id: orgId,
      entity_ids: entityIds,
      include_dependencies: includeDependencies,
      canvas_width: canvasWidth,
      canvas_height: canvasHeight,
    });

    if (!response.data.success) {
      throw new Error(response.data.error || 'Import failed');
    }

    return {
      success: true,
      message: response.data.message || 'Import successful',
      nodes: response.data.nodes || [],
      connectors: response.data.connectors || [],
      entity_count: response.data.entity_count || 0,
      relationship_count: response.data.relationship_count || 0,
    };
  } catch (error) {
    console.error('Error importing from Elder:', error);
    throw error;
  }
}

/**
 * Get Elder health/status
 *
 * @returns Promise resolving to health status
 */
export async function checkElderHealth(): Promise<boolean> {
  try {
    const response = await apiClient.get('/elder/health');
    return response.data.status === 'healthy';
  } catch (error) {
    console.error('Error checking Elder health:', error);
    return false;
  }
}
