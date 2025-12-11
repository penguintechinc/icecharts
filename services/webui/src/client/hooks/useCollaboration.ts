/**
 * useCollaboration Hook - Real-time collaboration for DrawingEditor
 * Manages WebSocket connection, cursor tracking, and attention gestures
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import { io, Socket } from 'socket.io-client';

interface Collaborator {
  user_id: number;
  username: string;
  permission: 'viewer' | 'editor' | 'admin';
  cursor?: { x: number; y: number };
  color: string; // Assigned color for cursor
}

interface AttentionClick {
  x: number;
  y: number;
  timestamp: number;
  user_id: number;
  username: string;
}

interface UseCollaborationReturn {
  collaborators: Collaborator[];
  attentionClicks: AttentionClick[];
  isConnected: boolean;
  updateCursorPosition: (x: number, y: number) => void;
  triggerAttentionClick: (x: number, y: number) => void;
  broadcastChange: (changeType: string, changeData: any) => void;
}

const COLORS = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE'];

/**
 * Assign a random color to a collaborator
 */
function assignColor(): string {
  return COLORS[Math.floor(Math.random() * COLORS.length)];
}

/**
 * Throttle function to limit execution rate
 * @param func Function to throttle
 * @param limit Time limit in milliseconds
 */
function throttle<T extends (...args: any[]) => void>(func: T, limit: number): T {
  let inThrottle = false;
  return ((...args: any[]) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => {
        inThrottle = false;
      }, limit);
    }
  }) as T;
}

/**
 * Hook for managing real-time collaboration in DrawingEditor
 * @param drawingId ID of the drawing to collaborate on
 */
export const useCollaboration = (drawingId: number | string | undefined): UseCollaborationReturn => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [collaborators, setCollaborators] = useState<Collaborator[]>([]);
  const [attentionClicks, setAttentionClicks] = useState<AttentionClick[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  const socketRef = useRef<Socket | null>(null);

  // Get auth token from localStorage
  const getAuthToken = useCallback(() => {
    return localStorage.getItem('authToken');
  }, []);

  // Throttled cursor position update - 30 FPS (33ms)
  const updateCursorPosition = useCallback(
    throttle((x: number, y: number) => {
      if (socketRef.current && isConnected && drawingId) {
        socketRef.current.emit('cursor_move', {
          drawing_id: drawingId,
          x,
          y,
        });
      }
    }, 33),
    [isConnected, drawingId]
  );

  // Trigger attention-grabbing click animation
  const triggerAttentionClick = useCallback(
    (x: number, y: number) => {
      if (socketRef.current && isConnected && drawingId) {
        socketRef.current.emit('attention_click', {
          drawing_id: drawingId,
          x,
          y,
        });
      }
    },
    [isConnected, drawingId]
  );

  // Broadcast drawing change to other users
  const broadcastChange = useCallback(
    (changeType: string, changeData: any) => {
      if (socketRef.current && isConnected && drawingId) {
        socketRef.current.emit('drawing_change', {
          drawing_id: drawingId,
          change_type: changeType,
          change_data: changeData,
        });
      }
    },
    [isConnected, drawingId]
  );

  useEffect(() => {
    // Don't connect if no drawing ID
    if (!drawingId) {
      return;
    }

    const token = getAuthToken();
    if (!token) {
      console.warn('No auth token found, skipping collaboration connection');
      return;
    }

    // Connect to WebSocket server
    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';
    const newSocket = io(API_URL, {
      auth: {
        token,
      },
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 5,
    });

    socketRef.current = newSocket;
    setSocket(newSocket);

    // Connection established
    newSocket.on('connect', () => {
      console.log('WebSocket connected for collaboration');
      setIsConnected(true);

      // Join the drawing room
      newSocket.emit('join_drawing', { drawing_id: drawingId });
    });

    // Receive list of active collaborators
    newSocket.on('collaborators_list', (data: { collaborators: any[] }) => {
      console.log('Received collaborators list:', data.collaborators);
      const collaboratorsWithColors = data.collaborators.map((collab) => ({
        ...collab,
        color: collab.color || assignColor(),
      }));
      setCollaborators(collaboratorsWithColors);
    });

    // User joined the drawing
    newSocket.on('user_joined', (data: { user_id: number; username: string; permission: string }) => {
      console.log('User joined:', data);
      const newCollaborator: Collaborator = {
        user_id: data.user_id,
        username: data.username,
        permission: data.permission as 'viewer' | 'editor' | 'admin',
        color: assignColor(),
      };
      setCollaborators((prev) => {
        // Check if user already exists (avoid duplicates)
        if (prev.some((c) => c.user_id === data.user_id)) {
          return prev;
        }
        return [...prev, newCollaborator];
      });
    });

    // User left the drawing
    newSocket.on('user_left', (data: { user_id: number }) => {
      console.log('User left:', data);
      setCollaborators((prev) => prev.filter((c) => c.user_id !== data.user_id));
    });

    // Cursor position updated
    newSocket.on('cursor_moved', (data: { user_id: number; username: string; x: number; y: number }) => {
      setCollaborators((prev) =>
        prev.map((c) =>
          c.user_id === data.user_id
            ? { ...c, cursor: { x: data.x, y: data.y } }
            : c
        )
      );
    });

    // Attention click received
    newSocket.on('attention_click', (data: { user_id: number; username: string; x: number; y: number }) => {
      console.log('Attention click:', data);
      const clickEvent: AttentionClick = {
        x: data.x,
        y: data.y,
        timestamp: Date.now(),
        user_id: data.user_id,
        username: data.username,
      };
      setAttentionClicks((prev) => [...prev, clickEvent]);

      // Auto-remove after animation completes (2 seconds)
      setTimeout(() => {
        setAttentionClicks((prev) => prev.filter((c) => c.timestamp !== clickEvent.timestamp));
      }, 2000);
    });

    // Drawing changed by another user
    newSocket.on('drawing_changed', (data: { user_id: number; change_type: string; change_data: any }) => {
      console.log('Drawing changed:', data);
      // Emit custom event that DrawingEditor can listen to
      window.dispatchEvent(
        new CustomEvent('collaboration:drawing_changed', {
          detail: data,
        })
      );
    });

    // Disconnection
    newSocket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      setIsConnected(false);
      setCollaborators([]);
    });

    // Error handling
    newSocket.on('error', (data: { message: string }) => {
      console.error('WebSocket error:', data.message);
    });

    // Cleanup on unmount
    return () => {
      console.log('Cleaning up collaboration connection');
      if (newSocket.connected) {
        newSocket.emit('leave_drawing', { drawing_id: drawingId });
        newSocket.disconnect();
      }
      socketRef.current = null;
      setSocket(null);
      setIsConnected(false);
      setCollaborators([]);
      setAttentionClicks([]);
    };
  }, [drawingId, getAuthToken]);

  return {
    collaborators,
    attentionClicks,
    isConnected,
    updateCursorPosition,
    triggerAttentionClick,
    broadcastChange,
  };
};
