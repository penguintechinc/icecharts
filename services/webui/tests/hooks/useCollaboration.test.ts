/**
 * useCollaboration Hook Tests
 * Tests for real-time collaboration WebSocket functionality
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useCollaboration } from '@/client/hooks/useCollaboration';

// Use vi.hoisted so mockSocket is available inside the vi.mock factory (which is hoisted)
const mockSocket = vi.hoisted(() => ({
  connect: vi.fn(),
  disconnect: vi.fn(),
  emit: vi.fn(),
  on: vi.fn(),
  off: vi.fn(),
  connected: true,
}));

vi.mock('socket.io-client', () => ({
  io: vi.fn(() => mockSocket),
}));

// Import io as a proper ESM import so it can be used as a spy
import { io } from 'socket.io-client';

describe('useCollaboration Hook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // localStorage is mocked in setup.ts - configure it to return the auth token by default
    (localStorage.getItem as ReturnType<typeof vi.fn>).mockReturnValue('test-token-123');
    (localStorage.setItem as ReturnType<typeof vi.fn>).mockImplementation(() => {});
    (localStorage.removeItem as ReturnType<typeof vi.fn>).mockImplementation(() => {});
    mockSocket.on.mockClear();
    mockSocket.emit.mockClear();
    mockSocket.disconnect.mockClear();
    mockSocket.connected = true;
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with empty collaborators and no connection', () => {
    const { result } = renderHook(() => useCollaboration(undefined));

    expect(result.current.collaborators).toEqual([]);
    expect(result.current.attentionClicks).toEqual([]);
    expect(result.current.isConnected).toBe(false);
  });

  it('should not connect if no drawing ID provided', () => {
    renderHook(() => useCollaboration(undefined));

    expect(io).not.toHaveBeenCalled();
  });

  it('should not connect if no auth token', () => {
    // Make localStorage return null to simulate no token
    (localStorage.getItem as ReturnType<typeof vi.fn>).mockReturnValue(null);

    renderHook(() => useCollaboration('drawing-1'));

    expect(io).not.toHaveBeenCalled();
  });

  it('should connect with drawing ID and auth token', () => {
    renderHook(() => useCollaboration('drawing-1'));

    expect(io).toHaveBeenCalledWith(expect.any(String), {
      auth: { token: 'test-token-123' },
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 5,
    });
  });

  it('should emit join_drawing on connect', async () => {
    renderHook(() => useCollaboration('drawing-1'));

    // Get the connect handler from mock call tracking
    const connectHandler = mockSocket.on.mock.calls.find(
      (call: any[]) => call[0] === 'connect'
    )?.[1];

    await act(async () => {
      connectHandler?.();
    });

    expect(mockSocket.emit).toHaveBeenCalledWith('join_drawing', {
      drawing_id: 'drawing-1',
    });
  });

  it('should update connection state on connect', async () => {
    const { result } = renderHook(() => useCollaboration('drawing-1'));

    const connectHandler = mockSocket.on.mock.calls.find(
      (call: any[]) => call[0] === 'connect'
    )?.[1];

    await act(async () => {
      connectHandler?.();
    });

    expect(result.current.isConnected).toBe(true);
  });

  it('should receive collaborators list', async () => {
    const mockCollaborators = [
      { user_id: 1, username: 'user1', permission: 'editor', color: '#FF0000' },
      { user_id: 2, username: 'user2', permission: 'viewer', color: '#00FF00' },
    ];

    const { result } = renderHook(() => useCollaboration('drawing-1'));

    const collaboratorsHandler = mockSocket.on.mock.calls.find(
      (call: any[]) => call[0] === 'collaborators_list'
    )?.[1];

    await act(async () => {
      collaboratorsHandler?.({ collaborators: mockCollaborators });
    });

    expect(result.current.collaborators).toHaveLength(2);
    expect(result.current.collaborators[0].username).toBe('user1');
  });

  it('should handle user joined event', async () => {
    const { result } = renderHook(() => useCollaboration('drawing-1'));

    const userJoinedHandler = mockSocket.on.mock.calls.find(
      (call: any[]) => call[0] === 'user_joined'
    )?.[1];

    await act(async () => {
      userJoinedHandler?.({
        user_id: 3,
        username: 'newuser',
        permission: 'editor',
      });
    });

    expect(result.current.collaborators).toHaveLength(1);
    expect(result.current.collaborators[0].username).toBe('newuser');
  });

  it('should prevent duplicate collaborators on user_joined', async () => {
    const { result } = renderHook(() => useCollaboration('drawing-1'));

    const userJoinedHandler = mockSocket.on.mock.calls.find(
      (call: any[]) => call[0] === 'user_joined'
    )?.[1];

    await act(async () => {
      userJoinedHandler?.({
        user_id: 1,
        username: 'user1',
        permission: 'editor',
      });
      userJoinedHandler?.({
        user_id: 1,
        username: 'user1',
        permission: 'editor',
      });
    });

    expect(result.current.collaborators).toHaveLength(1);
  });

  it('should handle user left event', async () => {
    const mockCollaborators = [
      { user_id: 1, username: 'user1', permission: 'editor', color: '#FF0000' },
      { user_id: 2, username: 'user2', permission: 'viewer', color: '#00FF00' },
    ];

    const { result } = renderHook(() => useCollaboration('drawing-1'));

    const collaboratorsHandler = mockSocket.on.mock.calls.find(
      (call: any[]) => call[0] === 'collaborators_list'
    )?.[1];

    await act(async () => {
      collaboratorsHandler?.({ collaborators: mockCollaborators });
    });

    const userLeftHandler = mockSocket.on.mock.calls.find(
      (call: any[]) => call[0] === 'user_left'
    )?.[1];

    await act(async () => {
      userLeftHandler?.({ user_id: 1 });
    });

    expect(result.current.collaborators).toHaveLength(1);
    expect(result.current.collaborators[0].user_id).toBe(2);
  });

  it('should update cursor position', async () => {
    const { result } = renderHook(() => useCollaboration('drawing-1'));

    // Connect first so isConnected becomes true
    const connectHandler = mockSocket.on.mock.calls.find(
      (call: any[]) => call[0] === 'connect'
    )?.[1];

    await act(async () => {
      connectHandler?.();
    });

    await act(async () => {
      result.current.updateCursorPosition(100, 200);
    });

    expect(mockSocket.emit).toHaveBeenCalledWith('cursor_move', {
      drawing_id: 'drawing-1',
      x: 100,
      y: 200,
    });
  });

  it('should handle cursor moved event', async () => {
    const mockCollaborators = [
      { user_id: 1, username: 'user1', permission: 'editor', color: '#FF0000' },
    ];

    const { result } = renderHook(() => useCollaboration('drawing-1'));

    const collaboratorsHandler = mockSocket.on.mock.calls.find(
      (call: any[]) => call[0] === 'collaborators_list'
    )?.[1];

    await act(async () => {
      collaboratorsHandler?.({ collaborators: mockCollaborators });
    });

    const cursorMovedHandler = mockSocket.on.mock.calls.find(
      (call: any[]) => call[0] === 'cursor_moved'
    )?.[1];

    await act(async () => {
      cursorMovedHandler?.({
        user_id: 1,
        username: 'user1',
        x: 150,
        y: 250,
      });
    });

    expect(result.current.collaborators[0].cursor).toEqual({ x: 150, y: 250 });
  });

  it('should trigger attention click', async () => {
    const { result } = renderHook(() => useCollaboration('drawing-1'));

    const connectHandler = mockSocket.on.mock.calls.find(
      (call: any[]) => call[0] === 'connect'
    )?.[1];

    await act(async () => {
      connectHandler?.();
    });

    await act(async () => {
      result.current.triggerAttentionClick(300, 400);
    });

    expect(mockSocket.emit).toHaveBeenCalledWith('attention_click', {
      drawing_id: 'drawing-1',
      x: 300,
      y: 400,
    });
  });

  it('should handle attention_click event', async () => {
    vi.useFakeTimers();

    const { result } = renderHook(() => useCollaboration('drawing-1'));

    const attentionHandler = mockSocket.on.mock.calls.find(
      (call: any[]) => call[0] === 'attention_click'
    )?.[1];

    await act(async () => {
      attentionHandler?.({
        user_id: 1,
        username: 'user1',
        x: 100,
        y: 200,
      });
    });

    expect(result.current.attentionClicks).toHaveLength(1);
    expect(result.current.attentionClicks[0].x).toBe(100);
    expect(result.current.attentionClicks[0].y).toBe(200);

    // Auto-remove after 2 seconds
    await act(async () => {
      vi.advanceTimersByTime(2000);
    });

    expect(result.current.attentionClicks).toHaveLength(0);

    vi.useRealTimers();
  });

  it('should broadcast drawing changes', async () => {
    const { result } = renderHook(() => useCollaboration('drawing-1'));

    const connectHandler = mockSocket.on.mock.calls.find(
      (call: any[]) => call[0] === 'connect'
    )?.[1];

    await act(async () => {
      connectHandler?.();
    });

    await act(async () => {
      result.current.broadcastChange('shape_added', {
        shape_id: 'shape-1',
        type: 'rectangle',
      });
    });

    expect(mockSocket.emit).toHaveBeenCalledWith('drawing_change', {
      drawing_id: 'drawing-1',
      change_type: 'shape_added',
      change_data: { shape_id: 'shape-1', type: 'rectangle' },
    });
  });

  it('should handle drawing_changed event', async () => {
    renderHook(() => useCollaboration('drawing-1'));

    const dispatchEventSpy = vi.spyOn(window, 'dispatchEvent');

    const drawingChangedHandler = mockSocket.on.mock.calls.find(
      (call: any[]) => call[0] === 'drawing_changed'
    )?.[1];

    await act(async () => {
      drawingChangedHandler?.({
        user_id: 1,
        change_type: 'shape_deleted',
        change_data: { shape_id: 'shape-1' },
      });
    });

    expect(dispatchEventSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        type: 'collaboration:drawing_changed',
      })
    );
  });

  it('should handle disconnect', async () => {
    const { result } = renderHook(() => useCollaboration('drawing-1'));

    const connectHandler = mockSocket.on.mock.calls.find(
      (call: any[]) => call[0] === 'connect'
    )?.[1];

    await act(async () => {
      connectHandler?.();
    });

    const disconnectHandler = mockSocket.on.mock.calls.find(
      (call: any[]) => call[0] === 'disconnect'
    )?.[1];

    await act(async () => {
      disconnectHandler?.('client disconnect');
    });

    // Source disconnect handler sets isConnected=false and clears collaborators
    // attentionClicks is NOT cleared on disconnect (only on cleanup/unmount)
    expect(result.current.isConnected).toBe(false);
    expect(result.current.collaborators).toHaveLength(0);
  });

  it('should clean up on unmount', async () => {
    const { unmount } = renderHook(() => useCollaboration('drawing-1'));

    // Simulate connection
    const connectHandler = mockSocket.on.mock.calls.find(
      (call: any[]) => call[0] === 'connect'
    )?.[1];

    await act(async () => {
      connectHandler?.();
    });

    mockSocket.connected = true;

    unmount();

    expect(mockSocket.emit).toHaveBeenCalledWith('leave_drawing', {
      drawing_id: 'drawing-1',
    });
    expect(mockSocket.disconnect).toHaveBeenCalled();
  });

  it('should throttle cursor position updates', async () => {
    vi.useFakeTimers();

    const { result } = renderHook(() => useCollaboration('drawing-1'));

    const connectHandler = mockSocket.on.mock.calls.find(
      (call: any[]) => call[0] === 'connect'
    )?.[1];

    await act(async () => {
      connectHandler?.();
    });

    const initialEmitCount = mockSocket.emit.mock.calls.length;

    // Rapid cursor updates within the throttle window (33ms)
    await act(async () => {
      result.current.updateCursorPosition(100, 100);
      result.current.updateCursorPosition(101, 101);
      result.current.updateCursorPosition(102, 102);
    });

    // Only first call should be emitted due to throttling (33ms)
    const newEmitCount = mockSocket.emit.mock.calls.length - initialEmitCount;
    expect(newEmitCount).toBeLessThanOrEqual(1);

    vi.useRealTimers();
  });
});
