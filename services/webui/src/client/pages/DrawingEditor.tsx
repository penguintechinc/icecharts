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

// Cloud Provider Icons as SVG components
const AwsIcon = () => (
  <svg viewBox="0 0 24 24" className="w-8 h-8" fill="currentColor">
    <path d="M6.763 10.036c0 .296.032.535.088.71.064.176.144.368.256.576.04.063.056.127.056.183 0 .08-.048.16-.152.24l-.503.335a.383.383 0 0 1-.208.072c-.08 0-.16-.04-.239-.112a2.47 2.47 0 0 1-.287-.375 6.18 6.18 0 0 1-.248-.471c-.622.734-1.405 1.101-2.347 1.101-.67 0-1.205-.191-1.596-.574-.391-.384-.59-.894-.59-1.533 0-.678.239-1.23.726-1.644.487-.415 1.133-.623 1.955-.623.272 0 .551.024.846.064.296.04.6.104.918.176v-.583c0-.607-.127-1.03-.375-1.277-.255-.248-.686-.367-1.3-.367-.28 0-.568.031-.863.103-.295.072-.583.16-.862.272a2.287 2.287 0 0 1-.28.104.488.488 0 0 1-.127.023c-.112 0-.168-.08-.168-.247v-.391c0-.128.016-.224.056-.28a.597.597 0 0 1 .224-.167c.279-.144.614-.264 1.005-.36a4.84 4.84 0 0 1 1.246-.151c.95 0 1.644.216 2.091.647.439.43.662 1.085.662 1.963v2.586zm-3.24 1.214c.263 0 .534-.048.822-.144.287-.096.543-.271.758-.51.128-.152.224-.32.272-.512.047-.191.08-.423.08-.694v-.335a6.66 6.66 0 0 0-.735-.136 6.02 6.02 0 0 0-.75-.048c-.535 0-.926.104-1.19.32-.263.215-.39.518-.39.917 0 .375.095.655.295.846.191.2.47.296.838.296zm6.41.862c-.144 0-.24-.024-.304-.08-.064-.048-.12-.16-.168-.311L7.586 5.55a1.398 1.398 0 0 1-.072-.32c0-.128.064-.2.191-.2h.783c.151 0 .255.025.31.08.065.048.113.16.16.312l1.342 5.284 1.245-5.284c.04-.16.088-.264.151-.312a.549.549 0 0 1 .32-.08h.638c.152 0 .256.025.32.08.063.048.12.16.151.312l1.261 5.348 1.381-5.348c.048-.16.104-.264.16-.312a.52.52 0 0 1 .311-.08h.743c.127 0 .2.065.2.2 0 .04-.009.08-.017.128a1.137 1.137 0 0 1-.056.2l-1.923 6.17c-.048.16-.104.263-.168.311a.51.51 0 0 1-.303.08h-.687c-.151 0-.255-.024-.32-.08-.063-.056-.119-.16-.15-.32l-1.238-5.148-1.23 5.14c-.04.16-.087.264-.15.32-.065.056-.177.08-.32.08zm10.256.215c-.415 0-.83-.048-1.229-.143-.399-.096-.71-.2-.918-.32-.128-.071-.215-.151-.247-.223a.563.563 0 0 1-.048-.224v-.407c0-.167.064-.247.183-.247.048 0 .096.008.144.024.048.016.12.048.2.08.271.12.566.215.878.279.319.064.63.096.95.096.502 0 .894-.088 1.165-.264a.86.86 0 0 0 .415-.758.777.777 0 0 0-.215-.559c-.144-.151-.416-.287-.807-.415l-1.157-.36c-.583-.183-1.014-.454-1.277-.813a1.902 1.902 0 0 1-.4-1.158c0-.335.073-.63.216-.886.144-.255.335-.479.575-.654.24-.184.51-.32.83-.415.32-.096.655-.136 1.006-.136.175 0 .359.008.535.032.183.024.35.056.518.088.16.04.312.08.455.127.144.048.256.096.336.144a.69.69 0 0 1 .24.2.43.43 0 0 1 .071.263v.375c0 .168-.064.256-.184.256a.83.83 0 0 1-.303-.096 3.652 3.652 0 0 0-1.532-.311c-.455 0-.815.071-1.062.223-.248.152-.375.383-.375.71 0 .224.08.416.24.567.159.152.454.304.877.44l1.134.358c.574.184.99.44 1.237.767.247.327.367.702.367 1.117 0 .343-.072.655-.207.926-.144.272-.336.511-.583.703-.248.2-.543.343-.886.447-.36.111-.734.167-1.142.167z"/>
  </svg>
);

const AzureIcon = () => (
  <svg viewBox="0 0 24 24" className="w-8 h-8" fill="currentColor">
    <path d="M5.483 21.3H24L14.025 4.013l-3.038 8.347 5.836 6.938L5.483 21.3zM13.23 2.7L6.105 8.677 0 19.253h5.505l7.725-16.553z"/>
  </svg>
);

const GcpIcon = () => (
  <svg viewBox="0 0 24 24" className="w-8 h-8" fill="currentColor">
    <path d="M12.19 2.38a9.344 9.344 0 0 0-9.234 6.893c.053-.02-.055.013 0 0-3.875 2.551-3.922 8.11-.247 10.941l.006-.007-.007.03a6.717 6.717 0 0 0 4.077 1.356h5.173l.03.03h5.192c6.687.053 9.376-8.605 3.835-12.35a9.365 9.365 0 0 0-8.825-6.893zM8.073 19.39a4.303 4.303 0 0 1-2.57-.9l-.003.006a4.895 4.895 0 0 1-.18-7.617l.007.007A7.154 7.154 0 0 1 6.86 8.957a7.14 7.14 0 0 1 5.33-4.57 7.14 7.14 0 0 1 6.876 2.897 7.14 7.14 0 0 1 1.444 5.59l.007.007a4.895 4.895 0 0 1-4.167 5.018 4.895 4.895 0 0 1-1.287.09l-.007-.007-.007.007H8.073z"/>
  </svg>
);

const KubernetesIcon = () => (
  <svg viewBox="0 0 24 24" className="w-8 h-8" fill="currentColor">
    <path d="M10.204 14.35l.007.01-.999 2.413a5.171 5.171 0 0 1-2.075-2.597l2.578-.437.004.005a.44.44 0 0 1 .484.606zm-.833-2.129a.44.44 0 0 0 .173-.756l.002-.011L7.585 9.7a5.143 5.143 0 0 0-.73 3.255l2.514-.725.002-.009zm1.145-1.98a.44.44 0 0 0 .699-.337l-.01-.02.15-2.62a5.144 5.144 0 0 0-3.01 1.442l2.164 1.548.007-.013zm2.369-1.898l-.009.02.15 2.62a.44.44 0 0 0 .699.337l.007.013 2.164-1.548a5.144 5.144 0 0 0-3.01-1.442zm2.262 3.673l.002.009 2.514.725a5.143 5.143 0 0 0-.73-3.255l-1.96 1.754.002.011a.44.44 0 0 0 .172.756zm-.695 1.209l.004-.005 2.578.437a5.171 5.171 0 0 1-2.075 2.597l-.999-2.413.007-.01a.44.44 0 0 1 .485-.606z"/>
  </svg>
);

const DockerIcon = () => (
  <svg viewBox="0 0 24 24" className="w-8 h-8" fill="currentColor">
    <path d="M13.983 11.078h2.119a.186.186 0 0 0 .186-.185V9.006a.186.186 0 0 0-.186-.186h-2.119a.185.185 0 0 0-.185.185v1.888c0 .102.083.185.185.185m-2.954-5.43h2.118a.186.186 0 0 0 .186-.186V3.574a.186.186 0 0 0-.186-.185h-2.118a.185.185 0 0 0-.185.185v1.888c0 .102.082.185.185.186m0 2.716h2.118a.187.187 0 0 0 .186-.186V6.29a.186.186 0 0 0-.186-.185h-2.118a.185.185 0 0 0-.185.185v1.887c0 .102.082.185.185.186m-2.93 0h2.12a.186.186 0 0 0 .184-.186V6.29a.185.185 0 0 0-.185-.185H8.1a.185.185 0 0 0-.185.185v1.887c0 .102.083.185.185.186m-2.964 0h2.119a.186.186 0 0 0 .185-.186V6.29a.186.186 0 0 0-.185-.185H5.136a.186.186 0 0 0-.186.185v1.887c0 .102.084.185.186.186m5.893 2.715h2.118a.186.186 0 0 0 .186-.185V9.006a.186.186 0 0 0-.186-.186h-2.118a.185.185 0 0 0-.185.185v1.888c0 .102.082.185.185.185m-2.93 0h2.12a.185.185 0 0 0 .184-.185V9.006a.185.185 0 0 0-.184-.186h-2.12a.185.185 0 0 0-.184.185v1.888c0 .102.083.185.185.185m-2.964 0h2.119a.185.185 0 0 0 .185-.185V9.006a.185.185 0 0 0-.185-.186h-2.119a.186.186 0 0 0-.186.186v1.887c0 .102.084.185.186.185m-2.92 0h2.12a.185.185 0 0 0 .184-.185V9.006a.185.185 0 0 0-.184-.186h-2.12a.185.185 0 0 0-.184.185v1.888c0 .102.082.185.185.185M23.763 9.89c-.065-.051-.672-.51-1.954-.51-.338.001-.676.03-1.01.087-.248-1.7-1.653-2.53-1.716-2.566l-.344-.199-.226.327c-.284.438-.49.922-.612 1.43-.23.97-.09 1.882.403 2.661-.595.332-1.55.413-1.744.42H.751a.751.751 0 0 0-.75.748 11.376 11.376 0 0 0 .692 4.062c.545 1.428 1.355 2.48 2.41 3.124 1.18.723 3.1 1.137 5.275 1.137.983.003 1.963-.086 2.93-.266a12.248 12.248 0 0 0 3.823-1.389c.98-.567 1.86-1.288 2.61-2.136 1.252-1.418 1.998-2.997 2.553-4.4h.221c1.372 0 2.215-.549 2.68-1.009.309-.293.55-.65.707-1.046l.098-.288Z"/>
  </svg>
);

// Infrastructure shape components
function CloudProviderNode({ data, selected }: { data: { label: string; provider: string; color: string }; selected: boolean }) {
  const icons: Record<string, JSX.Element> = {
    aws: <AwsIcon />,
    azure: <AzureIcon />,
    gcp: <GcpIcon />,
    kubernetes: <KubernetesIcon />,
    docker: <DockerIcon />,
  };

  return (
    <div className={`relative px-4 py-3 rounded-lg shadow-lg border-2 ${selected ? 'border-gold-400' : 'border-dark-600'}`}
         style={{ backgroundColor: data.color || '#1F2937' }}>
      <Handle type="target" position={Position.Top} className="w-3 h-3 !bg-gold-500" />
      <Handle type="source" position={Position.Bottom} className="w-3 h-3 !bg-gold-500" />
      <Handle type="target" position={Position.Left} className="w-3 h-3 !bg-gold-500" />
      <Handle type="source" position={Position.Right} className="w-3 h-3 !bg-gold-500" />
      <div className="flex flex-col items-center gap-2 text-white">
        {icons[data.provider] || <ServerIcon />}
        <span className="text-xs font-medium">{data.label}</span>
      </div>
    </div>
  );
}

// Basic shape icons
const ServerIcon = () => (
  <svg viewBox="0 0 24 24" className="w-8 h-8" fill="none" stroke="currentColor" strokeWidth="1.5">
    <rect x="2" y="3" width="20" height="6" rx="1" />
    <rect x="2" y="11" width="20" height="6" rx="1" />
    <circle cx="6" cy="6" r="1" fill="currentColor" />
    <circle cx="6" cy="14" r="1" fill="currentColor" />
  </svg>
);

const DatabaseIcon = () => (
  <svg viewBox="0 0 24 24" className="w-8 h-8" fill="none" stroke="currentColor" strokeWidth="1.5">
    <ellipse cx="12" cy="5" rx="9" ry="3" />
    <path d="M21 5v14c0 1.657-4.03 3-9 3s-9-1.343-9-3V5" />
    <path d="M21 12c0 1.657-4.03 3-9 3s-9-1.343-9-3" />
  </svg>
);

const NetworkIcon = () => (
  <svg viewBox="0 0 24 24" className="w-8 h-8" fill="none" stroke="currentColor" strokeWidth="1.5">
    <circle cx="12" cy="12" r="3" />
    <circle cx="4" cy="6" r="2" />
    <circle cx="20" cy="6" r="2" />
    <circle cx="4" cy="18" r="2" />
    <circle cx="20" cy="18" r="2" />
    <path d="M6 7l4 3M14 10l4-3M6 17l4-3M14 14l4 3" />
  </svg>
);

const StorageIcon = () => (
  <svg viewBox="0 0 24 24" className="w-8 h-8" fill="none" stroke="currentColor" strokeWidth="1.5">
    <path d="M4 4h16v16H4z" />
    <path d="M4 9h16M4 14h16" />
    <circle cx="7" cy="6.5" r="0.5" fill="currentColor" />
    <circle cx="7" cy="11.5" r="0.5" fill="currentColor" />
    <circle cx="7" cy="16.5" r="0.5" fill="currentColor" />
  </svg>
);

const LoadBalancerIcon = () => (
  <svg viewBox="0 0 24 24" className="w-8 h-8" fill="none" stroke="currentColor" strokeWidth="1.5">
    <circle cx="12" cy="5" r="3" />
    <circle cx="5" cy="19" r="3" />
    <circle cx="12" cy="19" r="3" />
    <circle cx="19" cy="19" r="3" />
    <path d="M12 8v3M8 14l-2 2M12 14v2M16 14l2 2" />
  </svg>
);

const UserIcon = () => (
  <svg viewBox="0 0 24 24" className="w-8 h-8" fill="none" stroke="currentColor" strokeWidth="1.5">
    <circle cx="12" cy="7" r="4" />
    <path d="M5 21v-2a4 4 0 014-4h6a4 4 0 014 4v2" />
  </svg>
);

const SecurityIcon = () => (
  <svg viewBox="0 0 24 24" className="w-8 h-8" fill="none" stroke="currentColor" strokeWidth="1.5">
    <path d="M12 2l8 4v6c0 5.5-3.5 10-8 11-4.5-1-8-5.5-8-11V6l8-4z" />
    <path d="M9 12l2 2 4-4" />
  </svg>
);

const ApiIcon = () => (
  <svg viewBox="0 0 24 24" className="w-8 h-8" fill="none" stroke="currentColor" strokeWidth="1.5">
    <path d="M4 6h16M4 12h16M4 18h10" />
    <circle cx="19" cy="18" r="2" />
  </svg>
);

function InfrastructureNode({ data, selected }: { data: { label: string; type: string; color: string }; selected: boolean }) {
  const icons: Record<string, JSX.Element> = {
    server: <ServerIcon />,
    database: <DatabaseIcon />,
    network: <NetworkIcon />,
    storage: <StorageIcon />,
    loadbalancer: <LoadBalancerIcon />,
    user: <UserIcon />,
    security: <SecurityIcon />,
    api: <ApiIcon />,
  };

  return (
    <div className={`relative px-4 py-3 rounded-lg shadow-lg border-2 ${selected ? 'border-gold-400' : 'border-dark-600'}`}
         style={{ backgroundColor: data.color || '#1F2937' }}>
      <Handle type="target" position={Position.Top} className="w-3 h-3 !bg-gold-500" />
      <Handle type="source" position={Position.Bottom} className="w-3 h-3 !bg-gold-500" />
      <Handle type="target" position={Position.Left} className="w-3 h-3 !bg-gold-500" />
      <Handle type="source" position={Position.Right} className="w-3 h-3 !bg-gold-500" />
      <div className="flex flex-col items-center gap-2 text-white">
        {icons[data.type] || <ServerIcon />}
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
      <Handle type="target" position={Position.Top} className="w-3 h-3 !bg-gold-500" />
      <Handle type="source" position={Position.Bottom} className="w-3 h-3 !bg-gold-500" />
      <Handle type="target" position={Position.Left} className="w-3 h-3 !bg-gold-500" />
      <Handle type="source" position={Position.Right} className="w-3 h-3 !bg-gold-500" />
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

// Toolbar categories
const cloudProviders = [
  { id: 'aws', label: 'AWS', color: '#FF9900' },
  { id: 'azure', label: 'Azure', color: '#0078D4' },
  { id: 'gcp', label: 'GCP', color: '#4285F4' },
  { id: 'kubernetes', label: 'K8s', color: '#326CE5' },
  { id: 'docker', label: 'Docker', color: '#2496ED' },
];

const infrastructureTypes = [
  { id: 'server', label: 'Server', icon: '🖥️' },
  { id: 'database', label: 'Database', icon: '🗄️' },
  { id: 'network', label: 'Network', icon: '🌐' },
  { id: 'storage', label: 'Storage', icon: '💾' },
  { id: 'loadbalancer', label: 'Load Balancer', icon: '⚖️' },
  { id: 'user', label: 'User', icon: '👤' },
  { id: 'security', label: 'Security', icon: '🔒' },
  { id: 'api', label: 'API', icon: '🔌' },
];

const shapeOptions = [
  { type: 'rectangle', label: 'Rectangle', icon: '▭' },
  { type: 'rounded', label: 'Rounded', icon: '▢' },
  { type: 'circle', label: 'Circle', icon: '○' },
  { type: 'diamond', label: 'Diamond', icon: '◇' },
];

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
  const [activeTab, setActiveTab] = useState<'cloud' | 'infra' | 'shapes'>('cloud');

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

  const addCloudProviderNode = useCallback((provider: typeof cloudProviders[0]) => {
    const newNode: Node = {
      id: String(nodeIdCounter.current++),
      type: 'cloudProvider',
      position: { x: Math.random() * 400 + 100, y: Math.random() * 300 + 50 },
      data: { label: provider.label, provider: provider.id, color: provider.color },
    };
    setNodes((nds) => [...nds, newNode]);
  }, []);

  const addInfrastructureNode = useCallback((infra: typeof infrastructureTypes[0]) => {
    const newNode: Node = {
      id: String(nodeIdCounter.current++),
      type: 'infrastructure',
      position: { x: Math.random() * 400 + 100, y: Math.random() * 300 + 50 },
      data: { label: infra.label, type: infra.id, color: selectedColor },
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
        {/* Left Toolbar */}
        <div className="w-48 bg-dark-900 border-r border-dark-700 flex flex-col overflow-y-auto">
          {/* Tabs */}
          <div className="flex border-b border-dark-700">
            <button
              onClick={() => setActiveTab('cloud')}
              className={`flex-1 px-2 py-2 text-xs font-medium transition-colors ${activeTab === 'cloud' ? 'bg-dark-800 text-gold-400' : 'text-dark-400 hover:text-gold-400'}`}
            >
              Cloud
            </button>
            <button
              onClick={() => setActiveTab('infra')}
              className={`flex-1 px-2 py-2 text-xs font-medium transition-colors ${activeTab === 'infra' ? 'bg-dark-800 text-gold-400' : 'text-dark-400 hover:text-gold-400'}`}
            >
              Infra
            </button>
            <button
              onClick={() => setActiveTab('shapes')}
              className={`flex-1 px-2 py-2 text-xs font-medium transition-colors ${activeTab === 'shapes' ? 'bg-dark-800 text-gold-400' : 'text-dark-400 hover:text-gold-400'}`}
            >
              Shapes
            </button>
          </div>

          <div className="p-3 space-y-3">
            {activeTab === 'cloud' && (
              <>
                <div className="text-xs text-dark-500 font-medium">Cloud Providers</div>
                <div className="grid grid-cols-2 gap-2">
                  {cloudProviders.map((provider) => (
                    <button
                      key={provider.id}
                      onClick={() => addCloudProviderNode(provider)}
                      className="flex flex-col items-center gap-1 p-2 rounded bg-dark-800 hover:bg-dark-700 transition-colors"
                      style={{ borderLeft: `3px solid ${provider.color}` }}
                    >
                      <span className="text-lg">{provider.id === 'aws' ? '☁️' : provider.id === 'azure' ? '🔷' : provider.id === 'gcp' ? '🔴' : provider.id === 'kubernetes' ? '☸️' : '🐳'}</span>
                      <span className="text-xs text-dark-300">{provider.label}</span>
                    </button>
                  ))}
                </div>
              </>
            )}

            {activeTab === 'infra' && (
              <>
                <div className="text-xs text-dark-500 font-medium">Infrastructure</div>
                <div className="grid grid-cols-2 gap-2">
                  {infrastructureTypes.map((infra) => (
                    <button
                      key={infra.id}
                      onClick={() => addInfrastructureNode(infra)}
                      className="flex flex-col items-center gap-1 p-2 rounded bg-dark-800 hover:bg-dark-700 transition-colors"
                    >
                      <span className="text-lg">{infra.icon}</span>
                      <span className="text-xs text-dark-300">{infra.label}</span>
                    </button>
                  ))}
                </div>

                <div className="border-t border-dark-700 pt-3">
                  <div className="text-xs text-dark-500 font-medium mb-2">Node Color</div>
                  <div className="flex flex-wrap gap-1">
                    {colorOptions.map((opt) => (
                      <button
                        key={opt.color}
                        onClick={() => setSelectedColor(opt.color)}
                        className={`w-6 h-6 rounded border-2 transition-all ${selectedColor === opt.color ? 'border-gold-400 scale-110' : 'border-transparent'}`}
                        style={{ backgroundColor: opt.color }}
                        title={opt.label}
                      />
                    ))}
                  </div>
                </div>
              </>
            )}

            {activeTab === 'shapes' && (
              <>
                <div className="text-xs text-dark-500 font-medium">Basic Shapes</div>
                <div className="grid grid-cols-2 gap-2">
                  {shapeOptions.map((shape) => (
                    <button
                      key={shape.type}
                      onClick={() => addShapeNode(shape.type)}
                      className="flex flex-col items-center gap-1 p-2 rounded bg-dark-800 hover:bg-dark-700 transition-colors"
                    >
                      <span className="text-2xl">{shape.icon}</span>
                      <span className="text-xs text-dark-300">{shape.label}</span>
                    </button>
                  ))}
                </div>

                <div className="border-t border-dark-700 pt-3">
                  <button
                    onClick={addTextNode}
                    className="w-full flex items-center gap-2 p-2 rounded bg-dark-800 hover:bg-dark-700 transition-colors"
                  >
                    <span className="text-lg">T</span>
                    <span className="text-xs text-dark-300">Add Text</span>
                  </button>
                </div>

                <div className="border-t border-dark-700 pt-3">
                  <div className="text-xs text-dark-500 font-medium mb-2">Shape Color</div>
                  <div className="flex flex-wrap gap-1">
                    {colorOptions.map((opt) => (
                      <button
                        key={opt.color}
                        onClick={() => setSelectedColor(opt.color)}
                        className={`w-6 h-6 rounded border-2 transition-all ${selectedColor === opt.color ? 'border-gold-400 scale-110' : 'border-transparent'}`}
                        style={{ backgroundColor: opt.color }}
                        title={opt.label}
                      />
                    ))}
                  </div>
                </div>
              </>
            )}

            {/* Delete button */}
            <div className="border-t border-dark-700 pt-3">
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
