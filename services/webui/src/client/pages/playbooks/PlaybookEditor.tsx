/**
 * PlaybookEditor - Visual workflow editor using ReactFlow
 *
 * Provides drag-and-drop workflow canvas with:
 * - Node palette (triggers, transforms, actions)
 * - Configuration panel for selected nodes
 * - Real-time save/auto-save
 * - Editor locking (single editor at a time)
 * - Directional animated edges showing data flow
 */

import React, { useState, useEffect, useCallback, useRef, DragEvent } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  type Connection,
  type OnConnect,
  MarkerType,
  BackgroundVariant,
  ConnectionMode,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import api from '../../lib/api';
import { playbookEdgeTypes } from '../../components/playbooks/edges';
import { PlaybookNode } from '../../components/playbooks/nodes';
import { NodeConfigPanel } from '../../components/playbooks/panels';
import { ConnectorSection, Subsection } from '../../components/playbooks/ConnectorSection';
import { CategorySection } from '../../components/playbooks/CategorySection';
import { useConnectors } from '../../hooks/useConnectors';
import { isConnectorNode } from '../../types/connector';

/**
 * Define node handles (input/output ports) for different node types
 * This enables nodes to have multiple output branches for conditional logic
 */
interface NodeHandles {
  inputs: string[];
  outputs: string[];
}

/**
 * Get node handles configuration.
 * For connector nodes, returns handles from the connectorHandles parameter.
 * For built-in nodes, uses hardcoded configurations.
 */
const getNodeHandles = (nodeType: string, connectorHandles?: NodeHandles): NodeHandles => {
  // If connector handles are provided (from manifest), use them
  if (connectorHandles) {
    return connectorHandles;
  }

  // Check if this is a connector node - default to single in/out
  if (isConnectorNode(nodeType)) {
    // Triggers have no inputs, only outputs
    if (nodeType.startsWith('trigger_')) {
      return { inputs: [], outputs: ['out'] };
    }
    // Actions and transforms have single in/out by default
    return { inputs: ['in'], outputs: ['out'] };
  }

  switch (nodeType) {
    // Conditional branching - true/false branches
    case 'conditional_if_then':
      return { inputs: ['in'], outputs: ['true', 'false'] };

    // Switch statement - multiple case branches
    case 'conditional_switch':
      return { inputs: ['in'], outputs: ['case1', 'case2', 'case3', 'default'] };

    // Loops - item output and completion output
    case 'conditional_for_each':
      return { inputs: ['in'], outputs: ['item', 'done'] };
    case 'conditional_while':
      return { inputs: ['in'], outputs: ['loop', 'done'] };

    // Comparison nodes - true/false output
    case 'conditional_equals':
    case 'conditional_greater_than':
    case 'conditional_less_than':
    case 'conditional_contains':
    case 'conditional_regex':
      return { inputs: ['in'], outputs: ['true', 'false'] };

    // Logic gates - single boolean output
    case 'conditional_and':
    case 'conditional_or':
      return { inputs: ['a', 'b'], outputs: ['out'] };
    case 'conditional_not':
      return { inputs: ['in'], outputs: ['out'] };

    // Split transform - multiple outputs
    case 'transform_split':
      return { inputs: ['in'], outputs: ['out1', 'out2', 'out3'] };

    // Merge transform - multiple inputs
    case 'transform_merge':
      return { inputs: ['in1', 'in2', 'in3'], outputs: ['out'] };

    // Default: single input, single output (most nodes)
    default:
      return { inputs: ['in'], outputs: ['out'] };
  }
};

interface EditorLock {
  playbook_id: string;
  locked_by_id: string;
  locked_by_name: string;
  locked_at: string;
  expires_at: string;
  is_holder: boolean;
}

interface Playbook {
  id: string;
  name: string;
  description: string;
  canvas_data: {
    nodes: any[];
    edges: any[];
  };
  trigger_type: string;
  status: string;
  is_enabled: boolean;
}

// Default edge options with arrow markers for directional flow
const defaultEdgeOptions = {
  type: 'animatedFlow',
  animated: true,
  markerEnd: {
    type: MarkerType.ArrowClosed,
    width: 20,
    height: 20,
    color: '#D4AF37',
  },
  style: {
    stroke: '#D4AF37',
    strokeWidth: 2,
  },
};

// Custom node types for playbook workflows
const playbookNodeTypes = {
  playbook: PlaybookNode,
};

const PlaybookEditor: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const reactFlowWrapper = useRef<HTMLDivElement>(null);

  const [playbook, setPlaybook] = useState<Playbook | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editorLock, setEditorLock] = useState<EditorLock | null>(null);
  const [isLocked, setIsLocked] = useState(false);
  const [_selectedNode, setSelectedNode] = useState<string | null>(null);
  // Top-level category expansion state (General, PenguinTech, External, and connectors)
  const [expandedCategories, setExpandedCategories] = useState<Record<string, boolean>>({
    general: true,
    penguintech: true,
    external: false,
  });

  // Connector subsection expansion state (e.g., "waddlebot-triggers": true)
  const [expandedConnectorSubsections, setExpandedConnectorSubsections] = useState<Record<string, boolean>>({});

  // Fetch available connectors
  const { connectors, loading: connectorsLoading } = useConnectors();

  // ReactFlow state with proper typing
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  const isNewPlaybook = !id;

  // Helper to get the selected node object
  const selectedNodeObject = nodes.find(n => n.id === _selectedNode) || null;

  // Toggle category expansion
  const toggleCategory = (category: string) => {
    setExpandedCategories(prev => ({
      ...prev,
      [category]: !prev[category]
    }));
  };

  // Toggle connector subsection expansion
  const toggleConnectorSubsection = (key: string) => {
    setExpandedConnectorSubsections(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  // Handler to update node data
  const onUpdateNodeData = useCallback((nodeId: string, newData: Record<string, any>) => {
    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === nodeId) {
          return { ...node, data: newData };
        }
        return node;
      })
    );
  }, [setNodes]);

  // Node palette data
  const triggers = [
    { id: 'trigger_manual', label: 'Manual', icon: '👆', description: 'Manually trigger workflow' },
    { id: 'trigger_mock_data', label: 'Mock Data', icon: '🎭', description: 'Generate mock data for testing' },
    { id: 'trigger_webhook', label: 'Webhook', icon: '🪝', description: 'Trigger from webhook' },
    { id: 'trigger_schedule', label: 'Schedule', icon: '⏰', description: 'Trigger on schedule' },
    { id: 'trigger_grpc', label: 'gRPC', icon: '⚡', description: 'Receive gRPC requests' },
    { id: 'trigger_mcp', label: 'MCP Server', icon: '🔌', description: 'Receive MCP protocol requests' },
  ];
  const transforms = [
    { id: 'transform_json', label: 'JSON Transform', icon: '🔧', description: 'Transform JSON data' },
    { id: 'transform_filter', label: 'Filter', icon: '🔍', description: 'Filter data' },
    { id: 'transform_split', label: 'Split', icon: '✂️', description: 'Split data stream' },
    { id: 'transform_merge', label: 'Merge', icon: '🔗', description: 'Merge data streams' },
    { id: 'transform_delay', label: 'Delay', icon: '⏱️', description: 'Add delay' },
    { id: 'transform_expression', label: 'Expression', icon: '📐', description: 'Evaluate expression' },
    { id: 'transform_code', label: 'Code', icon: '💻', description: 'Execute code' },
    { id: 'transform_ask_ai', label: 'Ask AI', icon: '🤖', description: 'Query LLM (Ollama/Claude/OpenAI)' },
  ];
  const conditionals = [
    // Logic/Control Flow
    { id: 'conditional_if_then', label: 'If/Then', icon: '🔀', description: 'Conditional branch (true/false)' },
    { id: 'conditional_switch', label: 'Switch', icon: '🎚️', description: 'Multi-way conditional branch' },
    { id: 'conditional_for_each', label: 'For Each', icon: '🔁', description: 'Loop over array items' },
    { id: 'conditional_while', label: 'While', icon: '🔄', description: 'Loop while condition is true' },
    // Comparisons
    { id: 'conditional_equals', label: 'Equals', icon: '⚖️', description: 'Check if values are equal' },
    { id: 'conditional_greater_than', label: 'Greater Than', icon: '➡️', description: 'Check if A > B' },
    { id: 'conditional_less_than', label: 'Less Than', icon: '⬅️', description: 'Check if A < B' },
    { id: 'conditional_contains', label: 'Contains', icon: '🔍', description: 'Check if string/array contains value' },
    { id: 'conditional_regex', label: 'Regex Match', icon: '📝', description: 'Match text against regex pattern' },
    // Logic Gates
    { id: 'conditional_and', label: 'AND', icon: '∧', description: 'All conditions must be true' },
    { id: 'conditional_or', label: 'OR', icon: '∨', description: 'Any condition must be true' },
    { id: 'conditional_not', label: 'NOT', icon: '¬', description: 'Invert boolean value' },
  ];
  const actions = [
    { id: 'action_http', label: 'HTTP Request', icon: '🌐', description: 'Make HTTP request' },
    { id: 'action_webhook', label: 'Webhook Out', icon: '📤', description: 'Send to webhook' },
    { id: 'action_grpc', label: 'gRPC Call', icon: '⚡', description: 'Call gRPC service' },
    { id: 'action_log', label: 'Log', icon: '📝', description: 'Log output' },
    { id: 'action_lambda', label: 'AWS Lambda', icon: '🔲', description: 'Invoke Lambda' },
    { id: 'action_gcp', label: 'GCP Function', icon: '☁️', description: 'Invoke GCP Function' },
    { id: 'action_mcp_call', label: 'MCP Call', icon: '📡', description: 'Call an MCP server tool' },
  ];

  // Handle new edge connections - always with arrow and animation
  // Supports multiple handles per node for conditional branching
  const onConnect: OnConnect = useCallback(
    (connection: Connection) => {
      const newEdge: Edge = {
        ...connection,
        id: `edge-${connection.source}-${connection.target}${
          connection.sourceHandle ? `-${connection.sourceHandle}` : ''
        }${connection.targetHandle ? `-${connection.targetHandle}` : ''}`,
        type: 'animatedFlow',
        animated: true,
        // Include handle information in the edge
        sourceHandle: connection.sourceHandle || 'default',
        targetHandle: connection.targetHandle || 'default',
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 20,
          height: 20,
          color: '#D4AF37',
        },
        style: {
          stroke: '#D4AF37',
          strokeWidth: 2,
        },
        data: {
          state: 'pending',
          animated: true,
          // Store handle names as labels for debugging/visualization
          sourceHandleLabel: connection.sourceHandle,
          targetHandleLabel: connection.targetHandle,
        },
      } as Edge;
      setEdges((eds) => addEdge(newEdge, eds));
    },
    [setEdges]
  );

  // Handle node selection
  const onNodeClick = useCallback((_event: React.MouseEvent, node: Node) => {
    setSelectedNode(node.id);
  }, []);

  // Handle canvas click (deselect)
  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, []);

  // Drag and drop handlers
  const onDragStart = (event: DragEvent<HTMLDivElement>, nodeType: string, category: string) => {
    event.dataTransfer.setData('application/reactflow', JSON.stringify({ nodeType, category }));
    event.dataTransfer.effectAllowed = 'move';
  };

  const onDragOver = useCallback((event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: DragEvent<HTMLDivElement>) => {
      event.preventDefault();

      const reactFlowBounds = reactFlowWrapper.current?.getBoundingClientRect();
      if (!reactFlowBounds) return;

      const data = event.dataTransfer.getData('application/reactflow');
      if (!data) return;

      const { nodeType, category } = JSON.parse(data);

      // Calculate position relative to ReactFlow canvas
      const position = {
        x: event.clientX - reactFlowBounds.left - 75,
        y: event.clientY - reactFlowBounds.top - 20,
      };

      // Find the node label from the definition
      let nodeLabel = nodeType;
      let connectorId: string | undefined;
      let connectorColor: string | undefined;
      let nodeHandles: NodeHandles | undefined;

      // First check built-in nodes
      const allBuiltInNodes = [...triggers, ...transforms, ...conditionals, ...actions];
      const builtInDef = allBuiltInNodes.find(n => n.id === nodeType);
      if (builtInDef) {
        nodeLabel = builtInDef.label;
      } else if (isConnectorNode(nodeType)) {
        // Check connector nodes - parse node type: {category}_{connector}_{id}
        const parts = nodeType.split('_');
        if (parts.length >= 3) {
          const connId = parts[1];
          const actionId = parts.slice(2).join('_');
          const connector = connectors.find(c => c.id === connId);
          if (connector) {
            connectorId = connector.id;
            connectorColor = connector.color;
            // Find the specific trigger/action/transform
            let nodeDef;
            if (category === 'triggers') {
              nodeDef = connector.triggers.find(t => t.id === actionId);
              if (nodeDef) {
                nodeLabel = nodeDef.name;
                nodeHandles = {
                  inputs: [],
                  outputs: nodeDef.outputs.map(o => o.name),
                };
              }
            } else if (category === 'actions') {
              nodeDef = connector.actions.find(a => a.id === actionId);
              if (nodeDef) {
                nodeLabel = nodeDef.name;
                nodeHandles = {
                  inputs: nodeDef.inputs.map(i => i.name),
                  outputs: nodeDef.outputs.map(o => o.name),
                };
              }
            } else if (category === 'transforms') {
              nodeDef = connector.transforms.find(t => t.id === actionId);
              if (nodeDef) {
                nodeLabel = nodeDef.name;
                nodeHandles = {
                  inputs: nodeDef.inputs.map(i => i.name),
                  outputs: nodeDef.outputs.map(o => o.name),
                };
              }
            }
          }
        }
      }

      // Get handles configuration for this node type
      const handles = getNodeHandles(nodeType, nodeHandles);

      const newNode: Node = {
        id: `${category}-${Date.now()}`,
        type: 'playbook',
        position,
        data: {
          label: nodeLabel,
          nodeType,
          category,
          handles,
          // Additional data for connector nodes
          ...(connectorId && { connectorId }),
          ...(connectorColor && { connectorColor }),
        },
      };

      setNodes((nds) => nds.concat(newNode));
    },
    [setNodes, triggers, transforms, conditionals, actions, connectors]
  );

  useEffect(() => {
    if (id) {
      fetchPlaybook();
    } else {
      // New playbook - initialize empty state
      setPlaybook({
        id: '',
        name: 'Untitled Playbook',
        description: '',
        canvas_data: { nodes: [], edges: [] },
        trigger_type: 'manual',
        status: 'draft',
        is_enabled: false,
      });
      setLoading(false);
    }
  }, [id]);

  const fetchPlaybook = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/playbooks/${id}`);

      const data = response.data;
      setPlaybook(data.playbook);

      // Load canvas data into ReactFlow state
      if (data.playbook?.canvas_data) {
        const canvasNodes = data.playbook.canvas_data.nodes || [];
        const canvasEdges = (data.playbook.canvas_data.edges || []).map((edge: any) => ({
          ...edge,
          type: 'animatedFlow',
          animated: true,
          markerEnd: {
            type: MarkerType.ArrowClosed,
            width: 20,
            height: 20,
            color: '#6B7280',
          },
          data: {
            state: edge.data?.state || 'pending',
            animated: true,
          },
        }));
        setNodes(canvasNodes);
        setEdges(canvasEdges);
      }

      // Check editor lock
      if (data.editor_lock) {
        setEditorLock(data.editor_lock);
        setIsLocked(!data.editor_lock.is_holder);
      }
    } catch (err: any) {
      if (err.response?.status === 404) {
        navigate('/playbooks');
        return;
      }
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  // Lock acquisition for exclusive editing
  const acquireLock = useCallback(async () => {
    if (!id) return;

    try {
      const response = await api.post(`/playbooks/${id}/lock`, {});
      setEditorLock(response.data.lock);
      setIsLocked(false);
      return true;
    } catch (err: any) {
      if (err.response?.status === 423) {
        // Locked by another user
        setEditorLock(err.response.data.lock);
        setIsLocked(true);
        return false;
      }
      console.error('Failed to acquire lock:', err);
      return false;
    }
  }, [id]);

  // Acquire lock when editing an existing playbook
  useEffect(() => {
    if (id && !loading && playbook && !isLocked) {
      acquireLock();
    }
  }, [id, loading, playbook, isLocked, acquireLock]);

  const releaseLock = async () => {
    if (!id) return;

    try {
      await api.delete(`/playbooks/${id}/lock`);
    } catch (err) {
      console.error('Failed to release lock:', err);
    }
  };

  const handleSave = async () => {
    if (!playbook) return;

    try {
      setSaving(true);

      // Build canvas data from current ReactFlow state
      const canvasData = {
        nodes: nodes,
        edges: edges.map((edge: Edge) => ({
          id: edge.id,
          source: edge.source,
          target: edge.target,
          sourceHandle: edge.sourceHandle,
          targetHandle: edge.targetHandle,
          type: 'animatedFlow',
          data: edge.data,
        })),
      };

      if (isNewPlaybook) {
        // Create new playbook
        const response = await api.post('/playbooks', {
          name: playbook.name,
          description: playbook.description,
          canvas_data: canvasData,
          trigger_type: playbook.trigger_type,
          visibility: 'private',
        });

        navigate(`/playbooks/${response.data.playbook.id}/edit`);
      } else {
        // Update existing playbook
        await api.put(`/playbooks/${id}`, {
          name: playbook.name,
          description: playbook.description,
          canvas_data: canvasData,
          trigger_type: playbook.trigger_type,
        });
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.error || err.message || 'Failed to save';
      setError(errorMessage);
    } finally {
      setSaving(false);
    }
  };

  // Cleanup on unmount - release lock
  useEffect(() => {
    return () => {
      if (id && editorLock?.is_holder) {
        releaseLock();
      }
    };
  }, [id, editorLock]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-ice-navy-900">
        <div className="animate-pulse text-ice-gold-400">Loading editor...</div>
      </div>
    );
  }

  // Locked by another user modal
  if (isLocked && editorLock) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-ice-navy-900">
        <div className="bg-ice-navy-800 p-8 rounded-lg border border-ice-navy-700 max-w-md text-center">
          <svg className="w-16 h-16 text-yellow-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
          <h2 className="text-xl font-bold text-white mb-2">Playbook is Locked</h2>
          <p className="text-ice-navy-300 mb-4">
            <span className="text-ice-gold-400 font-medium">{editorLock.locked_by_name}</span> is currently editing this playbook.
          </p>
          <p className="text-ice-navy-400 text-sm mb-6">
            You can view the playbook in read-only mode or wait for them to finish editing.
          </p>
          <div className="flex gap-3 justify-center">
            <Link
              to={`/playbooks/${id}`}
              className="px-4 py-2 bg-ice-navy-700 hover:bg-ice-navy-600 text-white rounded-lg transition-colors"
            >
              View Read-Only
            </Link>
            <button
              onClick={fetchPlaybook}
              className="px-4 py-2 bg-ice-gold-500 hover:bg-ice-gold-600 text-ice-navy-900 font-medium rounded-lg transition-colors"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-ice-navy-900">
      {/* Top toolbar */}
      <div className="flex items-center justify-between px-4 py-2 bg-ice-navy-800 border-b border-ice-navy-700">
        <div className="flex items-center gap-4">
          <Link
            to="/playbooks"
            className="p-2 text-ice-navy-400 hover:text-white rounded-lg transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </Link>

          <input
            type="text"
            value={playbook?.name || ''}
            onChange={(e) => setPlaybook(p => p ? { ...p, name: e.target.value } : null)}
            className="bg-transparent border-none text-white text-lg font-medium focus:outline-none focus:ring-2 focus:ring-ice-gold-500/50 rounded px-2 py-1"
            placeholder="Playbook name"
          />
        </div>

        <div className="flex items-center gap-3">
          {/* Status badge */}
          <span className="px-2 py-1 text-xs rounded-full bg-blue-500/20 text-blue-400">
            {playbook?.status || 'Draft'}
          </span>

          {/* Save button */}
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 px-4 py-2 bg-ice-gold-500 hover:bg-ice-gold-600 disabled:bg-ice-gold-500/50 text-ice-navy-900 font-medium rounded-lg transition-colors"
          >
            {saving ? (
              <>
                <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Saving...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
                </svg>
                Save
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error banner */}
      {error && (
        <div className="px-4 py-2 bg-red-500/10 border-b border-red-500/30 text-red-400 text-sm">
          {error}
          <button
            onClick={() => setError(null)}
            className="ml-4 underline hover:no-underline"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Main editor area */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left panel - Node palette */}
        <div className="w-64 bg-ice-navy-800 border-r border-ice-navy-700 overflow-y-auto">
          <div className="p-4 space-y-2">
            {/* ============================================================ */}
            {/* GENERAL - Built-in nodes (Triggers, Transforms, etc.)        */}
            {/* ============================================================ */}
            <CategorySection
              name="General"
              icon="⚡"
              color="#D4AF37"
              count={triggers.length + transforms.length + conditionals.length + actions.length}
              expanded={expandedCategories.general ?? true}
              onToggle={() => toggleCategory('general')}
            >
              {/* Triggers subsection */}
              <Subsection
                title="Triggers"
                category="triggers"
                items={triggers.map(t => ({ id: t.id, name: t.label, icon: t.icon, description: t.description }))}
                connectorId="general"
                connectorIcon="⚡"
                connectorColor="#D4AF37"
                expanded={expandedConnectorSubsections['general-triggers'] ?? false}
                onToggle={() => toggleConnectorSubsection('general-triggers')}
                onDragStart={onDragStart}
              />

              {/* Transforms subsection */}
              <Subsection
                title="Transforms"
                category="transforms"
                items={transforms.map(t => ({ id: t.id, name: t.label, icon: t.icon, description: t.description }))}
                connectorId="general"
                connectorIcon="⚡"
                connectorColor="#D4AF37"
                expanded={expandedConnectorSubsections['general-transforms'] ?? false}
                onToggle={() => toggleConnectorSubsection('general-transforms')}
                onDragStart={onDragStart}
              />

              {/* Conditionals subsection */}
              <Subsection
                title="Conditionals"
                category="conditionals"
                items={conditionals.map(c => ({ id: c.id, name: c.label, icon: c.icon, description: c.description }))}
                connectorId="general"
                connectorIcon="⚡"
                connectorColor="#D4AF37"
                expanded={expandedConnectorSubsections['general-conditionals'] ?? false}
                onToggle={() => toggleConnectorSubsection('general-conditionals')}
                onDragStart={onDragStart}
              />

              {/* Actions subsection */}
              <Subsection
                title="Actions"
                category="actions"
                items={actions.map(a => ({ id: a.id, name: a.label, icon: a.icon, description: a.description }))}
                connectorId="general"
                connectorIcon="⚡"
                connectorColor="#D4AF37"
                expanded={expandedConnectorSubsections['general-actions'] ?? false}
                onToggle={() => toggleConnectorSubsection('general-actions')}
                onDragStart={onDragStart}
              />
            </CategorySection>

            {/* ============================================================ */}
            {/* PENGUINTECH - Internal products (WaddleBot, Elder, etc.)     */}
            {/* ============================================================ */}
            {(() => {
              const penguintechConnectors = connectors.filter(c => c.vendor === 'penguintech');
              const penguintechCount = penguintechConnectors.reduce(
                (sum, c) => sum + c.triggers.length + c.actions.length + c.transforms.length,
                0
              );
              return (
                <CategorySection
                  name="PenguinTech"
                  icon="🐧"
                  color="#6366F1"
                  count={penguintechCount}
                  expanded={expandedCategories.penguintech ?? true}
                  onToggle={() => toggleCategory('penguintech')}
                >
                  {connectorsLoading ? (
                    <div className="flex items-center justify-center py-4">
                      <div className="animate-pulse text-ice-navy-400 text-sm">Loading...</div>
                    </div>
                  ) : penguintechConnectors.length === 0 ? (
                    <div className="text-ice-navy-500 text-xs px-2 py-2">
                      No PenguinTech connectors available
                    </div>
                  ) : (
                    penguintechConnectors.map((connector) => (
                      <ConnectorSection
                        key={connector.id}
                        connector={connector}
                        onDragStart={onDragStart}
                        expandedSubsections={expandedConnectorSubsections}
                        onToggleSubsection={toggleConnectorSubsection}
                        expanded={expandedCategories[connector.id] ?? true}
                        onToggle={() => toggleCategory(connector.id)}
                      />
                    ))
                  )}
                </CategorySection>
              );
            })()}

            {/* ============================================================ */}
            {/* EXTERNAL - Third-party integrations                          */}
            {/* ============================================================ */}
            {(() => {
              const externalConnectors = connectors.filter(c => c.vendor !== 'penguintech');
              const externalCount = externalConnectors.reduce(
                (sum, c) => sum + c.triggers.length + c.actions.length + c.transforms.length,
                0
              );
              return (
                <CategorySection
                  name="External"
                  icon="🔌"
                  color="#10B981"
                  count={externalCount}
                  expanded={expandedCategories.external ?? false}
                  onToggle={() => toggleCategory('external')}
                >
                  {connectorsLoading ? (
                    <div className="flex items-center justify-center py-4">
                      <div className="animate-pulse text-ice-navy-400 text-sm">Loading...</div>
                    </div>
                  ) : externalConnectors.length === 0 ? (
                    <div className="text-ice-navy-500 text-xs px-2 py-2">
                      No external connectors available
                    </div>
                  ) : (
                    externalConnectors.map((connector) => (
                      <ConnectorSection
                        key={connector.id}
                        connector={connector}
                        onDragStart={onDragStart}
                        expandedSubsections={expandedConnectorSubsections}
                        onToggleSubsection={toggleConnectorSubsection}
                        expanded={expandedCategories[connector.id] ?? false}
                        onToggle={() => toggleCategory(connector.id)}
                      />
                    ))
                  )}
                </CategorySection>
              );
            })()}
          </div>
        </div>

        {/* Canvas and right panel container */}
        <div className="flex-1 flex overflow-hidden">
          {/* Canvas area - ReactFlow */}
          <div
            className="flex-1 bg-ice-navy-900 relative"
            ref={reactFlowWrapper}
            onDrop={onDrop}
            onDragOver={onDragOver}
          >
            <ReactFlow
              nodes={nodes}
              edges={edges}
              nodeTypes={playbookNodeTypes}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onNodeClick={onNodeClick}
              onPaneClick={onPaneClick}
              edgeTypes={playbookEdgeTypes}
              defaultEdgeOptions={defaultEdgeOptions}
              connectionMode={ConnectionMode.Loose}
              connectionLineStyle={{ stroke: '#D4AF37', strokeWidth: 2 }}
              fitView
              snapToGrid
              snapGrid={[15, 15]}
              minZoom={0.2}
              maxZoom={2}
              attributionPosition="bottom-left"
              proOptions={{ hideAttribution: true }}
            >
              <Background
                variant={BackgroundVariant.Dots}
                gap={20}
                size={1}
                color="#374151"
              />
              <Controls
                className="bg-ice-navy-800 border border-ice-navy-700 rounded-lg"
                showInteractive={false}
              />
              <MiniMap
                className="bg-ice-navy-800 border border-ice-navy-700 rounded-lg"
                nodeColor="#6B7280"
                maskColor="rgba(0, 0, 0, 0.5)"
              />

              {/* Empty state overlay */}
              {nodes.length === 0 && (
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <div className="text-center text-ice-navy-500">
                    <svg className="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    <p className="text-lg">Drag nodes from the left panel to build your workflow</p>
                    <p className="text-sm mt-2 text-ice-navy-400">
                      Connections automatically show directional flow with animated arrows
                    </p>
                  </div>
                </div>
              )}
            </ReactFlow>
          </div>

          {/* Node Config Panel - slides in from right when node is selected */}
          {selectedNodeObject && (
            <NodeConfigPanel
              node={selectedNodeObject}
              onClose={() => setSelectedNode(null)}
              onUpdate={onUpdateNodeData}
            />
          )}

          {/* Right panel - Playbook settings (shown when no node is selected) */}
          {!selectedNodeObject && (
            <div className="w-80 bg-ice-navy-800 border-l border-ice-navy-700 overflow-y-auto">
              <div className="p-4">
                <h3 className="text-sm font-semibold text-ice-navy-300 uppercase tracking-wider mb-3">
                  Configuration
                </h3>
                <p className="text-ice-navy-500 text-sm">
                  Select a node to configure its settings
                </p>

                <div className="mt-6">
                  <h3 className="text-sm font-semibold text-ice-navy-300 uppercase tracking-wider mb-3">
                    Playbook Settings
                  </h3>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-ice-navy-400 text-sm mb-1">Description</label>
                      <textarea
                        value={playbook?.description || ''}
                        onChange={(e) => setPlaybook(p => p ? { ...p, description: e.target.value } : null)}
                        className="w-full px-3 py-2 bg-ice-navy-700 border border-ice-navy-600 rounded-lg text-white text-sm resize-none focus:outline-none focus:ring-2 focus:ring-ice-gold-500/50"
                        rows={3}
                        placeholder="Describe what this playbook does..."
                      />
                    </div>

                    <div>
                      <label className="block text-ice-navy-400 text-sm mb-1">Trigger Type</label>
                      <select
                        value={playbook?.trigger_type || 'manual'}
                        onChange={(e) => setPlaybook(p => p ? { ...p, trigger_type: e.target.value } : null)}
                        className="w-full px-3 py-2 bg-ice-navy-700 border border-ice-navy-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-ice-gold-500/50"
                      >
                        <option value="manual">Manual</option>
                        <option value="webhook">Webhook</option>
                        <option value="schedule">Schedule</option>
                        <option value="grpc">gRPC</option>
                      </select>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PlaybookEditor;
