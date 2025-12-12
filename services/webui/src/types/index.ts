// User types
export type UserRole = 'admin' | 'maintainer' | 'viewer';

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string | null;
  groups?: Array<{ id: number; name: string; role: string }>;
}

// Drawing types
export interface Drawing {
  id: string;
  name: string;
  description?: string;
  owner_id: string;
  created_at: string;
  updated_at: string;
  data: DrawingData;
  thumbnail_url?: string;
  is_public: boolean;
  collaborators?: Collaborator[];
}

export interface DrawingData {
  nodes: Node[];
  edges: Edge[];
  viewport: Viewport;
  metadata?: DrawingMetadata;
}

export interface DrawingMetadata {
  version: string;
  lastModifiedBy?: string;
  tags?: string[];
  gridSize?: number;
  snapToGrid?: boolean;
}

// Shape/Node types
export interface Node {
  id: string;
  type: NodeType;
  position: Position;
  data: NodeData;
  style?: React.CSSProperties;
  className?: string;
}

export type NodeType =
  | 'rectangle'
  | 'circle'
  | 'diamond'
  | 'triangle'
  | 'text'
  | 'image'
  | 'group'
  | 'custom';

export interface NodeData {
  label: string;
  backgroundColor?: string;
  borderColor?: string;
  borderWidth?: number;
  textColor?: string;
  fontSize?: number;
  fontFamily?: string;
  icon?: string;
  imageUrl?: string;
  width?: number;
  height?: number;
  [key: string]: unknown;
}

export interface Position {
  x: number;
  y: number;
}

// Edge/Connection types
export interface Edge {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
  type?: EdgeType;
  data?: EdgeData;
  style?: React.CSSProperties;
  animated?: boolean;
  label?: string;
}

export type EdgeType =
  | 'default'
  | 'straight'
  | 'step'
  | 'smoothstep'
  | 'bezier'
  | 'custom';

export interface EdgeData {
  label?: string;
  color?: string;
  strokeWidth?: number;
  arrowType?: 'arrow' | 'arrowclosed' | 'none';
  [key: string]: unknown;
}

// Viewport types
export interface Viewport {
  x: number;
  y: number;
  zoom: number;
}

// Collaboration types
export interface Collaborator {
  user_id: string;
  username: string;
  email: string;
  permission: Permission;
  avatar_url?: string;
  is_online?: boolean;
  cursor_position?: CursorPosition;
}

export type Permission = 'owner' | 'edit' | 'view';

export interface CursorPosition {
  x: number;
  y: number;
  color?: string;
}

// WebSocket event types
export interface WebSocketEvent {
  type: WebSocketEventType;
  drawingId: string;
  userId: string;
  timestamp: number;
  data: unknown;
}

export type WebSocketEventType =
  | 'user_joined'
  | 'user_left'
  | 'cursor_move'
  | 'node_create'
  | 'node_update'
  | 'node_delete'
  | 'edge_create'
  | 'edge_update'
  | 'edge_delete'
  | 'viewport_change'
  | 'drawing_update';

// Template types
export interface Template {
  id: string;
  name: string;
  description?: string;
  category: TemplateCategory;
  thumbnail_url?: string;
  data: DrawingData;
  is_featured: boolean;
  created_at: string;
}

export type TemplateCategory =
  | 'flowchart'
  | 'uml'
  | 'network'
  | 'organizational'
  | 'mindmap'
  | 'wireframe'
  | 'other';

// Export types
export type ExportFormat = 'png' | 'svg' | 'pdf' | 'json';

export interface ExportOptions {
  format: ExportFormat;
  quality?: number;
  scale?: number;
  backgroundColor?: string;
  includeMetadata?: boolean;
}

// Tool types
export type Tool =
  | 'select'
  | 'pan'
  | 'rectangle'
  | 'circle'
  | 'diamond'
  | 'triangle'
  | 'text'
  | 'line'
  | 'arrow'
  | 'pencil'
  | 'eraser';

// Color palette
export interface ColorPalette {
  name: string;
  colors: string[];
  isDefault?: boolean;
}

// History/Undo types
export interface HistoryState {
  past: DrawingData[];
  present: DrawingData;
  future: DrawingData[];
}

// API Response types
export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

// Error types
export interface ApiError {
  status: number;
  message: string;
  details?: Record<string, unknown>;
}

// Comment types
export interface Comment {
  id: string;
  drawing_id: string;
  author: CommentAuthor;
  content: string;
  shape_id?: string;
  parent_comment_id?: string;
  is_resolved: boolean;
  resolved_by?: {
    id: string;
    email: string;
    full_name: string;
  };
  resolved_at?: string;
  created_at: string;
  updated_at: string;
  replies?: Comment[];
}

export interface CommentAuthor {
  id: string;
  email: string;
  full_name: string;
  profile_picture_url?: string;
}

export interface CommentSummary {
  total_comments: number;
  resolved_comments: number;
  unresolved_comments: number;
  comments_by_shape: Record<string, number>;
}

// Form types
export interface LoginFormData {
  email: string;
  password: string;
  rememberMe?: boolean;
}

export interface RegisterFormData {
  email: string;
  username: string;
  password: string;
  confirmPassword: string;
}

export interface DrawingFormData {
  name: string;
  description?: string;
  is_public?: boolean;
}
