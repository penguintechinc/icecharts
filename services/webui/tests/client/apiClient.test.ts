/**
 * Client API Module Tests
 * Tests for src/client/lib/api.ts — token management helpers and interceptors
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';

// Capture interceptors hoisted so they're available inside vi.mock factory
const captured = vi.hoisted(() => ({
  requestInterceptorSuccess: null as ((config: any) => any) | null,
  requestInterceptorError: null as ((error: any) => any) | null,
  responseInterceptorSuccess: null as ((response: any) => any) | null,
  responseInterceptorError: null as ((error: any) => Promise<any>) | null,
  createConfig: null as any,
  mockPost: vi.fn(),
  mockGet: vi.fn(),
}));

vi.mock('axios', () => {
  const mockInstance = {
    get: captured.mockGet,
    post: captured.mockPost,
    interceptors: {
      request: {
        use: vi.fn((successFn: any, errorFn: any) => {
          captured.requestInterceptorSuccess = successFn;
          captured.requestInterceptorError = errorFn;
        }),
      },
      response: {
        use: vi.fn((successFn: any, errorFn: any) => {
          captured.responseInterceptorSuccess = successFn;
          captured.responseInterceptorError = errorFn;
        }),
        eject: vi.fn(),
      },
    },
  };

  return {
    default: {
      create: vi.fn((config: any) => {
        captured.createConfig = config;
        return mockInstance;
      }),
      post: captured.mockPost,
    },
  };
});

// Import after mock — interceptors are captured during module init
import { setTokens, clearTokens, getAccessToken, getRefreshToken } from '@/client/lib/api';

describe('Client API Module', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (localStorage.getItem as ReturnType<typeof vi.fn>).mockReturnValue(null);
    (localStorage.setItem as ReturnType<typeof vi.fn>).mockImplementation(() => {});
    (localStorage.removeItem as ReturnType<typeof vi.fn>).mockImplementation(() => {});
    delete (window as any).location;
    (window as any).location = { href: '' };
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Instance Configuration', () => {
    it('creates axios instance with correct base path', () => {
      expect(captured.createConfig).toBeDefined();
      expect(captured.createConfig.baseURL).toContain('/api/v1');
    });

    it('sets 30 second timeout', () => {
      expect(captured.createConfig.timeout).toBe(30000);
    });

    it('sets JSON content type header', () => {
      expect(captured.createConfig.headers['Content-Type']).toBe('application/json');
    });
  });

  describe('Token Management', () => {
    describe('setTokens', () => {
      it('stores access token in localStorage', () => {
        setTokens('access-123', 'refresh-456');
        expect(localStorage.setItem).toHaveBeenCalledWith('authToken', 'access-123');
      });

      it('stores refresh token in localStorage', () => {
        setTokens('access-123', 'refresh-456');
        expect(localStorage.setItem).toHaveBeenCalledWith('refreshToken', 'refresh-456');
      });
    });

    describe('clearTokens', () => {
      it('removes authToken from localStorage', () => {
        clearTokens();
        expect(localStorage.removeItem).toHaveBeenCalledWith('authToken');
      });

      it('removes refreshToken from localStorage', () => {
        clearTokens();
        expect(localStorage.removeItem).toHaveBeenCalledWith('refreshToken');
      });
    });

    describe('getAccessToken', () => {
      it('reads token from localStorage when not cached', () => {
        (localStorage.getItem as ReturnType<typeof vi.fn>).mockReturnValue('stored-token');
        clearTokens(); // reset in-memory cache
        const token = getAccessToken();
        expect(token).toBe('stored-token');
      });

      it('returns null when no token in localStorage', () => {
        (localStorage.getItem as ReturnType<typeof vi.fn>).mockReturnValue(null);
        clearTokens();
        const token = getAccessToken();
        expect(token).toBeNull();
      });
    });

    describe('getRefreshToken', () => {
      it('reads refresh token from localStorage when not cached', () => {
        (localStorage.getItem as ReturnType<typeof vi.fn>).mockImplementation((key: string) => {
          if (key === 'refreshToken') return 'stored-refresh';
          return null;
        });
        clearTokens();
        const token = getRefreshToken();
        expect(token).toBe('stored-refresh');
      });
    });
  });

  describe('Request Interceptor', () => {
    it('adds Authorization header when token is available', () => {
      setTokens('my-access-token', 'my-refresh-token');

      expect(captured.requestInterceptorSuccess).not.toBeNull();
      const config = { headers: {} as Record<string, string> };
      const result = captured.requestInterceptorSuccess!(config);

      expect(result.headers.Authorization).toBe('Bearer my-access-token');
    });

    it('does not add Authorization header when no token', () => {
      clearTokens();
      (localStorage.getItem as ReturnType<typeof vi.fn>).mockReturnValue(null);

      expect(captured.requestInterceptorSuccess).not.toBeNull();
      const config = { headers: {} as Record<string, string> };
      const result = captured.requestInterceptorSuccess!(config);

      expect(result.headers.Authorization).toBeUndefined();
    });
  });

  describe('Response Interceptor Error Handling', () => {
    it('passes through successful responses', () => {
      expect(captured.responseInterceptorSuccess).not.toBeNull();
      const response = { status: 200, data: { ok: true } };
      const result = captured.responseInterceptorSuccess!(response);
      expect(result).toEqual(response);
    });

    it('rejects promise on error', async () => {
      expect(captured.responseInterceptorError).not.toBeNull();
      const error = { response: { status: 500, data: {} }, request: {} };

      await expect(captured.responseInterceptorError!(error)).rejects.toEqual(error);
    });
  });
});
