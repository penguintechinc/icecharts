/**
 * useExport Hook Tests
 *
 * Tests for loading state, format handling, error reporting, and download triggering.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';

// Use vi.hoisted so the mock function is available inside vi.mock factory
const { mockAxiosGet } = vi.hoisted(() => ({
  mockAxiosGet: vi.fn(),
}));

// Mock axios so the apiClient singleton uses our mock
vi.mock('axios', async () => {
  const actual = await vi.importActual<typeof import('axios')>('axios');
  const mockInstance = {
    get: mockAxiosGet,
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    interceptors: {
      request: { use: vi.fn(), eject: vi.fn() },
      response: { use: vi.fn(), eject: vi.fn() },
    },
    defaults: {},
  };
  return {
    ...actual,
    default: {
      ...actual.default,
      create: vi.fn(() => mockInstance),
    },
  };
});

// Mock URL.createObjectURL and revokeObjectURL
const mockCreateObjectURL = vi.fn(() => 'blob:http://localhost/mock-url');
const mockRevokeObjectURL = vi.fn();
global.URL.createObjectURL = mockCreateObjectURL;
global.URL.revokeObjectURL = mockRevokeObjectURL;

// Track anchor link clicks without recursion
const mockClick = vi.fn();
const originalCreateElement = document.createElement.bind(document);
vi.spyOn(document, 'createElement').mockImplementation((tag: string) => {
  if (tag === 'a') {
    const el = originalCreateElement('span') as unknown as HTMLAnchorElement;
    (el as Record<string, unknown>).click = mockClick;
    (el as Record<string, unknown>).download = '';
    (el as Record<string, unknown>).href = '';
    return el;
  }
  return originalCreateElement(tag);
});

import { useExport } from '@/client/hooks/useExport';

describe('useExport Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockCreateObjectURL.mockReturnValue('blob:http://localhost/mock-url');
  });

  it('initializes with loading=false, error=null, success=false', () => {
    const { result } = renderHook(() => useExport());
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.success).toBe(false);
  });

  it('sets loading=true while export is in progress', async () => {
    mockAxiosGet.mockImplementation(() => new Promise(() => {}));

    const { result } = renderHook(() => useExport());

    act(() => {
      result.current.exportDrawing('drawing-1', { format: 'png' }).catch(() => {});
    });

    expect(result.current.loading).toBe(true);
  });

  it('sets success=true after synchronous export completes', async () => {
    const mockBlob = new Blob(['data'], { type: 'image/png' });
    mockAxiosGet.mockResolvedValue({
      status: 200,
      data: mockBlob,
      headers: { 'content-type': 'image/png' },
    });

    const { result } = renderHook(() => useExport());

    await act(async () => {
      await result.current.exportDrawing('drawing-1', { format: 'png' });
    });

    await waitFor(() => {
      expect(result.current.success).toBe(true);
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBeNull();
    });
  });

  it('triggers file download on successful synchronous export', async () => {
    const mockBlob = new Blob(['svg-data'], { type: 'image/svg+xml' });
    mockAxiosGet.mockResolvedValue({
      status: 200,
      data: mockBlob,
      headers: { 'content-type': 'image/svg+xml' },
    });

    const { result } = renderHook(() => useExport());

    await act(async () => {
      await result.current.exportDrawing('drawing-1', { format: 'svg' });
    });

    await waitFor(() => {
      expect(mockClick).toHaveBeenCalled();
    });
  });

  it('sets error state when export API call fails', async () => {
    const networkError = new Error('Network error');
    mockAxiosGet.mockRejectedValue(networkError);

    const { result } = renderHook(() => useExport());

    await act(async () => {
      try {
        await result.current.exportDrawing('drawing-1', { format: 'png' });
      } catch {
        // expected to throw
      }
    });

    await waitFor(() => {
      expect(result.current.error).toBe('Network error');
      expect(result.current.success).toBe(false);
      expect(result.current.loading).toBe(false);
    });
  });

  it('returns jobId for async exports (202 response)', async () => {
    const jobResponseData = JSON.stringify({ job_id: 'job-abc-123' });
    const jobBlob = new Blob([jobResponseData], { type: 'application/json' });

    mockAxiosGet.mockResolvedValue({
      status: 202,
      data: jobBlob,
      headers: {},
    });

    const { result } = renderHook(() => useExport());

    let exportResult: unknown;
    await act(async () => {
      exportResult = await result.current.exportDrawing('drawing-1', { format: 'pdf' });
    });

    await waitFor(() => {
      expect(exportResult).toMatchObject({ jobId: 'job-abc-123' });
    });
  });

  it('exposes exportDrawing function on the hook return value', () => {
    const { result } = renderHook(() => useExport());
    expect(typeof result.current.exportDrawing).toBe('function');
  });
});
