import React, { useCallback, useRef, useState } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Edge,
  Node,
  NodeTypes,
  EdgeTypes,
  BackgroundVariant,
  Panel,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import ShapeNode from './nodes/ShapeNode';
import CloudProviderNode from './nodes/CloudProviderNode';
import ContainerNode from './nodes/ContainerNode';
import TextNode from './nodes/TextNode';
import ConnectorEdge from './edges/ConnectorEdge';
import Toolbar from './Toolbar';
import ShapePanel from './ShapePanel';
import PropertiesPanel from './PropertiesPanel';
import ElderImportDialog from '../drawing/ElderImportDialog';

const nodeTypes: NodeTypes = {
  shape: ShapeNode,
  cloudProvider: CloudProviderNode,
  container: ContainerNode,
  text: TextNode,
};

const edgeTypes: EdgeTypes = {
  connector: ConnectorEdge,
};

interface CanvasProps {
  initialNodes?: Node[];
  initialEdges?: Edge[];
  onNodesChange?: (nodes: Node[]) => void;
  onEdgesChange?: (edges: Edge[]) => void;
}

interface HistoryState {
  nodes: Node[];
  edges: Edge[];
}

const Canvas: React.FC<CanvasProps> = ({
  initialNodes = [],
  initialEdges = [],
  onNodesChange,
  onEdgesChange,
}) => {
  const [nodes, setNodes, onNodesChangeInternal] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChangeInternal] = useEdgesState(initialEdges);
  const [selectedNodes, setSelectedNodes] = useState<string[]>([]);
  const [selectedEdges, setSelectedEdges] = useState<string[]>([]);
  const [clipboard, setClipboard] = useState<{ nodes: Node[]; edges: Edge[] } | null>(null);
  const [isElderDialogOpen, setIsElderDialogOpen] = useState(false);

  // History for undo/redo
  const [history, setHistory] = useState<HistoryState[]>([{ nodes: initialNodes, edges: initialEdges }]);
  const [historyIndex, setHistoryIndex] = useState(0);
  const reactFlowWrapper = useRef<HTMLDivElement>(null);

  // Save to history
  const saveToHistory = useCallback((newNodes: Node[], newEdges: Edge[]) => {
    setHistory((prev) => {
      const newHistory = prev.slice(0, historyIndex + 1);
      newHistory.push({ nodes: newNodes, edges: newEdges });
      // Limit history to 50 steps
      if (newHistory.length > 50) {
        newHistory.shift();
        return newHistory;
      }
      return newHistory;
    });
    setHistoryIndex((prev) => Math.min(prev + 1, 49));
  }, [historyIndex]);

  // Undo
  const handleUndo = useCallback(() => {
    if (historyIndex > 0) {
      const prevState = history[historyIndex - 1];
      setNodes(prevState.nodes);
      setEdges(prevState.edges);
      setHistoryIndex(historyIndex - 1);
      onNodesChange?.(prevState.nodes);
      onEdgesChange?.(prevState.edges);
    }
  }, [historyIndex, history, setNodes, setEdges, onNodesChange, onEdgesChange]);

  // Redo
  const handleRedo = useCallback(() => {
    if (historyIndex < history.length - 1) {
      const nextState = history[historyIndex + 1];
      setNodes(nextState.nodes);
      setEdges(nextState.edges);
      setHistoryIndex(historyIndex + 1);
      onNodesChange?.(nextState.nodes);
      onEdgesChange?.(nextState.edges);
    }
  }, [historyIndex, history, setNodes, setEdges, onNodesChange, onEdgesChange]);

  // Handle connection
  const onConnect = useCallback(
    (params: Connection) => {
      const newEdge: Edge = {
        ...params,
        id: `e${params.source}-${params.target}-${Date.now()}`,
        type: 'connector',
        data: {
          label: '',
          startMarker: 'none',
          endMarker: 'arrow',
          strokeColor: '#b1b1b7',
          strokeWidth: 2,
          dashPattern: 'solid',
        },
      };
      const updatedEdges = addEdge(newEdge, edges);
      setEdges(updatedEdges);
      saveToHistory(nodes, updatedEdges);
      onEdgesChange?.(updatedEdges);
    },
    [edges, nodes, setEdges, saveToHistory, onEdgesChange]
  );

  // Handle selection change
  const onSelectionChange = useCallback(
    ({ nodes: selectedNodes, edges: selectedEdges }: { nodes: Node[]; edges: Edge[] }) => {
      setSelectedNodes(selectedNodes.map((n) => n.id));
      setSelectedEdges(selectedEdges.map((e) => e.id));
    },
    []
  );

  // Handle node changes with history
  const handleNodesChange = useCallback(
    (changes: any) => {
      onNodesChangeInternal(changes);
      // Save to history on certain changes (e.g., position, removal)
      const shouldSave = changes.some(
        (change: any) => change.type === 'position' && !change.dragging || change.type === 'remove'
      );
      if (shouldSave) {
        const updatedNodes = nodes.filter((n) => !changes.find((c: any) => c.type === 'remove' && c.id === n.id));
        saveToHistory(updatedNodes, edges);
        onNodesChange?.(updatedNodes);
      }
    },
    [onNodesChangeInternal, nodes, edges, saveToHistory, onNodesChange]
  );

  // Handle edge changes with history
  const handleEdgesChange = useCallback(
    (changes: any) => {
      onEdgesChangeInternal(changes);
      const shouldSave = changes.some((change: any) => change.type === 'remove');
      if (shouldSave) {
        const updatedEdges = edges.filter((e) => !changes.find((c: any) => c.type === 'remove' && c.id === e.id));
        saveToHistory(nodes, updatedEdges);
        onEdgesChange?.(updatedEdges);
      }
    },
    [onEdgesChangeInternal, nodes, edges, saveToHistory, onEdgesChange]
  );

  // Delete selected elements
  const handleDelete = useCallback(() => {
    if (selectedNodes.length > 0 || selectedEdges.length > 0) {
      const updatedNodes = nodes.filter((n) => !selectedNodes.includes(n.id));
      const updatedEdges = edges.filter((e) => !selectedEdges.includes(e.id));
      setNodes(updatedNodes);
      setEdges(updatedEdges);
      saveToHistory(updatedNodes, updatedEdges);
      setSelectedNodes([]);
      setSelectedEdges([]);
      onNodesChange?.(updatedNodes);
      onEdgesChange?.(updatedEdges);
    }
  }, [selectedNodes, selectedEdges, nodes, edges, setNodes, setEdges, saveToHistory, onNodesChange, onEdgesChange]);

  // Copy selected elements
  const handleCopy = useCallback(() => {
    if (selectedNodes.length > 0) {
      const nodesToCopy = nodes.filter((n) => selectedNodes.includes(n.id));
      const edgesToCopy = edges.filter(
        (e) => selectedNodes.includes(e.source) && selectedNodes.includes(e.target)
      );
      setClipboard({ nodes: nodesToCopy, edges: edgesToCopy });
    }
  }, [selectedNodes, nodes, edges]);

  // Paste clipboard content
  const handlePaste = useCallback(() => {
    if (clipboard && clipboard.nodes.length > 0) {
      const idMap = new Map<string, string>();
      const newNodes = clipboard.nodes.map((node) => {
        const newId = `${node.id}-copy-${Date.now()}`;
        idMap.set(node.id, newId);
        return {
          ...node,
          id: newId,
          position: {
            x: node.position.x + 50,
            y: node.position.y + 50,
          },
          selected: true,
        };
      });

      const newEdges = clipboard.edges.map((edge) => ({
        ...edge,
        id: `${edge.id}-copy-${Date.now()}`,
        source: idMap.get(edge.source) || edge.source,
        target: idMap.get(edge.target) || edge.target,
      }));

      const updatedNodes = nodes.map((n) => ({ ...n, selected: false })).concat(newNodes);
      const updatedEdges = edges.concat(newEdges);

      setNodes(updatedNodes);
      setEdges(updatedEdges);
      saveToHistory(updatedNodes, updatedEdges);
      setSelectedNodes(newNodes.map((n) => n.id));
      onNodesChange?.(updatedNodes);
      onEdgesChange?.(updatedEdges);
    }
  }, [clipboard, nodes, edges, setNodes, setEdges, saveToHistory, onNodesChange, onEdgesChange]);

  // Keyboard shortcuts
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      // Delete
      if (event.key === 'Delete' || event.key === 'Backspace') {
        event.preventDefault();
        handleDelete();
      }
      // Copy (Ctrl/Cmd + C)
      if ((event.ctrlKey || event.metaKey) && event.key === 'c') {
        event.preventDefault();
        handleCopy();
      }
      // Paste (Ctrl/Cmd + V)
      if ((event.ctrlKey || event.metaKey) && event.key === 'v') {
        event.preventDefault();
        handlePaste();
      }
      // Undo (Ctrl/Cmd + Z)
      if ((event.ctrlKey || event.metaKey) && event.key === 'z' && !event.shiftKey) {
        event.preventDefault();
        handleUndo();
      }
      // Redo (Ctrl/Cmd + Shift + Z or Ctrl/Cmd + Y)
      if ((event.ctrlKey || event.metaKey) && (event.shiftKey && event.key === 'z' || event.key === 'y')) {
        event.preventDefault();
        handleRedo();
      }
    },
    [handleDelete, handleCopy, handlePaste, handleUndo, handleRedo]
  );

  // Attach keyboard listener
  React.useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleKeyDown]);

  // Update node data
  const updateNodeData = useCallback(
    (nodeId: string, newData: any) => {
      const updatedNodes = nodes.map((node) => {
        if (node.id === nodeId) {
          return { ...node, data: { ...node.data, ...newData } };
        }
        return node;
      });
      setNodes(updatedNodes);
      saveToHistory(updatedNodes, edges);
      onNodesChange?.(updatedNodes);
    },
    [nodes, edges, setNodes, saveToHistory, onNodesChange]
  );

  // Update edge data
  const updateEdgeData = useCallback(
    (edgeId: string, newData: any) => {
      const updatedEdges = edges.map((edge) => {
        if (edge.id === edgeId) {
          return { ...edge, data: { ...edge.data, ...newData } };
        }
        return edge;
      });
      setEdges(updatedEdges);
      saveToHistory(nodes, updatedEdges);
      onEdgesChange?.(updatedEdges);
    },
    [edges, nodes, setEdges, saveToHistory, onEdgesChange]
  );

  // Add node from toolbar/panel
  const addNode = useCallback(
    (nodeType: string, nodeData: any) => {
      const newNode: Node = {
        id: `node-${Date.now()}`,
        type: nodeType,
        position: { x: 250, y: 250 },
        data: nodeData,
      };
      const updatedNodes = [...nodes, newNode];
      setNodes(updatedNodes);
      saveToHistory(updatedNodes, edges);
      onNodesChange?.(updatedNodes);
    },
    [nodes, edges, setNodes, saveToHistory, onNodesChange]
  );

  // Handle Elder import
  const handleElderImport = useCallback(
    (importedNodes: any[], importedConnectors: any[]) => {
      const updatedNodes = [...nodes, ...importedNodes];
      const updatedEdges = [...edges, ...importedConnectors];

      setNodes(updatedNodes);
      setEdges(updatedEdges);
      saveToHistory(updatedNodes, updatedEdges);
      onNodesChange?.(updatedNodes);
      onEdgesChange?.(updatedEdges);
    },
    [nodes, edges, setNodes, setEdges, saveToHistory, onNodesChange, onEdgesChange]
  );

  const selectedNode = selectedNodes.length === 1 ? (nodes.find((n) => n.id === selectedNodes[0]) || null) : null;
  const selectedEdge = selectedEdges.length === 1 ? (edges.find((e) => e.id === selectedEdges[0]) || null) : null;

  return (
    <div className="flex h-screen w-screen">
      {/* Left Sidebar - Shape Panel */}
      <ShapePanel onAddNode={addNode} />

      {/* Main Canvas Area */}
      <div ref={reactFlowWrapper} className="flex-1 relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={handleNodesChange}
          onEdgesChange={handleEdgesChange}
          onConnect={onConnect}
          onSelectionChange={onSelectionChange}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          fitView
          attributionPosition="bottom-left"
        >
          <Background variant={BackgroundVariant.Dots} gap={16} size={1} color="#e5e7eb" />
          <Controls showInteractive={false} />
          <MiniMap
            nodeStrokeWidth={3}
            nodeColor={(node) => {
              if (node.selected) return '#d4af37';
              return '#94a3b8';
            }}
            nodeBorderRadius={2}
            className="bg-white border border-gray-200"
          />
          <Panel position="top-center">
            <Toolbar
              onUndo={handleUndo}
              onRedo={handleRedo}
              canUndo={historyIndex > 0}
              canRedo={historyIndex < history.length - 1}
              onAddNode={addNode}
              onElderImport={() => setIsElderDialogOpen(true)}
            />
          </Panel>
        </ReactFlow>
      </div>

      {/* Right Sidebar - Properties Panel */}
      <PropertiesPanel
        selectedNode={selectedNode}
        selectedEdge={selectedEdge}
        onUpdateNode={updateNodeData}
        onUpdateEdge={updateEdgeData}
      />

      {/* Elder Import Dialog */}
      <ElderImportDialog
        drawingId="current"
        isOpen={isElderDialogOpen}
        onClose={() => setIsElderDialogOpen(false)}
        onImport={handleElderImport}
      />
    </div>
  );
};

export default Canvas;
