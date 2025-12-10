/**
 * useCollaboration Hook - WebSocket connection and collaboration logic
 * Manages real-time collaboration features using Socket.IO
 */

import { useEffect, useRef, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';
import { useCollaborationStore } from '../store/collaborationStore';

interface UseCollaborationOptions {
  roomId?: string;
  enabled?: boolean;
  onConnected?: () => void;
  onDisconnected?: () => void;
  onError?: (error: string) => void;
}

export const useCollaboration = (options: UseCollaborationOptions = {}) => {
  const { roomId, enabled = true, onConnected, onDisconnected, onError } = options;

  const socketRef = useRef<Socket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>();
  const cursorThrottleRef = useRef<ReturnType<typeof setTimeout>>();

  const {
    setConnected,
    setConnecting,
    setError,
    setSessionId,
    setCurrentRoom,
    setMyColor,
    updateCollaborators,
    updateCursor,
    addLock,
    removeLock,
    clearCollaborators,
    clearCursors,
    clearLocks,
    reset,
  } = useCollaborationStore();

  /**
   * Initialize WebSocket connection
   */
  const connect = useCallback(() => {
    if (socketRef.current?.connected || !enabled) {
      return;
    }

    setConnecting(true);
    setError(null);

    // Get auth token from localStorage
    const token = localStorage.getItem('token');
    if (!token) {
      setError('Authentication required');
      setConnecting(false);
      return;
    }

    // Connect to WebSocket server
    const socket = io(import.meta.env.VITE_API_URL || 'http://localhost:5000', {
      auth: {
        token,
      },
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 5,
    });

    socketRef.current = socket;

    // Connection events
    socket.on('connect', () => {
      console.log('WebSocket connected');
      setConnected(true);
      setConnecting(false);
      setError(null);
      onConnected?.();
    });

    socket.on('connected', (data: { session_id: string }) => {
      console.log('Session ID:', data.session_id);
      setSessionId(data.session_id);
    });

    socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      setConnected(false);
      clearCollaborators();
      clearCursors();
      onDisconnected?.();

      // Attempt to reconnect
      if (reason === 'io server disconnect') {
        // Server disconnected, try to reconnect
        reconnectTimeoutRef.current = setTimeout(() => {
          socket.connect();
        }, 2000);
      }
    });

    socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      setError(error.message);
      setConnecting(false);
      onError?.(error.message);
    });

    // Room events
    socket.on('room_joined', (data: { room_id: string; user_id: string; color: string }) => {
      console.log('Joined room:', data);
      setCurrentRoom(data.room_id);
      setMyColor(data.color);
    });

    // Presence events
    socket.on('presence_update', (data: { users: any[] }) => {
      console.log('Presence update:', data.users);
      updateCollaborators(data.users);
    });

    // Cursor events
    socket.on(
      'cursor_moved',
      (data: { user_id: string; session_id: string; x: number; y: number }) => {
        // Get collaborator info to get color and username
        const collaborator = useCollaborationStore
          .getState()
          .getCollaboratorBySessionId(data.session_id);

        if (collaborator) {
          updateCursor(
            data.session_id,
            data.x,
            data.y,
            collaborator.color,
            collaborator.username
          );
        }
      }
    );

    // Lock events
    socket.on('shape_locked', (data: { shape_id: string; user_id: string }) => {
      console.log('Shape locked:', data);
      addLock(data.shape_id, data.user_id);
    });

    socket.on('shape_unlocked', (data: { shape_id: string }) => {
      console.log('Shape unlocked:', data);
      removeLock(data.shape_id);
    });

    socket.on('shape_lock_failed', (data: { shape_id: string; locked_by: string }) => {
      console.warn('Shape lock failed:', data);
      // You might want to show a notification here
    });

    // Shape update events
    socket.on(
      'shape_updated',
      (data: { shape_id: string; shape_data: any; user_id: string }) => {
        console.log('Shape updated:', data);
        // Emit custom event that can be listened to by canvas components
        window.dispatchEvent(
          new CustomEvent('collaboration:shape_updated', {
            detail: data,
          })
        );
      }
    );

    // Error events
    socket.on('error', (data: { message: string }) => {
      console.error('WebSocket error:', data.message);
      setError(data.message);
      onError?.(data.message);
    });

    return socket;
  }, [
    enabled,
    setConnected,
    setConnecting,
    setError,
    setSessionId,
    setCurrentRoom,
    setMyColor,
    updateCollaborators,
    updateCursor,
    addLock,
    removeLock,
    clearCollaborators,
    clearCursors,
    onConnected,
    onDisconnected,
    onError,
  ]);

  /**
   * Disconnect from WebSocket
   */
  const disconnect = useCallback(() => {
    if (socketRef.current) {
      socketRef.current.disconnect();
      socketRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    reset();
  }, [reset]);

  /**
   * Join a collaboration room
   */
  const joinRoom = useCallback(
    (targetRoomId: string) => {
      if (!socketRef.current?.connected) {
        console.warn('Cannot join room: not connected');
        return;
      }

      console.log('Joining room:', targetRoomId);
      socketRef.current.emit('join_room', { room_id: targetRoomId });
    },
    []
  );

  /**
   * Leave current room
   */
  const leaveRoom = useCallback(() => {
    const currentRoom = useCollaborationStore.getState().currentRoom;
    if (!socketRef.current?.connected || !currentRoom) {
      return;
    }

    console.log('Leaving room:', currentRoom);
    socketRef.current.emit('leave_room', { room_id: currentRoom });
    setCurrentRoom(null);
    clearCollaborators();
    clearCursors();
    clearLocks();
  }, [setCurrentRoom, clearCollaborators, clearCursors, clearLocks]);

  /**
   * Send cursor position (throttled)
   */
  const sendCursorPosition = useCallback(
    (x: number, y: number) => {
      const currentRoom = useCollaborationStore.getState().currentRoom;
      if (!socketRef.current?.connected || !currentRoom) {
        return;
      }

      // Throttle cursor updates to avoid overwhelming the server
      if (cursorThrottleRef.current) {
        clearTimeout(cursorThrottleRef.current);
      }

      cursorThrottleRef.current = setTimeout(() => {
        socketRef.current?.emit('cursor_move', {
          room_id: currentRoom,
          x,
          y,
        });
      }, 50); // 20 updates per second max
    },
    []
  );

  /**
   * Request to lock a shape
   */
  const lockShape = useCallback(
    (shapeId: string) => {
      const currentRoom = useCollaborationStore.getState().currentRoom;
      if (!socketRef.current?.connected || !currentRoom) {
        return Promise.reject(new Error('Not connected'));
      }

      return new Promise<void>((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error('Lock timeout'));
        }, 5000);

        const handleLocked = (data: { shape_id: string }) => {
          if (data.shape_id === shapeId) {
            clearTimeout(timeout);
            socketRef.current?.off('shape_locked', handleLocked);
            socketRef.current?.off('shape_lock_failed', handleFailed);
            resolve();
          }
        };

        const handleFailed = (data: { shape_id: string }) => {
          if (data.shape_id === shapeId) {
            clearTimeout(timeout);
            socketRef.current?.off('shape_locked', handleLocked);
            socketRef.current?.off('shape_lock_failed', handleFailed);
            reject(new Error('Shape is locked by another user'));
          }
        };

        socketRef.current?.on('shape_locked', handleLocked);
        socketRef.current?.on('shape_lock_failed', handleFailed);

        socketRef.current?.emit('shape_lock', {
          room_id: currentRoom,
          shape_id: shapeId,
        });
      });
    },
    []
  );

  /**
   * Release shape lock
   */
  const unlockShape = useCallback(
    (shapeId: string) => {
      const currentRoom = useCollaborationStore.getState().currentRoom;
      if (!socketRef.current?.connected || !currentRoom) {
        return;
      }

      socketRef.current.emit('shape_unlock', {
        room_id: currentRoom,
        shape_id: shapeId,
      });
    },
    []
  );

  /**
   * Send shape update
   */
  const sendShapeUpdate = useCallback(
    (shapeId: string, shapeData: any) => {
      const currentRoom = useCollaborationStore.getState().currentRoom;
      if (!socketRef.current?.connected || !currentRoom) {
        return;
      }

      socketRef.current.emit('shape_update', {
        room_id: currentRoom,
        shape_id: shapeId,
        shape_data: shapeData,
      });
    },
    []
  );

  /**
   * Request current presence
   */
  const requestPresence = useCallback(() => {
    const currentRoom = useCollaborationStore.getState().currentRoom;
    if (!socketRef.current?.connected || !currentRoom) {
      return;
    }

    socketRef.current.emit('request_presence', {
      room_id: currentRoom,
    });
  }, []);

  // Auto-connect on mount if enabled
  useEffect(() => {
    if (enabled) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [enabled, connect, disconnect]);

  // Auto-join room if roomId changes
  useEffect(() => {
    if (roomId && socketRef.current?.connected) {
      joinRoom(roomId);
    }

    return () => {
      if (roomId) {
        leaveRoom();
      }
    };
  }, [roomId, joinRoom, leaveRoom]);

  return {
    connect,
    disconnect,
    joinRoom,
    leaveRoom,
    sendCursorPosition,
    lockShape,
    unlockShape,
    sendShapeUpdate,
    requestPresence,
    socket: socketRef.current,
  };
};
