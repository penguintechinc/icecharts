import { io, Socket } from 'socket.io-client';

const SOCKET_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

interface WebSocketOptions {
  reconnection?: boolean;
  reconnectionAttempts?: number;
  reconnectionDelay?: number;
  autoConnect?: boolean;
}

class WebSocketClient {
  private socket: Socket | null = null;
  private eventHandlers: Map<string, Set<(...args: unknown[]) => void>> = new Map();
  private isConnected = false;

  constructor(private options: WebSocketOptions = {}) {
    this.options = {
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
      autoConnect: false,
      ...options,
    };
  }

  connect(token?: string): void {
    if (this.socket?.connected) {
      console.warn('WebSocket already connected');
      return;
    }

    const auth: { token?: string } = {};
    if (token) {
      auth.token = token;
    } else {
      const storedToken = localStorage.getItem('authToken');
      if (storedToken) {
        auth.token = storedToken;
      }
    }

    this.socket = io(SOCKET_URL, {
      ...this.options,
      auth,
      transports: ['websocket', 'polling'],
    });

    this.setupEventHandlers();
  }

  private setupEventHandlers(): void {
    if (!this.socket) return;

    // Connection events
    this.socket.on('connect', () => {
      this.isConnected = true;
      console.log('WebSocket connected:', this.socket?.id);
      this.emit('connection', { status: 'connected', socketId: this.socket?.id });
    });

    this.socket.on('disconnect', (reason: string) => {
      this.isConnected = false;
      console.log('WebSocket disconnected:', reason);
      this.emit('connection', { status: 'disconnected', reason });
    });

    this.socket.on('connect_error', (error: Error) => {
      console.error('WebSocket connection error:', error);
      this.emit('connection', { status: 'error', error: error.message });
    });

    this.socket.on('reconnect', (attemptNumber: number) => {
      console.log('WebSocket reconnected after', attemptNumber, 'attempts');
      this.emit('connection', { status: 'reconnected', attempts: attemptNumber });
    });

    this.socket.on('reconnect_error', (error: Error) => {
      console.error('WebSocket reconnection error:', error);
    });

    this.socket.on('reconnect_failed', () => {
      console.error('WebSocket reconnection failed');
      this.emit('connection', { status: 'reconnect_failed' });
    });

    // Re-register all event handlers
    this.eventHandlers.forEach((handlers, event) => {
      handlers.forEach((handler) => {
        this.socket?.on(event, handler);
      });
    });
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.isConnected = false;
    }
  }

  on(event: string, handler: (...args: unknown[]) => void): void {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, new Set());
    }
    this.eventHandlers.get(event)?.add(handler);

    if (this.socket) {
      this.socket.on(event, handler);
    }
  }

  off(event: string, handler?: (...args: unknown[]) => void): void {
    if (handler) {
      this.eventHandlers.get(event)?.delete(handler);
      if (this.socket) {
        this.socket.off(event, handler);
      }
    } else {
      this.eventHandlers.delete(event);
      if (this.socket) {
        this.socket.off(event);
      }
    }
  }

  emit(event: string, data?: unknown): void {
    if (this.socket) {
      this.socket.emit(event, data);
    } else {
      console.warn('Cannot emit event - socket not connected:', event);
    }
  }

  // Drawing-specific methods
  joinDrawing(drawingId: string): void {
    this.emit('join_drawing', { drawingId });
  }

  leaveDrawing(drawingId: string): void {
    this.emit('leave_drawing', { drawingId });
  }

  sendDrawingUpdate(drawingId: string, data: unknown): void {
    this.emit('drawing_update', { drawingId, data });
  }

  sendCursorPosition(drawingId: string, x: number, y: number): void {
    this.emit('cursor_position', { drawingId, x, y });
  }

  sendShapeUpdate(drawingId: string, shapeId: string, updates: unknown): void {
    this.emit('shape_update', { drawingId, shapeId, updates });
  }

  sendShapeDelete(drawingId: string, shapeId: string): void {
    this.emit('shape_delete', { drawingId, shapeId });
  }

  sendShapeCreate(drawingId: string, shape: unknown): void {
    this.emit('shape_create', { drawingId, shape });
  }

  get connected(): boolean {
    return this.isConnected && this.socket?.connected === true;
  }

  get socketId(): string | undefined {
    return this.socket?.id;
  }
}

// Export singleton instance
export const wsClient = new WebSocketClient();

export default wsClient;
