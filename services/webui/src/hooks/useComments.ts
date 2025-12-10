import { useCallback, useState } from 'react';
import { api } from '../lib/api';
import type { Comment, CommentSummary } from '../types';

interface UseCommentsReturn {
  comments: Comment[];
  summary: CommentSummary | null;
  isLoading: boolean;
  error: string | null;
  fetchComments: (drawingId: string, filters?: { shape_id?: string; filter?: 'all' | 'open' | 'resolved'; thread?: boolean }) => Promise<void>;
  fetchCommentsSummary: (drawingId: string) => Promise<void>;
  createComment: (drawingId: string, content: string, shape_id?: string, parent_comment_id?: string) => Promise<Comment | null>;
  updateComment: (drawingId: string, commentId: string, content: string) => Promise<Comment | null>;
  deleteComment: (drawingId: string, commentId: string) => Promise<boolean>;
  resolveComment: (drawingId: string, commentId: string) => Promise<Comment | null>;
  unresolveComment: (drawingId: string, commentId: string) => Promise<Comment | null>;
  clearError: () => void;
}

export const useComments = (): UseCommentsReturn => {
  const [comments, setComments] = useState<Comment[]>([]);
  const [summary, setSummary] = useState<CommentSummary | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => setError(null), []);

  const fetchComments = useCallback(
    async (drawingId: string, filters?: { shape_id?: string; filter?: 'all' | 'open' | 'resolved'; thread?: boolean }) => {
      try {
        setIsLoading(true);
        setError(null);
        const response = await api.comments.list(drawingId, filters);
        setComments(response.data.comments || []);
      } catch (err: unknown) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to fetch comments';
        setError(errorMessage);
        setComments([]);
      } finally {
        setIsLoading(false);
      }
    },
    []
  );

  const fetchCommentsSummary = useCallback(
    async (drawingId: string) => {
      try {
        setError(null);
        const response = await api.comments.getSummary(drawingId);
        setSummary(response.data);
      } catch (err: unknown) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to fetch summary';
        setError(errorMessage);
      }
    },
    []
  );

  const createComment = useCallback(
    async (drawingId: string, content: string, shape_id?: string, parent_comment_id?: string) => {
      try {
        setError(null);
        const response = await api.comments.create(drawingId, {
          content,
          shape_id,
          parent_comment_id,
        });
        const newComment = response.data.comment as Comment;
        setComments((prev) => [...prev, newComment]);
        return newComment;
      } catch (err: unknown) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to create comment';
        setError(errorMessage);
        return null;
      }
    },
    []
  );

  const updateComment = useCallback(
    async (drawingId: string, commentId: string, content: string) => {
      try {
        setError(null);
        const response = await api.comments.update(drawingId, commentId, { content });
        const updatedComment = response.data.comment as Comment;
        setComments((prev) =>
          prev.map((c) => (c.id === commentId ? updatedComment : c))
        );
        return updatedComment;
      } catch (err: unknown) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to update comment';
        setError(errorMessage);
        return null;
      }
    },
    []
  );

  const deleteComment = useCallback(
    async (drawingId: string, commentId: string) => {
      try {
        setError(null);
        await api.comments.delete(drawingId, commentId);
        setComments((prev) => prev.filter((c) => c.id !== commentId));
        return true;
      } catch (err: unknown) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to delete comment';
        setError(errorMessage);
        return false;
      }
    },
    []
  );

  const resolveComment = useCallback(
    async (drawingId: string, commentId: string) => {
      try {
        setError(null);
        const response = await api.comments.resolve(drawingId, commentId);
        const updatedComment = response.data.comment as Comment;
        setComments((prev) =>
          prev.map((c) => (c.id === commentId ? updatedComment : c))
        );
        return updatedComment;
      } catch (err: unknown) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to resolve comment';
        setError(errorMessage);
        return null;
      }
    },
    []
  );

  const unresolveComment = useCallback(
    async (drawingId: string, commentId: string) => {
      try {
        setError(null);
        const response = await api.comments.unresolve(drawingId, commentId);
        const updatedComment = response.data.comment as Comment;
        setComments((prev) =>
          prev.map((c) => (c.id === commentId ? updatedComment : c))
        );
        return updatedComment;
      } catch (err: unknown) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to unresolve comment';
        setError(errorMessage);
        return null;
      }
    },
    []
  );

  return {
    comments,
    summary,
    isLoading,
    error,
    fetchComments,
    fetchCommentsSummary,
    createComment,
    updateComment,
    deleteComment,
    resolveComment,
    unresolveComment,
    clearError,
  };
};
