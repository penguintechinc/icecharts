/**
 * useConnectors Hook Tests
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useConnectors, useConnectorNodes, useConnector, useConnectorNodeSchema, buildPaletteNodesFromConnectors } from '@/client/hooks/useConnectors';
import * as apiModule from '@/client/lib/api';

vi.mock('@/client/lib/api');

describe('useConnectors Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with loading state', () => {
    vi.spyOn(apiModule.default, 'get').mockRejectedValueOnce(new Error('API not ready'));

    const { result } = renderHook(() => useConnectors());

    expect(result.current.loading).toBe(true);
    expect(result.current.connectors).toEqual([]);
    expect(result.current.error).toBeNull();
  });

  it('should fetch connectors successfully', async () => {
    const mockConnectors = [
      { id: 'connector-1', name: 'Test Connector 1', icon: 'icon1', color: '#FF0000', triggers: [], actions: [], transforms: [] },
      { id: 'connector-2', name: 'Test Connector 2', icon: 'icon2', color: '#00FF00', triggers: [], actions: [], transforms: [] },
    ];

    vi.spyOn(apiModule.default, 'get').mockResolvedValueOnce({
      data: { connectors: mockConnectors },
    });

    const { result } = renderHook(() => useConnectors());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.connectors).toEqual(mockConnectors);
    expect(result.current.error).toBeNull();
  });

  it('should handle API errors', async () => {
    const errorMessage = 'Failed to fetch connectors';
    vi.spyOn(apiModule.default, 'get').mockRejectedValueOnce(new Error(errorMessage));

    const { result } = renderHook(() => useConnectors());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe(errorMessage);
    expect(result.current.connectors).toEqual([]);
  });

  it('should provide refetch function', async () => {
    const mockConnectors = [
      { id: 'connector-1', name: 'Test Connector', icon: 'icon', color: '#FF0000', triggers: [], actions: [], transforms: [] },
    ];

    vi.spyOn(apiModule.default, 'get').mockResolvedValueOnce({
      data: { connectors: mockConnectors },
    });

    const { result } = renderHook(() => useConnectors());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(typeof result.current.refetch).toBe('function');

    // Reset mock and refetch
    vi.spyOn(apiModule.default, 'get').mockResolvedValueOnce({
      data: { connectors: [...mockConnectors] },
    });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.connectors).toHaveLength(1);
  });

  it('should handle empty connector list', async () => {
    vi.spyOn(apiModule.default, 'get').mockResolvedValueOnce({
      data: { connectors: [] },
    });

    const { result } = renderHook(() => useConnectors());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.connectors).toEqual([]);
    expect(result.current.error).toBeNull();
  });
});

describe('useConnectorNodes Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should fetch connector nodes', async () => {
    const mockNodes = [
      { id: 'node-1', node_type: 'trigger', connector_id: 'conn-1', category: 'triggers', config_schema: [], inputs: [], outputs: [] },
      { id: 'node-2', node_type: 'action', connector_id: 'conn-1', category: 'actions', config_schema: [], inputs: [], outputs: [] },
    ];

    vi.spyOn(apiModule.default, 'get').mockResolvedValueOnce({
      data: { nodes: mockNodes },
    });

    const { result } = renderHook(() => useConnectorNodes());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.nodes).toEqual(mockNodes);
  });

  it('should group nodes by connector', async () => {
    const mockNodes = [
      { id: 'node-1', node_type: 'trigger', connector_id: 'conn-1', category: 'triggers', config_schema: [], inputs: [], outputs: [] },
      { id: 'node-2', node_type: 'action', connector_id: 'conn-1', category: 'actions', config_schema: [], inputs: [], outputs: [] },
      { id: 'node-3', node_type: 'trigger', connector_id: 'conn-2', category: 'triggers', config_schema: [], inputs: [], outputs: [] },
    ];

    vi.spyOn(apiModule.default, 'get').mockResolvedValueOnce({
      data: { nodes: mockNodes },
    });

    const { result } = renderHook(() => useConnectorNodes());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(Object.keys(result.current.nodesByConnector)).toContain('conn-1');
    expect(Object.keys(result.current.nodesByConnector)).toContain('conn-2');
    expect(result.current.nodesByConnector['conn-1']).toHaveLength(2);
    expect(result.current.nodesByConnector['conn-2']).toHaveLength(1);
  });

  it('should group nodes by category', async () => {
    const mockNodes = [
      { id: 'node-1', node_type: 'trigger', connector_id: 'conn-1', category: 'triggers', config_schema: [], inputs: [], outputs: [] },
      { id: 'node-2', node_type: 'action', connector_id: 'conn-1', category: 'actions', config_schema: [], inputs: [], outputs: [] },
      { id: 'node-3', node_type: 'trigger', connector_id: 'conn-2', category: 'triggers', config_schema: [], inputs: [], outputs: [] },
    ];

    vi.spyOn(apiModule.default, 'get').mockResolvedValueOnce({
      data: { nodes: mockNodes },
    });

    const { result } = renderHook(() => useConnectorNodes());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(Object.keys(result.current.nodesByCategory)).toContain('triggers');
    expect(Object.keys(result.current.nodesByCategory)).toContain('actions');
    expect(result.current.nodesByCategory['triggers']).toHaveLength(2);
    expect(result.current.nodesByCategory['actions']).toHaveLength(1);
  });

  it('should filter nodes by category parameter', async () => {
    vi.spyOn(apiModule.default, 'get').mockResolvedValueOnce({
      data: { nodes: [] },
    });

    const { result } = renderHook(() => useConnectorNodes('triggers'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(apiModule.default.get).toHaveBeenCalledWith('/connectors/nodes?category=triggers');
  });
});

describe('useConnector Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should find connector by ID', async () => {
    const mockConnectors = [
      { id: 'connector-1', name: 'Test Connector 1', icon: 'icon1', color: '#FF0000', triggers: [], actions: [], transforms: [] },
      { id: 'connector-2', name: 'Test Connector 2', icon: 'icon2', color: '#00FF00', triggers: [], actions: [], transforms: [] },
    ];

    vi.spyOn(apiModule.default, 'get').mockResolvedValueOnce({
      data: { connectors: mockConnectors },
    });

    const { result } = renderHook(() => useConnector('connector-1'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.connector).toEqual(mockConnectors[0]);
  });

  it('should return null for non-existent connector', async () => {
    const mockConnectors = [
      { id: 'connector-1', name: 'Test Connector', icon: 'icon', color: '#FF0000', triggers: [], actions: [], transforms: [] },
    ];

    vi.spyOn(apiModule.default, 'get').mockResolvedValueOnce({
      data: { connectors: mockConnectors },
    });

    const { result } = renderHook(() => useConnector('non-existent'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.connector).toBeNull();
  });

  it('should return null when connectorId is null', async () => {
    vi.spyOn(apiModule.default, 'get').mockResolvedValueOnce({
      data: { connectors: [] },
    });

    const { result } = renderHook(() => useConnector(null));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.connector).toBeNull();
  });
});

describe('useConnectorNodeSchema Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should retrieve node schema by node type', async () => {
    const mockNode = {
      id: 'node-1',
      node_type: 'trigger-type-1',
      connector_id: 'conn-1',
      category: 'triggers',
      config_schema: [{ field: 'config1', type: 'string' }],
      inputs: [{ name: 'input1' }],
      outputs: [{ name: 'output1' }],
    };

    vi.spyOn(apiModule.default, 'get').mockResolvedValueOnce({
      data: { nodes: [mockNode] },
    });

    const { result } = renderHook(() => useConnectorNodeSchema('trigger-type-1'));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.node).toEqual(mockNode);
    expect(result.current.configSchema).toEqual(mockNode.config_schema);
    expect(result.current.inputs).toEqual(mockNode.inputs);
    expect(result.current.outputs).toEqual(mockNode.outputs);
  });

  it('should return null schema when nodeType is null', async () => {
    vi.spyOn(apiModule.default, 'get').mockResolvedValueOnce({
      data: { nodes: [] },
    });

    const { result } = renderHook(() => useConnectorNodeSchema(null));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.node).toBeNull();
    expect(result.current.configSchema).toEqual([]);
    expect(result.current.inputs).toEqual([]);
    expect(result.current.outputs).toEqual([]);
  });
});

describe('buildPaletteNodesFromConnectors', () => {
  it('should build palette nodes from connectors', () => {
    const connectors = [
      {
        id: 'connector-1',
        name: 'Test Connector',
        icon: 'test-icon',
        color: '#FF0000',
        triggers: [
          { id: 'trigger-1', name: 'Trigger 1', icon: 'trigger-icon', description: 'Test trigger' },
        ],
        actions: [
          { id: 'action-1', name: 'Action 1', icon: 'action-icon', description: 'Test action' },
        ],
        transforms: [
          { id: 'transform-1', name: 'Transform 1', icon: 'transform-icon', description: 'Test transform' },
        ],
      },
    ];

    const result = buildPaletteNodesFromConnectors(connectors);

    expect(result.triggers).toHaveLength(1);
    expect(result.actions).toHaveLength(1);
    expect(result.transforms).toHaveLength(1);

    expect(result.triggers[0].id).toBe('trigger_connector-1_trigger-1');
    expect(result.actions[0].id).toBe('action_connector-1_action-1');
    expect(result.transforms[0].id).toBe('transform_connector-1_transform-1');
  });

  it('should handle empty connectors', () => {
    const result = buildPaletteNodesFromConnectors([]);

    expect(result.triggers).toHaveLength(0);
    expect(result.actions).toHaveLength(0);
    expect(result.transforms).toHaveLength(0);
  });

  it('should use connector color for all nodes', () => {
    const connectors = [
      {
        id: 'connector-1',
        name: 'Test Connector',
        icon: 'test-icon',
        color: '#ABCDEF',
        triggers: [{ id: 'trigger-1', name: 'Trigger 1', icon: 'icon', description: 'desc' }],
        actions: [],
        transforms: [],
      },
    ];

    const result = buildPaletteNodesFromConnectors(connectors);

    expect(result.triggers[0].connectorColor).toBe('#ABCDEF');
  });

  it('should handle multiple connectors', () => {
    const connectors = [
      {
        id: 'connector-1',
        name: 'Connector 1',
        icon: 'icon1',
        color: '#FF0000',
        triggers: [{ id: 'trigger-1', name: 'T1', icon: 'i1', description: 'd1' }],
        actions: [],
        transforms: [],
      },
      {
        id: 'connector-2',
        name: 'Connector 2',
        icon: 'icon2',
        color: '#00FF00',
        triggers: [{ id: 'trigger-2', name: 'T2', icon: 'i2', description: 'd2' }],
        actions: [],
        transforms: [],
      },
    ];

    const result = buildPaletteNodesFromConnectors(connectors);

    expect(result.triggers).toHaveLength(2);
    expect(result.triggers[0].connectorId).toBe('connector-1');
    expect(result.triggers[1].connectorId).toBe('connector-2');
  });
});
