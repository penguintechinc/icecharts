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

export interface CreateUserData {
  email: string;
  password: string;
  full_name: string;
  role: UserRole;
}

export interface UpdateUserData {
  email?: string;
  full_name?: string;
  role?: UserRole;
  is_active?: boolean;
  password?: string;
}

// Auth types
export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

// API Response types
export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

// Navigation types
export interface NavItem {
  label: string;
  path: string;
  icon?: string;
  roles?: UserRole[];
}

export interface NavCategory {
  label: string;
  items: NavItem[];
  roles?: UserRole[];
}

// Tab types
export interface Tab {
  id: string;
  label: string;
  content?: React.ReactNode;
}

// IceCharts domain types
export type DrawingVisibility = 'private' | 'group' | 'public';

export interface Drawing {
  id: number;
  name: string;
  description: string | null;
  visibility: DrawingVisibility;
  thumbnail_url: string | null;
  content: object;
  owner_id: number;
  owner_name: string;
  group_id: number | null;
  group_name: string | null;
  created_at: string;
  updated_at: string;
  is_template: boolean;
}

export interface CreateDrawingData {
  name: string;
  description?: string;
  visibility?: DrawingVisibility;
  content?: object;
  group_id?: number;
  is_template?: boolean;
}

export interface UpdateDrawingData {
  name?: string;
  description?: string;
  visibility?: DrawingVisibility;
  content?: object;
  group_id?: number;
}

export interface Group {
  id: number;
  name: string;
  description: string | null;
  owner_id: number;
  owner_name: string;
  member_count: number;
  drawing_count: number;
  created_at: string;
  updated_at: string;
}

export interface CreateGroupData {
  name: string;
  description?: string;
}

export interface UpdateGroupData {
  name?: string;
  description?: string;
}

export interface GroupMember {
  id: number;
  group_id: number;
  user_id: number;
  user_name: string;
  user_email: string;
  role: 'owner' | 'admin' | 'editor' | 'viewer';
  added_at: string;
}

export interface Template {
  id: number;
  name: string;
  description: string | null;
  category: string;
  thumbnail_url: string | null;
  content: object;
  created_by: number;
  created_by_name: string;
  usage_count: number;
  created_at: string;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name: string;
}

export interface SSOConfiguration {
  id: number;
  provider: 'google' | 'saml' | 'oauth2';
  enabled: boolean;
  client_id: string;
  client_secret?: string;
  metadata_url?: string;
  created_at: string;
  updated_at: string;
}

// Collection types
export type CollectionShareMode = 'private' | 'link_only' | 'registered_users';
export type CollectionPermission = 'viewer' | 'editor' | 'admin';

export interface Collection {
  id: number;
  name: string;
  description: string | null;
  owner_id: number;
  owner_name: string;
  thumbnail_url: string | null;
  is_public: boolean;
  share_token: string | null;
  share_mode: CollectionShareMode;
  drawing_count: number;
  created_at: string;
  updated_at: string;
}

export interface CreateCollectionData {
  name: string;
  description?: string;
  is_public?: boolean;
  share_mode?: CollectionShareMode;
}

export interface UpdateCollectionData {
  name?: string;
  description?: string;
  is_public?: boolean;
  share_mode?: CollectionShareMode;
}

export interface CollectionItem {
  id: number;
  collection_id: number;
  drawing_id: number;
  drawing: Drawing;
  order_index: number;
  added_by_id: number;
  added_by_name: string;
  added_at: string;
}

export interface CollectionShare {
  id: number;
  collection_id: number;
  shared_with_id: number | null;
  shared_with_name: string | null;
  shared_with_group_id: number | null;
  shared_with_group_name: string | null;
  permission: CollectionPermission;
  created_by_id: number;
  created_by_name: string;
  created_at: string;
}

export interface CollectionAnalytics {
  view_count: number;
  unique_viewers: number;
  last_accessed: string | null;
  recent_accesses: Array<{
    user_id: number | null;
    user_name: string | null;
    accessed_at: string;
    ip_address: string | null;
  }>;
}

// Drawing analytics types
export interface DrawingAnalytics {
  view_count?: number;
  total_views?: number;
  unique_viewers?: number;
  last_accessed?: string | null;
  recent_accesses?: Array<{
    accessed_at: string | null;
    access_ip?: string | null;
    ip_address?: string | null;
    user_agent?: string | null;
  }>;
}

// Service Account types
export interface ServiceAccount {
  id: number;
  name: string;
  description: string | null;
  scopes: string[];
  is_active: boolean;
  created_by_id: number;
  created_by_name: string;
  created_at: string;
  updated_at: string;
  last_used_at: string | null;
}

export interface ServiceAccountToken {
  jti: string;
  name: string;
  scopes: string[];
  created_at: string;
  expires_at: string | null;
  last_used_at: string | null;
}

export interface CreateServiceAccountData {
  name: string;
  description?: string;
  scopes: string[];
}

export interface UpdateServiceAccountData {
  name?: string;
  description?: string;
  scopes?: string[];
  is_active?: boolean;
}

export interface CreateTokenData {
  name: string;
  scopes?: string[];
  expires_in_days?: number;
}

export interface GeneratedToken {
  token: string;
  jti: string;
  name: string;
  scopes: string[];
  expires_at: string | null;
}

// Activity Log types
export interface ActivityLog {
  id: number;
  user_id: number;
  user_name: string;
  user_email: string;
  action: string;
  resource_type: string;
  resource_id: number | null;
  resource_name: string | null;
  timestamp: string;
  ip_address: string | null;
  user_agent: string | null;
  details: Record<string, any>;
}

// Audit Log types
export interface AuditLog {
  id: number;
  user_id: number;
  user_name: string;
  user_email: string;
  action: string;
  resource_type: string;
  resource_id: number | null;
  resource_name: string | null;
  timestamp: string;
  ip_address: string | null;
  user_agent: string | null;
  old_values: Record<string, any>;
  new_values: Record<string, any>;
  status: 'success' | 'failed';
  error_message: string | null;
}

// Shape Library types
export interface ShapeLibrary {
  id: number;
  tenant_id?: number;
  name: string;
  description: string | null;
  owner_id: number;
  owner_name?: string;
  is_public: boolean;
  created_at: string;
  updated_at: string;
  shape_count?: number;
  shapes?: LibraryShape[];
}

export interface LibraryShape {
  id: number;
  library_id: number;
  name: string;
  description: string | null;
  shape_data: object;
  category: string;
  created_at: string;
  updated_at: string;
}

export interface CreateLibraryData {
  name: string;
  description?: string;
  is_public?: boolean;
}

export interface UpdateLibraryData {
  name?: string;
  description?: string;
  is_public?: boolean;
}

export interface CreateShapeData {
  name: string;
  description?: string;
  shape_data: object;
  category?: string;
}

export interface UpdateShapeData {
  name?: string;
  description?: string;
  shape_data?: object;
  category?: string;
}
