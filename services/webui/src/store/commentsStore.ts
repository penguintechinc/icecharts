import { create } from 'zustand';
import { api } from '../lib/api';
import type { Comment, CommentSummary } from '../types';

interface CommentsState {
  commentsByDrawing: Record<string, Comment[]>;
  summaryByDrawing: Record<string, CommentSummary>;
  isLoading: boolean;
  error: string | null;
  filterType: 'all' | 'open' | 'resolved';
  selectedShapeId: string | null;

  // Actions
  fetchComments: (drawingId: string, filters?: { shape_id?: string; filter?: 'all' | 'open' | 'resolved'; thread?: boolean }) => Promise<void>;
  fetchSummary: (drawingId: string) => Promise<void>;
  createComment: (drawingId: string, content: string, shape_id?: string, parent_comment_id?: string) => Promise<Comment | null>;
  updateComment: (drawingId: string, commentId: string, content: string) => Promise<Comment | null>;
  deleteComment: (drawingId: string, commentId: string) => Promise<boolean>;
  resolveComment: (drawingId: string, commentId: string) => Promise<Comment | null>;
  unresolveComment: (drawingId: string, commentId: string) => Promise<Comment | null>;
  setFilterType: (filter: 'all' | 'open' | 'resolved') => void;
  setSelectedShapeId: (shapeId: string | null) => void;
  clearError: () => void;
  clearDrawingComments: (drawingId: string) => void;
}

export const useCommentsStore = create<CommentsState>((set) => ({
  commentsByDrawing: {},
  summaryByDrawing: {},
  isLoading: false,
  error: null,
  filterType: 'all',
  selectedShapeId: null,

  fetchComments: async (drawingId: string, filters?: { shape_id?: string; filter?: 'all' | 'open' | 'resolved'; thread?: boolean }) => {
    try {
      set({ isLoading: true, error: null });
      const response = await api.comments.list(drawingId, filters);
      const comments = response.data.comments || [];

      set((state) => ({
        commentsByDrawing: {
          ...state.commentsByDrawing,
          [drawingId]: comments,
        },
        isLoading: false,
      }));
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch comments';
      set({ error: errorMessage, isLoading: false });
    }
  },

  fetchSummary: async (drawingId: string) => {
    try {
      set({ error: null });
      const response = await api.comments.getSummary(drawingId);

      set((state) => ({
        summaryByDrawing: {
          ...state.summaryByDrawing,
          [drawingId]: response.data,
        },
      }));
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch summary';
      set({ error: errorMessage });
    }
  },

  createComment: async (drawingId: string, content: string, shape_id?: string, parent_comment_id?: string) => {
    try {
      set({ error: null });
      const response = await api.comments.create(drawingId, {
        content,
        shape_id,
        parent_comment_id,
      });

      const newComment = response.data.comment as Comment;

      set((state) => ({
        commentsByDrawing: {
          ...state.commentsByDrawing,
          [drawingId]: [...(state.commentsByDrawing[drawingId] || []), newComment],
        },
      }));

      return newComment;
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to create comment';
      set({ error: errorMessage });
      return null;
    }
  },

  updateComment: async (drawingId: string, commentId: string, content: string) => {
    try {
      set({ error: null });
      const response = await api.comments.update(drawingId, commentId, { content });
      const updatedComment = response.data.comment as Comment;

      set((state) => ({
        commentsByDrawing: {
          ...state.commentsByDrawing,
          [drawingId]: (state.commentsByDrawing[drawingId] || []).map((c) =>
            c.id === commentId ? updatedComment : c
          ),
        },
      }));

      return updatedComment;
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to update comment';
      set({ error: errorMessage });
      return null;
    }
  },

  deleteComment: async (drawingId: string, commentId: string) => {
    try {
      set({ error: null });
      await api.comments.delete(drawingId, commentId);

      set((state) => ({
        commentsByDrawing: {
          ...state.commentsByDrawing,
          [drawingId]: (state.commentsByDrawing[drawingId] || []).filter((c) => c.id !== commentId),
        },
      }));

      return true;
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to delete comment';
      set({ error: errorMessage });
      return false;
    }
  },

  resolveComment: async (drawingId: string, commentId: string) => {
    try {
      set({ error: null });
      const response = await api.comments.resolve(drawingId, commentId);
      const updatedComment = response.data.comment as Comment;

      set((state) => ({
        commentsByDrawing: {
          ...state.commentsByDrawing,
          [drawingId]: (state.commentsByDrawing[drawingId] || []).map((c) =>
            c.id === commentId ? updatedComment : c
          ),
        },
      }));

      return updatedComment;
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to resolve comment';
      set({ error: errorMessage });
      return null;
    }
  },

  unresolveComment: async (drawingId: string, commentId: string) => {
    try {
      set({ error: null });
      const response = await api.comments.unresolve(drawingId, commentId);
      const updatedComment = response.data.comment as Comment;

      set((state) => ({
        commentsByDrawing: {
          ...state.commentsByDrawing,
          [drawingId]: (state.commentsByDrawing[drawingId] || []).map((c) =>
            c.id === commentId ? updatedComment : c
          ),
        },
      }));

      return updatedComment;
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to unresolve comment';
      set({ error: errorMessage });
      return null;
    }
  },

  setFilterType: (filter: 'all' | 'open' | 'resolved') => {
    set({ filterType: filter });
  },

  setSelectedShapeId: (shapeId: string | null) => {
    set({ selectedShapeId: shapeId });
  },

  clearError: () => set({ error: null }),

  clearDrawingComments: (drawingId: string) => {
    set((state) => {
      const newCommentsByDrawing = { ...state.commentsByDrawing };
      delete newCommentsByDrawing[drawingId];
      return { commentsByDrawing: newCommentsByDrawing };
    });
  },
}));
