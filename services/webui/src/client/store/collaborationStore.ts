/**
 * Collaboration Store - Manages real-time collaboration state
 * Uses Zustand for state management
 */

import { create } from 'zustand';

export interface Collaborator {
  userId: string;
  username: string;
  email: string;
  color: string;
  sessionId: string;
  cursorX: number;
  cursorY: number;
  lastSeen: number;
}

export interface ShapeLock {
  shapeId: string;
  userId: string;
  lockedAt: number;
}

interface CollaborationState {
  // Connection state
  connected: boolean;
  connecting: boolean;
  error: string | null;
  sessionId: string | null;

  // Current room
  currentRoom: string | null;
  myColor: string | null;

  // Collaborators
  collaborators: Map<string, Collaborator>;

  // Shape locks
  shapeLocks: Map<string, ShapeLock>;

  // Cursor positions (sessionId -> position)
  cursors: Map<string, { x: number; y: number; color: string; username: string }>;

  // Actions
  setConnected: (connected: boolean) => void;
  setConnecting: (connecting: boolean) => void;
  setError: (error: string | null) => void;
  setSessionId: (sessionId: string | null) => void;
  setCurrentRoom: (roomId: string | null) => void;
  setMyColor: (color: string | null) => void;

  // Collaborator actions
  addCollaborator: (collaborator: Collaborator) => void;
  removeCollaborator: (sessionId: string) => void;
  updateCollaborators: (collaborators: Collaborator[]) => void;
  clearCollaborators: () => void;

  // Cursor actions
  updateCursor: (sessionId: string, x: number, y: number, color: string, username: string) => void;
  removeCursor: (sessionId: string) => void;
  clearCursors: () => void;

  // Lock actions
  addLock: (shapeId: string, userId: string) => void;
  removeLock: (shapeId: string) => void;
  isShapeLocked: (shapeId: string) => boolean;
  getShapeLock: (shapeId: string) => ShapeLock | undefined;
  clearLocks: () => void;

  // Helpers
  getCollaboratorBySessionId: (sessionId: string) => Collaborator | undefined;
  getCollaboratorsList: () => Collaborator[];
  reset: () => void;
}

export const useCollaborationStore = create<CollaborationState>((set, get) => ({
  // Initial state
  connected: false,
  connecting: false,
  error: null,
  sessionId: null,
  currentRoom: null,
  myColor: null,
  collaborators: new Map(),
  shapeLocks: new Map(),
  cursors: new Map(),

  // Connection actions
  setConnected: (connected) => set({ connected }),
  setConnecting: (connecting) => set({ connecting }),
  setError: (error) => set({ error }),
  setSessionId: (sessionId) => set({ sessionId }),
  setCurrentRoom: (roomId) => set({ currentRoom: roomId }),
  setMyColor: (color) => set({ myColor: color }),

  // Collaborator actions
  addCollaborator: (collaborator) =>
    set((state) => {
      const newCollaborators = new Map(state.collaborators);
      newCollaborators.set(collaborator.sessionId, collaborator);
      return { collaborators: newCollaborators };
    }),

  removeCollaborator: (sessionId) =>
    set((state) => {
      const newCollaborators = new Map(state.collaborators);
      newCollaborators.delete(sessionId);

      // Also remove cursor
      const newCursors = new Map(state.cursors);
      newCursors.delete(sessionId);

      return { collaborators: newCollaborators, cursors: newCursors };
    }),

  updateCollaborators: (collaborators) =>
    set(() => {
      const newCollaborators = new Map<string, Collaborator>();
      collaborators.forEach((collab) => {
        newCollaborators.set(collab.sessionId, collab);
      });
      return { collaborators: newCollaborators };
    }),

  clearCollaborators: () =>
    set({
      collaborators: new Map(),
      cursors: new Map(),
    }),

  // Cursor actions
  updateCursor: (sessionId, x, y, color, username) =>
    set((state) => {
      // Don't track our own cursor
      if (sessionId === state.sessionId) {
        return state;
      }

      const newCursors = new Map(state.cursors);
      newCursors.set(sessionId, { x, y, color, username });
      return { cursors: newCursors };
    }),

  removeCursor: (sessionId) =>
    set((state) => {
      const newCursors = new Map(state.cursors);
      newCursors.delete(sessionId);
      return { cursors: newCursors };
    }),

  clearCursors: () => set({ cursors: new Map() }),

  // Lock actions
  addLock: (shapeId, userId) =>
    set((state) => {
      const newLocks = new Map(state.shapeLocks);
      newLocks.set(shapeId, { shapeId, userId, lockedAt: Date.now() });
      return { shapeLocks: newLocks };
    }),

  removeLock: (shapeId) =>
    set((state) => {
      const newLocks = new Map(state.shapeLocks);
      newLocks.delete(shapeId);
      return { shapeLocks: newLocks };
    }),

  isShapeLocked: (shapeId) => {
    const state = get();
    return state.shapeLocks.has(shapeId);
  },

  getShapeLock: (shapeId) => {
    const state = get();
    return state.shapeLocks.get(shapeId);
  },

  clearLocks: () => set({ shapeLocks: new Map() }),

  // Helpers
  getCollaboratorBySessionId: (sessionId) => {
    const state = get();
    return state.collaborators.get(sessionId);
  },

  getCollaboratorsList: () => {
    const state = get();
    return Array.from(state.collaborators.values());
  },

  reset: () =>
    set({
      connected: false,
      connecting: false,
      error: null,
      sessionId: null,
      currentRoom: null,
      myColor: null,
      collaborators: new Map(),
      shapeLocks: new Map(),
      cursors: new Map(),
    }),
}));
