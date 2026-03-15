/**
 * useApi Hook Tests - Testing generic API call hook and API methods
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useApiCall, usersApi, helloApi, goApi } from '@/client/hooks/useApi';
import * as apiModule from '@/client/lib/api';

vi.mock('@/client/lib/api');

describe('useApiCall Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with null data and no error', () => {
    const { result } = renderHook(() => useApiCall());

    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.isLoading).toBe(false);
  });

  it('should execute API call successfully', async () => {
    const mockData = { id: 1, name: 'Test' };
    const { result } = renderHook(() => useApiCall());

    await act(async () => {
      const response = await result.current.execute(async () => mockData);
      expect(response).toEqual(mockData);
    });

    expect(result.current.data).toEqual(mockData);
    expect(result.current.error).toBeNull();
    expect(result.current.isLoading).toBe(false);
  });

  it('should handle API call errors', async () => {
    const errorMessage = 'API Error';
    const { result } = renderHook(() => useApiCall());

    await act(async () => {
      try {
        await result.current.execute(async () => {
          throw new Error(errorMessage);
        });
      } catch {
        // Expected error
      }
    });

    expect(result.current.error).toBe(errorMessage);
    expect(result.current.data).toBeNull();
    expect(result.current.isLoading).toBe(false);
  });

  it('should handle non-Error objects as error messages', async () => {
    const { result } = renderHook(() => useApiCall());

    await act(async () => {
      try {
        await result.current.execute(async () => {
          throw 'string error';
        });
      } catch {
        // Expected error
      }
    });

    expect(result.current.error).toBe('An error occurred');
    expect(result.current.isLoading).toBe(false);
  });

  it('should set loading state during execution', async () => {
    const { result } = renderHook(() => useApiCall());

    // Use a deferred callback so React has a chance to flush the setIsLoading(true)
    // state update before we read result.current.isLoading
    let resolveCallback!: () => void;
    const callbackPromise = new Promise<{ data: string }>((resolve) => {
      resolveCallback = () => resolve({ data: 'test' });
    });

    // Start execute — don't await yet
    let executePromise: Promise<unknown>;
    act(() => {
      executePromise = result.current.execute(() => callbackPromise);
    });

    // After act flushes the setIsLoading(true) update, isLoading should be true
    await waitFor(() => {
      expect(result.current.isLoading).toBe(true);
    });

    // Now resolve the callback and wait for completion
    resolveCallback();
    await act(async () => {
      await executePromise;
    });

    expect(result.current.isLoading).toBe(false);
  });

  it('should allow manual data updates with setData', async () => {
    const { result } = renderHook(() => useApiCall());

    await act(async () => {
      result.current.setData({ id: 1, name: 'Manual' });
    });

    expect(result.current.data).toEqual({ id: 1, name: 'Manual' });
  });
});

describe('usersApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should list users', async () => {
    const mockUsers = [
      { id: 1, email: 'user1@example.com', active: true },
      { id: 2, email: 'user2@example.com', active: true },
    ];

    vi.spyOn(apiModule.default, 'get').mockResolvedValueOnce({
      data: { users: mockUsers, total: 2 },
    });

    const result = await usersApi.list(1, 20);

    expect(result.users).toEqual(mockUsers);
    expect(result.total).toBe(2);
    expect(apiModule.default.get).toHaveBeenCalledWith('/admin/users', {
      params: { page: 1, per_page: 20 },
    });
  });

  it('should get single user', async () => {
    const mockUser = { id: 1, email: 'user@example.com', active: true };

    vi.spyOn(apiModule.default, 'get').mockResolvedValueOnce({
      data: { user: mockUser },
    });

    const result = await usersApi.get(1);

    expect(result).toEqual(mockUser);
    expect(apiModule.default.get).toHaveBeenCalledWith('/admin/users/1');
  });

  it('should create user', async () => {
    const newUser = { id: 3, email: 'newuser@example.com', active: true };
    const createData = { email: 'newuser@example.com', password: 'pass123' };

    vi.spyOn(apiModule.default, 'post').mockResolvedValueOnce({
      data: { user: newUser },
    });

    const result = await usersApi.create(createData);

    expect(result).toEqual(newUser);
    expect(apiModule.default.post).toHaveBeenCalledWith('/admin/users', createData);
  });

  it('should update user', async () => {
    const updatedUser = { id: 1, email: 'updated@example.com', active: true };
    const updateData = { email: 'updated@example.com' };

    vi.spyOn(apiModule.default, 'put').mockResolvedValueOnce({
      data: { user: updatedUser },
    });

    const result = await usersApi.update(1, updateData);

    expect(result).toEqual(updatedUser);
    expect(apiModule.default.put).toHaveBeenCalledWith('/admin/users/1', updateData);
  });

  it('should delete user', async () => {
    vi.spyOn(apiModule.default, 'delete').mockResolvedValueOnce({});

    await usersApi.delete(1);

    expect(apiModule.default.delete).toHaveBeenCalledWith('/admin/users/1');
  });

  it('should activate user', async () => {
    vi.spyOn(apiModule.default, 'post').mockResolvedValueOnce({});

    await usersApi.activate(1);

    expect(apiModule.default.post).toHaveBeenCalledWith('/admin/users/1/activate');
  });

  it('should deactivate user', async () => {
    vi.spyOn(apiModule.default, 'post').mockResolvedValueOnce({});

    await usersApi.deactivate(1);

    expect(apiModule.default.post).toHaveBeenCalledWith('/admin/users/1/deactivate');
  });
});

describe('helloApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should get public hello message', async () => {
    const mockMessage = { message: 'Hello World', timestamp: '2025-01-01T00:00:00Z' };

    vi.spyOn(apiModule.default, 'get').mockResolvedValueOnce({
      data: mockMessage,
    });

    const result = await helloApi.get();

    expect(result).toEqual(mockMessage);
    expect(apiModule.default.get).toHaveBeenCalledWith('/hello');
  });

  it('should get protected hello message', async () => {
    const mockMessage = { message: 'Hello User', user: 'testuser', role: 'admin' };

    vi.spyOn(apiModule.default, 'get').mockResolvedValueOnce({
      data: mockMessage,
    });

    const result = await helloApi.getProtected();

    expect(result).toEqual(mockMessage);
    expect(apiModule.default.get).toHaveBeenCalledWith('/hello/protected');
  });
});

describe('goApi', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should get Go backend status', async () => {
    const mockStatus = { status: 'healthy', version: '1.0.0' };

    vi.spyOn(apiModule.default, 'get').mockResolvedValueOnce({
      data: mockStatus,
    });

    const result = await goApi.status();

    expect(result).toEqual(mockStatus);
    expect(apiModule.default.get).toHaveBeenCalledWith('/go/status');
  });

  it('should get NUMA info', async () => {
    const mockNumaInfo = { nodes: 2, memory_per_node: 8000000000 };

    vi.spyOn(apiModule.default, 'get').mockResolvedValueOnce({
      data: mockNumaInfo,
    });

    const result = await goApi.numaInfo();

    expect(result).toEqual(mockNumaInfo);
    expect(apiModule.default.get).toHaveBeenCalledWith('/go/numa/info');
  });

  it('should get memory stats', async () => {
    const mockMemStats = { alloc: 1000000, total_alloc: 5000000, sys: 6000000 };

    vi.spyOn(apiModule.default, 'get').mockResolvedValueOnce({
      data: mockMemStats,
    });

    const result = await goApi.memoryStats();

    expect(result).toEqual(mockMemStats);
    expect(apiModule.default.get).toHaveBeenCalledWith('/go/memory/stats');
  });
});
