import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ReactFlow,
  Controls,
  Background,
  MiniMap,
  addEdge,
  applyNodeChanges,
  applyEdgeChanges,
  type Node,
  type Edge,
  type OnNodesChange,
  type OnEdgesChange,
  type OnConnect,
  type NodeTypes,
  BackgroundVariant,
  Panel,
  Handle,
  Position,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import api from '../lib/api';
import Button from '../components/Button';
import type { Drawing, UpdateDrawingData } from '../types';
import { iconMap, iconCategories } from '../components/diagram/icons';

// Custom handle styles for bidirectional connections
const handleStyle = "!w-3 !h-3 !bg-gold-500 !border-2 !border-gold-600";

// Infrastructure shape components - using iconMap from icons.tsx
function CloudProviderNode({ data, selected }: { data: { label: string; provider: string; color: string }; selected: boolean }) {
  const IconComponent = iconMap[data.provider];

  return (
    <div className={`relative px-4 py-3 rounded-lg shadow-lg border-2 ${selected ? 'border-gold-400' : 'border-dark-600'}`}
         style={{ backgroundColor: data.color || '#1F2937' }}>
      {/* Top - both source and target */}
      <Handle type="target" position={Position.Top} id="top-target" className={handleStyle} />
      <Handle type="source" position={Position.Top} id="top-source" className={handleStyle} style={{ top: -6 }} />
      {/* Bottom - both source and target */}
      <Handle type="target" position={Position.Bottom} id="bottom-target" className={handleStyle} />
      <Handle type="source" position={Position.Bottom} id="bottom-source" className={handleStyle} style={{ bottom: -6 }} />
      {/* Left - both source and target */}
      <Handle type="target" position={Position.Left} id="left-target" className={handleStyle} />
      <Handle type="source" position={Position.Left} id="left-source" className={handleStyle} style={{ left: -6 }} />
      {/* Right - both source and target */}
      <Handle type="target" position={Position.Right} id="right-target" className={handleStyle} />
      <Handle type="source" position={Position.Right} id="right-source" className={handleStyle} style={{ right: -6 }} />
      <div className="flex flex-col items-center gap-2 text-white">
        {IconComponent ? <IconComponent className="w-8 h-8" /> : <DefaultServerIcon />}
        <span className="text-xs font-medium">{data.label}</span>
      </div>
    </div>
  );
}

// Default fallback icon
const DefaultServerIcon = () => (
  <svg viewBox="0 0 24 24" className="w-8 h-8" fill="none" stroke="currentColor" strokeWidth="1.5">
    <rect x="2" y="3" width="20" height="6" rx="1" />
    <rect x="2" y="11" width="20" height="6" rx="1" />
    <circle cx="6" cy="6" r="1" fill="currentColor" />
    <circle cx="6" cy="14" r="1" fill="currentColor" />
  </svg>
);

// Generic icon node - uses iconMap for any icon type
function InfrastructureNode({ data, selected }: { data: { label: string; type: string; color: string }; selected: boolean }) {
  const IconComponent = iconMap[data.type];

  return (
    <div className={`relative px-4 py-3 rounded-lg shadow-lg border-2 ${selected ? 'border-gold-400' : 'border-dark-600'}`}
         style={{ backgroundColor: data.color || '#1F2937' }}>
      {/* Top - both source and target */}
      <Handle type="target" position={Position.Top} id="top-target" className={handleStyle} />
      <Handle type="source" position={Position.Top} id="top-source" className={handleStyle} style={{ top: -6 }} />
      {/* Bottom - both source and target */}
      <Handle type="target" position={Position.Bottom} id="bottom-target" className={handleStyle} />
      <Handle type="source" position={Position.Bottom} id="bottom-source" className={handleStyle} style={{ bottom: -6 }} />
      {/* Left - both source and target */}
      <Handle type="target" position={Position.Left} id="left-target" className={handleStyle} />
      <Handle type="source" position={Position.Left} id="left-source" className={handleStyle} style={{ left: -6 }} />
      {/* Right - both source and target */}
      <Handle type="target" position={Position.Right} id="right-target" className={handleStyle} />
      <Handle type="source" position={Position.Right} id="right-source" className={handleStyle} style={{ right: -6 }} />
      <div className="flex flex-col items-center gap-2 text-white">
        {IconComponent ? <IconComponent className="w-8 h-8" /> : <DefaultServerIcon />}
        <span className="text-xs font-medium">{data.label}</span>
      </div>
    </div>
  );
}

function ShapeNode({ data, selected }: { data: { label: string; color: string; shape: string }; selected: boolean }) {
  const shapeStyles: Record<string, string> = {
    rectangle: 'rounded-md',
    rounded: 'rounded-xl',
    diamond: 'rotate-45',
    circle: 'rounded-full',
    hexagon: 'clip-path-hexagon',
  };

  return (
    <div className={`relative ${data.shape === 'circle' ? 'w-20 h-20' : 'px-4 py-3'}`}>
      {/* Top - both source and target */}
      <Handle type="target" position={Position.Top} id="top-target" className={handleStyle} />
      <Handle type="source" position={Position.Top} id="top-source" className={handleStyle} style={{ top: -6 }} />
      {/* Bottom - both source and target */}
      <Handle type="target" position={Position.Bottom} id="bottom-target" className={handleStyle} />
      <Handle type="source" position={Position.Bottom} id="bottom-source" className={handleStyle} style={{ bottom: -6 }} />
      {/* Left - both source and target */}
      <Handle type="target" position={Position.Left} id="left-target" className={handleStyle} />
      <Handle type="source" position={Position.Left} id="left-source" className={handleStyle} style={{ left: -6 }} />
      {/* Right - both source and target */}
      <Handle type="target" position={Position.Right} id="right-target" className={handleStyle} />
      <Handle type="source" position={Position.Right} id="right-source" className={handleStyle} style={{ right: -6 }} />
      <div
        className={`flex items-center justify-center shadow-lg border-2 ${selected ? 'border-gold-400' : 'border-transparent'} ${shapeStyles[data.shape] || shapeStyles.rectangle} ${data.shape === 'circle' ? 'w-full h-full' : 'px-4 py-2'}`}
        style={{ backgroundColor: data.color || '#374151' }}
      >
        <span className={`text-white text-sm ${data.shape === 'diamond' ? '-rotate-45 block' : ''}`}>
          {data.label}
        </span>
      </div>
    </div>
  );
}

function TextNode({ data, selected }: { data: { label: string; fontSize: string }; selected: boolean }) {
  return (
    <div className={`px-2 py-1 ${selected ? 'ring-2 ring-gold-400' : ''}`}>
      <span className={`text-white ${data.fontSize || 'text-sm'}`}>{data.label}</span>
    </div>
  );
}

const nodeTypes: NodeTypes = {
  cloudProvider: CloudProviderNode,
  infrastructure: InfrastructureNode,
  shape: ShapeNode,
  text: TextNode,
};

// Shape options for basic shapes
const shapeOptions = [
  { type: 'rectangle', label: 'Rectangle', icon: '▭' },
  { type: 'rounded', label: 'Rounded', icon: '▢' },
  { type: 'circle', label: 'Circle', icon: '○' },
  { type: 'diamond', label: 'Diamond', icon: '◇' },
];

// Get category keys for tabs
const categoryKeys = Object.keys(iconCategories) as (keyof typeof iconCategories)[];

const colorOptions = [
  { color: '#3B82F6', label: 'Blue' },
  { color: '#10B981', label: 'Green' },
  { color: '#F59E0B', label: 'Amber' },
  { color: '#EF4444', label: 'Red' },
  { color: '#8B5CF6', label: 'Purple' },
  { color: '#EC4899', label: 'Pink' },
  { color: '#6B7280', label: 'Gray' },
  { color: '#1F2937', label: 'Dark' },
];

export default function DrawingEditor() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [, setDrawing] = useState<Drawing | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [drawingName, setDrawingName] = useState('Untitled Drawing');
  const [isEditingName, setIsEditingName] = useState(false);
  const [activeCategory, setActiveCategory] = useState<keyof typeof iconCategories | 'shapes'>('cloud');

  // React Flow state
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [selectedColor, setSelectedColor] = useState('#3B82F6');
  const nodeIdCounter = useRef(1);

  const isNewDrawing = !id || id === 'new';

  useEffect(() => {
    if (id && id !== 'new') {
      fetchDrawing();
    } else {
      setIsLoading(false);
      // Initialize with example nodes for new drawings
      setNodes([
        {
          id: '1',
          type: 'cloudProvider',
          position: { x: 250, y: 50 },
          data: { label: 'AWS Cloud', provider: 'aws', color: '#FF9900' },
        },
        {
          id: '2',
          type: 'infrastructure',
          position: { x: 150, y: 200 },
          data: { label: 'Web Server', type: 'server', color: '#1F2937' },
        },
        {
          id: '3',
          type: 'infrastructure',
          position: { x: 350, y: 200 },
          data: { label: 'Database', type: 'database', color: '#1F2937' },
        },
      ]);
      setEdges([
        { id: 'e1-2', source: '1', target: '2', animated: true, style: { stroke: '#D4AF37', strokeWidth: 2 } },
        { id: 'e1-3', source: '1', target: '3', animated: true, style: { stroke: '#D4AF37', strokeWidth: 2 } },
        { id: 'e2-3', source: '2', target: '3', animated: true, style: { stroke: '#D4AF37', strokeWidth: 2 } },
      ]);
      nodeIdCounter.current = 4;
    }
  }, [id]);

  const fetchDrawing = async () => {
    setIsLoading(true);
    try {
      const response = await api.get<Drawing>(`/drawings/${id}`);
      setDrawing(response.data);
      setDrawingName(response.data.name || 'Untitled Drawing');
      if (response.data.content) {
        const content = response.data.content as { nodes?: Node[]; edges?: Edge[] };
        if (content.nodes) setNodes(content.nodes);
        if (content.edges) setEdges(content.edges);
        nodeIdCounter.current = (content.nodes?.length || 0) + 1;
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to load drawing');
    } finally {
      setIsLoading(false);
    }
  };

  const onNodesChange: OnNodesChange = useCallback(
    (changes) => setNodes((nds) => applyNodeChanges(changes, nds)),
    []
  );

  const onEdgesChange: OnEdgesChange = useCallback(
    (changes) => setEdges((eds) => applyEdgeChanges(changes, eds)),
    []
  );

  const onConnect: OnConnect = useCallback(
    (connection) => setEdges((eds) => addEdge({ ...connection, animated: true, style: { stroke: '#D4AF37', strokeWidth: 2 } }, eds)),
    []
  );

  // Add icon node from any category
  const addIconNode = useCallback((iconId: string, label: string, color: string, isCloudProvider: boolean = false) => {
    const newNode: Node = {
      id: String(nodeIdCounter.current++),
      type: isCloudProvider ? 'cloudProvider' : 'infrastructure',
      position: { x: Math.random() * 400 + 100, y: Math.random() * 300 + 50 },
      data: isCloudProvider
        ? { label, provider: iconId, color }
        : { label, type: iconId, color: selectedColor },
    };
    setNodes((nds) => [...nds, newNode]);
  }, [selectedColor]);

  const addShapeNode = useCallback((shape: string) => {
    const newNode: Node = {
      id: String(nodeIdCounter.current++),
      type: 'shape',
      position: { x: Math.random() * 400 + 100, y: Math.random() * 300 + 50 },
      data: { label: `Node ${nodeIdCounter.current - 1}`, color: selectedColor, shape },
    };
    setNodes((nds) => [...nds, newNode]);
  }, [selectedColor]);

  const addTextNode = useCallback(() => {
    const newNode: Node = {
      id: String(nodeIdCounter.current++),
      type: 'text',
      position: { x: Math.random() * 400 + 100, y: Math.random() * 300 + 50 },
      data: { label: 'Text Label', fontSize: 'text-sm' },
    };
    setNodes((nds) => [...nds, newNode]);
  }, []);

  const handleSave = useCallback(async () => {
    setIsSaving(true);
    setError('');

    try {
      const content = { nodes, edges };

      if (isNewDrawing) {
        const newDrawing: UpdateDrawingData = {
          name: drawingName,
          content,
          visibility: 'private',
        };
        const response = await api.post<{ drawing: Drawing }>('/drawings', newDrawing);
        const createdDrawing = response.data.drawing || response.data;
        if (createdDrawing?.id) {
          navigate(`/drawings/${createdDrawing.id}`, { replace: true });
        }
      } else {
        const updated: UpdateDrawingData = {
          name: drawingName,
          content,
        };
        await api.put(`/drawings/${id}`, updated);
        await fetchDrawing();
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to save drawing');
    } finally {
      setIsSaving(false);
    }
  }, [nodes, edges, drawingName, isNewDrawing, id, navigate]);

  const deleteSelectedNodes = useCallback(() => {
    setNodes((nds) => nds.filter((node) => !node.selected));
    setEdges((eds) => eds.filter((edge) => !edge.selected));
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Delete' || e.key === 'Backspace') {
        if (document.activeElement?.tagName !== 'INPUT') {
          deleteSelectedNodes();
        }
      }
      if (e.key === 's' && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        handleSave();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [deleteSelectedNodes, handleSave]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-dark-950">
        <div className="text-gold-400 text-xl">Loading editor...</div>
      </div>
    );
  }

  if (error && !isNewDrawing) {
    return (
      <div className="flex items-center justify-center h-screen bg-dark-950">
        <div className="bg-dark-900 border border-dark-700 rounded-lg p-8 max-w-md text-center">
          <p className="text-red-400 mb-4">{error}</p>
          <Link to="/drawings">
            <Button>Back to Drawings</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-dark-950">
      {/* Editor Header */}
      <div className="bg-dark-900 border-b border-dark-700 px-4 py-2 flex items-center justify-between z-10">
        <div className="flex items-center gap-4">
          <Link
            to="/drawings"
            className="text-gold-400 hover:text-gold-300 transition-colors p-2"
            title="Back to Drawings"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </Link>

          {isEditingName ? (
            <input
              type="text"
              value={drawingName}
              onChange={(e) => setDrawingName(e.target.value)}
              onBlur={() => setIsEditingName(false)}
              onKeyDown={(e) => e.key === 'Enter' && setIsEditingName(false)}
              className="bg-dark-800 border border-dark-600 rounded px-2 py-1 text-gold-400 focus:outline-none focus:border-gold-500"
              autoFocus
            />
          ) : (
            <h1
              className="text-lg font-semibold text-gold-400 cursor-pointer hover:text-gold-300"
              onClick={() => setIsEditingName(true)}
              title="Click to edit name"
            >
              {drawingName}
            </h1>
          )}
        </div>

        <div className="flex items-center gap-3">
          {error && <span className="text-sm text-red-400">{error}</span>}
          <span className="text-xs text-dark-500">Ctrl+S to save</span>
          <Button onClick={handleSave} isLoading={isSaving}>
            Save
          </Button>
        </div>
      </div>

      {/* Main Editor Area */}
      <div className="flex-1 flex">
        {/* Left Toolbar - Scrollable category list */}
        <div className="w-56 bg-dark-900 border-r border-dark-700 flex flex-col">
          {/* Category selector dropdown */}
          <div className="p-2 border-b border-dark-700">
            <select
              value={activeCategory}
              onChange={(e) => setActiveCategory(e.target.value as keyof typeof iconCategories | 'shapes')}
              className="w-full bg-dark-800 border border-dark-600 rounded px-2 py-1.5 text-sm text-gold-400 focus:outline-none focus:border-gold-500"
            >
              {categoryKeys.map((key) => (
                <option key={key} value={key}>
                  {iconCategories[key].label}
                </option>
              ))}
              <option value="shapes">Basic Shapes</option>
            </select>
          </div>

          {/* Icon grid */}
          <div className="flex-1 overflow-y-auto p-2">
            {activeCategory !== 'shapes' && iconCategories[activeCategory] && (
              <div className="grid grid-cols-2 gap-1.5">
                {iconCategories[activeCategory].icons.map((icon) => {
                  const IconComponent = iconMap[icon.id];
                  const isCloudProvider = activeCategory === 'cloud';
                  return (
                    <button
                      key={icon.id}
                      onClick={() => addIconNode(icon.id, icon.label, icon.color, isCloudProvider)}
                      className="flex flex-col items-center gap-1 p-2 rounded bg-dark-800 hover:bg-dark-700 transition-colors text-white"
                      style={{ borderLeft: `3px solid ${icon.color}` }}
                      title={icon.label}
                    >
                      {IconComponent && <IconComponent className="w-6 h-6" />}
                      <span className="text-[10px] text-dark-300 truncate w-full text-center">{icon.label}</span>
                    </button>
                  );
                })}
              </div>
            )}

            {activeCategory === 'shapes' && (
              <>
                <div className="grid grid-cols-2 gap-1.5 mb-3">
                  {shapeOptions.map((shape) => (
                    <button
                      key={shape.type}
                      onClick={() => addShapeNode(shape.type)}
                      className="flex flex-col items-center gap-1 p-2 rounded bg-dark-800 hover:bg-dark-700 transition-colors"
                    >
                      <span className="text-xl text-white">{shape.icon}</span>
                      <span className="text-[10px] text-dark-300">{shape.label}</span>
                    </button>
                  ))}
                </div>

                <button
                  onClick={addTextNode}
                  className="w-full flex items-center gap-2 p-2 rounded bg-dark-800 hover:bg-dark-700 transition-colors mb-3"
                >
                  <span className="text-lg text-white">T</span>
                  <span className="text-xs text-dark-300">Add Text</span>
                </button>
              </>
            )}

            {/* Color picker - always visible */}
            <div className="border-t border-dark-700 pt-3 mt-3">
              <div className="text-xs text-dark-500 font-medium mb-2">Node Color</div>
              <div className="flex flex-wrap gap-1">
                {colorOptions.map((opt) => (
                  <button
                    key={opt.color}
                    onClick={() => setSelectedColor(opt.color)}
                    className={`w-5 h-5 rounded border-2 transition-all ${selectedColor === opt.color ? 'border-gold-400 scale-110' : 'border-transparent'}`}
                    style={{ backgroundColor: opt.color }}
                    title={opt.label}
                  />
                ))}
              </div>
            </div>

            {/* Delete button */}
            <div className="border-t border-dark-700 pt-3 mt-3">
              <button
                onClick={deleteSelectedNodes}
                className="w-full flex items-center justify-center gap-2 p-2 rounded bg-dark-800 hover:bg-red-900 text-dark-400 hover:text-red-400 transition-colors"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                <span className="text-xs">Delete Selected</span>
              </button>
            </div>
          </div>
        </div>

        {/* Canvas */}
        <div className="flex-1">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            nodeTypes={nodeTypes}
            fitView
            snapToGrid
            snapGrid={[15, 15]}
            defaultEdgeOptions={{
              animated: true,
              style: { stroke: '#D4AF37', strokeWidth: 2 },
            }}
            style={{ background: '#0a0a0f' }}
          >
            <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#1f2937" />
            <Controls className="bg-dark-900 border border-dark-700 rounded-lg" />
            <MiniMap
              nodeColor={(node) => (node.data as any)?.color || '#374151'}
              maskColor="rgba(0, 0, 0, 0.8)"
              className="bg-dark-900 border border-dark-700 rounded-lg"
            />
            <Panel position="bottom-center" className="bg-dark-900/80 px-4 py-2 rounded-t-lg border border-dark-700 border-b-0">
              <div className="flex items-center gap-4 text-xs text-dark-400">
                <span>Drag to connect</span>
                <span>|</span>
                <span>Scroll to zoom</span>
                <span>|</span>
                <span>Del to remove</span>
                <span>|</span>
                <span>{nodes.length} nodes, {edges.length} edges</span>
              </div>
            </Panel>
          </ReactFlow>
        </div>
      </div>
    </div>
  );
}
