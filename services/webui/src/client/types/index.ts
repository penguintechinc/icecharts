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
  role: 'owner' | 'member';
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
