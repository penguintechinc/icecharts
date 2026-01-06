import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';

// Build API URL - always use direct API connection to avoid nginx header issues
const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5001';
const basePath = import.meta.env.VITE_API_BASE_PATH || '/api/v1';
const API_BASE_URL = `${apiUrl}${basePath}`;

// Create axios instance with default config
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('authToken');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response) {
      // Server responded with error status
      const status = error.response.status;

      switch (status) {
        case 401:
          // Unauthorized - clear token and redirect to login
          localStorage.removeItem('authToken');
          localStorage.removeItem('user');
          window.location.href = '/login';
          break;
        case 403:
          // Forbidden - user doesn't have permission
          console.error('Access denied:', error.response.data);
          break;
        case 404:
          // Not found
          console.error('Resource not found:', error.response.data);
          break;
        case 500:
          // Server error
          console.error('Server error:', error.response.data);
          break;
        default:
          console.error('API error:', error.response.data);
      }
    } else if (error.request) {
      // Request made but no response received
      console.error('Network error - no response received');
    } else {
      // Error setting up request
      console.error('Request error:', error.message);
    }

    return Promise.reject(error);
  }
);

// API methods
export const api = {
  // Auth endpoints
  auth: {
    login: (email: string, password: string) =>
      apiClient.post('/auth/login', { email, password }),
    register: (email: string, password: string, username: string) =>
      apiClient.post('/auth/register', { email, password, username }),
    logout: () =>
      apiClient.post('/auth/logout'),
    me: () =>
      apiClient.get('/auth/me'),
    refreshToken: () =>
      apiClient.post('/auth/refresh'),
    // OAuth endpoints
    google: () =>
      apiClient.get('/auth/google'),
    googleCallback: (code: string, state: string) =>
      apiClient.post('/auth/google/callback', { code, state }),
  },

  // Drawing endpoints
  drawings: {
    list: () =>
      apiClient.get('/drawings'),
    get: (id: string) =>
      apiClient.get(`/drawings/${id}`),
    create: (data: { name: string; description?: string }) =>
      apiClient.post('/drawings', data),
    update: (id: string, data: Partial<{ name: string; description?: string; data: unknown }>) =>
      apiClient.put(`/drawings/${id}`, data),
    delete: (id: string) =>
      apiClient.delete(`/drawings/${id}`),
    share: (id: string, userId: string, permission: string) =>
      apiClient.post(`/drawings/${id}/share`, { userId, permission }),
    export: (id: string, format: string) =>
      apiClient.get(`/drawings/${id}/export/${format}`, { responseType: 'blob' }),
  },

  // User endpoints
  users: {
    list: () =>
      apiClient.get('/users'),
    get: (id: string) =>
      apiClient.get(`/users/${id}`),
    update: (id: string, data: Partial<{ username: string; email: string }>) =>
      apiClient.put(`/users/${id}`, data),
    delete: (id: string) =>
      apiClient.delete(`/users/${id}`),
  },

  // Template endpoints
  templates: {
    list: () =>
      apiClient.get('/templates'),
    get: (id: string) =>
      apiClient.get(`/templates/${id}`),
    create: (data: { name: string; description?: string; data: unknown }) =>
      apiClient.post('/templates', data),
  },

  // Elder integration endpoints
  elder: {
    validateConnection: (baseUrl: string, apiKey: string) =>
      apiClient.post('/elder/validate-connection', { base_url: baseUrl, api_key: apiKey }),
    getEntities: (baseUrl: string, apiKey: string, orgId: number, entityType?: string) => {
      const params = new URLSearchParams({
        base_url: baseUrl,
        api_key: apiKey,
        org_id: orgId.toString(),
      });
      if (entityType) params.append('entity_type', entityType);
      return apiClient.get(`/elder/entities?${params}`);
    },
    getRelationships: (baseUrl: string, apiKey: string, orgId: number) => {
      const params = new URLSearchParams({
        base_url: baseUrl,
        api_key: apiKey,
        org_id: orgId.toString(),
      });
      return apiClient.get(`/elder/relationships?${params}`);
    },
    getGraph: (baseUrl: string, apiKey: string, orgId: number, entityId?: number, depth?: number) => {
      const params = new URLSearchParams({
        base_url: baseUrl,
        api_key: apiKey,
        org_id: orgId.toString(),
      });
      if (entityId) params.append('entity_id', entityId.toString());
      if (depth) params.append('depth', depth.toString());
      return apiClient.get(`/elder/graph?${params}`);
    },
    importEntities: (data: {
      drawing_id: string;
      base_url: string;
      api_key: string;
      org_id: number;
      entity_ids: number[];
      include_dependencies?: boolean;
      canvas_width?: number;
      canvas_height?: number;
    }) =>
      apiClient.post('/elder/import', data),
  },

  // Comment endpoints
  comments: {
    list: (drawingId: string, filters?: { shape_id?: string; filter?: 'all' | 'open' | 'resolved'; thread?: boolean }) => {
      const params = new URLSearchParams();
      if (filters?.shape_id) params.append('shape_id', filters.shape_id);
      if (filters?.filter) params.append('filter', filters.filter);
      if (filters?.thread !== undefined) params.append('thread', filters.thread.toString());
      const queryString = params.toString();
      return apiClient.get(`/drawings/${drawingId}/comments${queryString ? `?${queryString}` : ''}`);
    },
    getSummary: (drawingId: string) =>
      apiClient.get(`/drawings/${drawingId}/comments/summary`),
    create: (drawingId: string, data: { content: string; shape_id?: string; parent_comment_id?: string }) =>
      apiClient.post(`/drawings/${drawingId}/comments`, data),
    update: (drawingId: string, commentId: string, data: { content: string }) =>
      apiClient.put(`/drawings/${drawingId}/comments/${commentId}`, data),
    delete: (drawingId: string, commentId: string) =>
      apiClient.delete(`/drawings/${drawingId}/comments/${commentId}`),
    resolve: (drawingId: string, commentId: string) =>
      apiClient.post(`/drawings/${drawingId}/comments/${commentId}/resolve`),
    unresolve: (drawingId: string, commentId: string) =>
      apiClient.post(`/drawings/${drawingId}/comments/${commentId}/unresolve`),
  },

  // Health check
  health: () =>
    apiClient.get('/health'),
};

export default apiClient;
