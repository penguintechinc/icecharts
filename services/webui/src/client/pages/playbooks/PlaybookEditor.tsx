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

import React, { useState, useEffect, useCallback, useRef } from 'react';
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
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { useAuthStore } from '../../../store/authStore';
import { playbookEdgeTypes } from '../../components/playbooks/edges';

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
    color: '#6B7280',
  },
  style: {
    strokeWidth: 2,
  },
};

const PlaybookEditor: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { token } = useAuthStore();
  const reactFlowWrapper = useRef<HTMLDivElement>(null);

  const [playbook, setPlaybook] = useState<Playbook | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editorLock, setEditorLock] = useState<EditorLock | null>(null);
  const [isLocked, setIsLocked] = useState(false);
  const [_selectedNode, setSelectedNode] = useState<string | null>(null);

  // ReactFlow state with proper typing
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  const isNewPlaybook = !id;

  // Handle new edge connections - always with arrow and animation
  const onConnect: OnConnect = useCallback(
    (connection: Connection) => {
      const newEdge: Edge = {
        ...connection,
        id: `edge-${connection.source}-${connection.target}`,
        type: 'animatedFlow',
        animated: true,
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 20,
          height: 20,
          color: '#6B7280',
        },
        data: {
          state: 'pending',
          animated: true,
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
  }, [id, token]);

  const fetchPlaybook = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/v1/playbooks/${id}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        if (response.status === 404) {
          navigate('/playbooks');
          return;
        }
        throw new Error('Failed to fetch playbook');
      }

      const data = await response.json();
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
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  // Lock acquisition for exclusive editing
  const acquireLock = useCallback(async () => {
    if (!id) return;

    try {
      const response = await fetch(`/api/v1/playbooks/${id}/lock`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({}),
      });

      if (response.status === 423) {
        // Locked by another user
        const data = await response.json();
        setEditorLock(data.lock);
        setIsLocked(true);
        return false;
      }

      if (!response.ok) {
        throw new Error('Failed to acquire lock');
      }

      const data = await response.json();
      setEditorLock(data.lock);
      setIsLocked(false);
      return true;
    } catch (err) {
      console.error('Failed to acquire lock:', err);
      return false;
    }
  }, [id, token]);

  // Acquire lock when editing an existing playbook
  useEffect(() => {
    if (id && !loading && playbook && !isLocked) {
      acquireLock();
    }
  }, [id, loading, playbook, isLocked, acquireLock]);

  const releaseLock = async () => {
    if (!id) return;

    try {
      await fetch(`/api/v1/playbooks/${id}/lock`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
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
        const response = await fetch('/api/v1/playbooks', {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            name: playbook.name,
            description: playbook.description,
            canvas_data: canvasData,
            trigger_type: playbook.trigger_type,
            visibility: 'private',
          }),
        });

        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.error || 'Failed to create playbook');
        }

        const data = await response.json();
        navigate(`/playbooks/${data.playbook.id}/edit`);
      } else {
        // Update existing playbook
        const response = await fetch(`/api/v1/playbooks/${id}`, {
          method: 'PUT',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            name: playbook.name,
            description: playbook.description,
            canvas_data: canvasData,
            trigger_type: playbook.trigger_type,
          }),
        });

        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.error || 'Failed to save playbook');
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save');
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
          <div className="p-4">
            <h3 className="text-sm font-semibold text-ice-navy-300 uppercase tracking-wider mb-3">
              Triggers
            </h3>
            <div className="space-y-2">
              {['Manual', 'Webhook', 'Schedule', 'gRPC'].map((trigger) => (
                <div
                  key={trigger}
                  className="p-3 bg-green-500/10 border border-green-500/30 rounded-lg cursor-move hover:bg-green-500/20 transition-colors"
                  draggable
                >
                  <span className="text-green-400 text-sm">{trigger}</span>
                </div>
              ))}
            </div>

            <h3 className="text-sm font-semibold text-ice-navy-300 uppercase tracking-wider mb-3 mt-6">
              Transforms
            </h3>
            <div className="space-y-2">
              {['Mock Data', 'JSON Transform', 'Filter', 'Split', 'Merge', 'Delay', 'Expression', 'Code'].map((transform) => (
                <div
                  key={transform}
                  className="p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg cursor-move hover:bg-blue-500/20 transition-colors"
                  draggable
                >
                  <span className="text-blue-400 text-sm">{transform}</span>
                </div>
              ))}
            </div>

            <h3 className="text-sm font-semibold text-ice-navy-300 uppercase tracking-wider mb-3 mt-6">
              Actions
            </h3>
            <div className="space-y-2">
              {['HTTP Request', 'Webhook Out', 'gRPC Call', 'Log', 'AWS Lambda', 'GCP Function'].map((action) => (
                <div
                  key={action}
                  className="p-3 bg-orange-500/10 border border-orange-500/30 rounded-lg cursor-move hover:bg-orange-500/20 transition-colors"
                  draggable
                >
                  <span className="text-orange-400 text-sm">{action}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Canvas area - ReactFlow */}
        <div className="flex-1 bg-ice-navy-900 relative" ref={reactFlowWrapper}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            onPaneClick={onPaneClick}
            edgeTypes={playbookEdgeTypes}
            defaultEdgeOptions={defaultEdgeOptions}
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

        {/* Right panel - Node configuration */}
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
      </div>
    </div>
  );
};

export default PlaybookEditor;
