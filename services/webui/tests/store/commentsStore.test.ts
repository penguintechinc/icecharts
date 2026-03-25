/**
 * Comments Store Tests (Zustand)
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { act } from '@testing-library/react';

vi.mock('@/lib/api', () => ({
  api: {
    comments: {
      list: vi.fn(),
      getSummary: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
      resolve: vi.fn(),
      unresolve: vi.fn(),
    },
  },
  default: { get: vi.fn() },
}));

import { useCommentsStore } from '@/store/commentsStore';
import { api } from '@/lib/api';

// Comment type from the store
interface Comment {
  id: string;
  drawing_id: string;
  content: string;
  author_id: number;
  author_name: string;
  is_resolved: boolean;
  created_at: string;
  updated_at: string;
}

const makeComment = (overrides: Partial<Comment> = {}): Comment => ({
  id: 'comment-1',
  drawing_id: 'drawing-1',
  content: 'Test comment',
  author_id: 1,
  author_name: 'Test User',
  is_resolved: false,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  ...overrides,
});

describe('commentsStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useCommentsStore.setState({
      commentsByDrawing: {},
      summaryByDrawing: {},
      isLoading: false,
      error: null,
      filterType: 'all',
      selectedShapeId: null,
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Initial State', () => {
    it('starts with empty comments by drawing', () => {
      expect(useCommentsStore.getState().commentsByDrawing).toEqual({});
    });

    it('starts with isLoading false', () => {
      expect(useCommentsStore.getState().isLoading).toBe(false);
    });

    it('starts with null error', () => {
      expect(useCommentsStore.getState().error).toBeNull();
    });

    it('starts with filterType all', () => {
      expect(useCommentsStore.getState().filterType).toBe('all');
    });
  });

  describe('fetchComments', () => {
    it('fetches and stores comments for a drawing', async () => {
      const comments = [makeComment(), makeComment({ id: 'comment-2', content: 'Second comment' })];
      (api.comments.list as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: { comments },
      });

      await act(async () => {
        await useCommentsStore.getState().fetchComments('drawing-1');
      });

      expect(useCommentsStore.getState().commentsByDrawing['drawing-1']).toHaveLength(2);
    });

    it('handles fetch error', async () => {
      (api.comments.list as ReturnType<typeof vi.fn>).mockRejectedValue(
        new Error('Failed to fetch')
      );

      await act(async () => {
        await useCommentsStore.getState().fetchComments('drawing-1');
      });

      expect(useCommentsStore.getState().error).toBe('Failed to fetch');
      expect(useCommentsStore.getState().isLoading).toBe(false);
    });

    it('sets isLoading false after fetch', async () => {
      (api.comments.list as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: { comments: [] },
      });

      await act(async () => {
        await useCommentsStore.getState().fetchComments('drawing-1');
      });

      expect(useCommentsStore.getState().isLoading).toBe(false);
    });
  });

  describe('fetchSummary', () => {
    it('stores summary for a drawing', async () => {
      const summary = { total: 5, resolved: 2, open: 3 };
      (api.comments.getSummary as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: summary,
      });

      await act(async () => {
        await useCommentsStore.getState().fetchSummary('drawing-1');
      });

      expect(useCommentsStore.getState().summaryByDrawing['drawing-1']).toEqual(summary);
    });

    it('sets error on fetch failure', async () => {
      (api.comments.getSummary as ReturnType<typeof vi.fn>).mockRejectedValue(
        new Error('Summary error')
      );

      await act(async () => {
        await useCommentsStore.getState().fetchSummary('drawing-1');
      });

      expect(useCommentsStore.getState().error).toBe('Summary error');
    });
  });

  describe('createComment', () => {
    it('adds new comment to the drawing', async () => {
      const newComment = makeComment({ id: 'comment-new' });
      (api.comments.create as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: { comment: newComment },
      });

      await act(async () => {
        await useCommentsStore.getState().createComment('drawing-1', 'New comment text');
      });

      expect(useCommentsStore.getState().commentsByDrawing['drawing-1']).toHaveLength(1);
      expect(useCommentsStore.getState().commentsByDrawing['drawing-1'][0].id).toBe('comment-new');
    });

    it('returns null on failure', async () => {
      (api.comments.create as ReturnType<typeof vi.fn>).mockRejectedValue(
        new Error('Create failed')
      );

      let result: Comment | null = makeComment();
      await act(async () => {
        result = await useCommentsStore.getState().createComment('drawing-1', 'text');
      });

      expect(result).toBeNull();
      expect(useCommentsStore.getState().error).toBe('Create failed');
    });

    it('appends to existing comments', async () => {
      const existingComment = makeComment({ id: 'comment-existing' });
      useCommentsStore.setState({
        commentsByDrawing: { 'drawing-1': [existingComment] },
      });

      const newComment = makeComment({ id: 'comment-new' });
      (api.comments.create as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: { comment: newComment },
      });

      await act(async () => {
        await useCommentsStore.getState().createComment('drawing-1', 'New comment');
      });

      expect(useCommentsStore.getState().commentsByDrawing['drawing-1']).toHaveLength(2);
    });
  });

  describe('updateComment', () => {
    it('updates comment in the store', async () => {
      const existingComment = makeComment({ id: 'comment-1', content: 'Original' });
      useCommentsStore.setState({
        commentsByDrawing: { 'drawing-1': [existingComment] },
      });

      const updatedComment = makeComment({ id: 'comment-1', content: 'Updated' });
      (api.comments.update as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: { comment: updatedComment },
      });

      await act(async () => {
        await useCommentsStore.getState().updateComment('drawing-1', 'comment-1', 'Updated');
      });

      const comments = useCommentsStore.getState().commentsByDrawing['drawing-1'];
      expect(comments[0].content).toBe('Updated');
    });

    it('returns null on failure', async () => {
      (api.comments.update as ReturnType<typeof vi.fn>).mockRejectedValue(
        new Error('Update failed')
      );

      let result: Comment | null = makeComment();
      await act(async () => {
        result = await useCommentsStore.getState().updateComment('drawing-1', 'comment-1', 'text');
      });

      expect(result).toBeNull();
    });
  });

  describe('deleteComment', () => {
    it('removes comment from the store', async () => {
      const comment1 = makeComment({ id: 'comment-1' });
      const comment2 = makeComment({ id: 'comment-2' });
      useCommentsStore.setState({
        commentsByDrawing: { 'drawing-1': [comment1, comment2] },
      });

      (api.comments.delete as ReturnType<typeof vi.fn>).mockResolvedValue({});

      await act(async () => {
        await useCommentsStore.getState().deleteComment('drawing-1', 'comment-1');
      });

      const comments = useCommentsStore.getState().commentsByDrawing['drawing-1'];
      expect(comments).toHaveLength(1);
      expect(comments[0].id).toBe('comment-2');
    });

    it('returns true on success', async () => {
      useCommentsStore.setState({
        commentsByDrawing: { 'drawing-1': [makeComment()] },
      });
      (api.comments.delete as ReturnType<typeof vi.fn>).mockResolvedValue({});

      let result = false;
      await act(async () => {
        result = await useCommentsStore.getState().deleteComment('drawing-1', 'comment-1');
      });

      expect(result).toBe(true);
    });

    it('returns false on failure', async () => {
      (api.comments.delete as ReturnType<typeof vi.fn>).mockRejectedValue(
        new Error('Delete failed')
      );

      let result = true;
      await act(async () => {
        result = await useCommentsStore.getState().deleteComment('drawing-1', 'comment-1');
      });

      expect(result).toBe(false);
    });
  });

  describe('resolveComment', () => {
    it('updates resolved state', async () => {
      const comment = makeComment({ id: 'comment-1', is_resolved: false });
      useCommentsStore.setState({
        commentsByDrawing: { 'drawing-1': [comment] },
      });

      const resolved = makeComment({ id: 'comment-1', is_resolved: true });
      (api.comments.resolve as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: { comment: resolved },
      });

      await act(async () => {
        await useCommentsStore.getState().resolveComment('drawing-1', 'comment-1');
      });

      const comments = useCommentsStore.getState().commentsByDrawing['drawing-1'];
      expect(comments[0].is_resolved).toBe(true);
    });
  });

  describe('unresolveComment', () => {
    it('updates unresolved state', async () => {
      const comment = makeComment({ id: 'comment-1', is_resolved: true });
      useCommentsStore.setState({
        commentsByDrawing: { 'drawing-1': [comment] },
      });

      const unresolved = makeComment({ id: 'comment-1', is_resolved: false });
      (api.comments.unresolve as ReturnType<typeof vi.fn>).mockResolvedValue({
        data: { comment: unresolved },
      });

      await act(async () => {
        await useCommentsStore.getState().unresolveComment('drawing-1', 'comment-1');
      });

      const comments = useCommentsStore.getState().commentsByDrawing['drawing-1'];
      expect(comments[0].is_resolved).toBe(false);
    });
  });

  describe('setFilterType', () => {
    it('updates filter type', () => {
      act(() => {
        useCommentsStore.getState().setFilterType('resolved');
      });
      expect(useCommentsStore.getState().filterType).toBe('resolved');
    });
  });

  describe('setSelectedShapeId', () => {
    it('updates selected shape ID', () => {
      act(() => {
        useCommentsStore.getState().setSelectedShapeId('shape-abc');
      });
      expect(useCommentsStore.getState().selectedShapeId).toBe('shape-abc');
    });

    it('can clear selected shape ID', () => {
      useCommentsStore.setState({ selectedShapeId: 'shape-abc' });
      act(() => {
        useCommentsStore.getState().setSelectedShapeId(null);
      });
      expect(useCommentsStore.getState().selectedShapeId).toBeNull();
    });
  });

  describe('clearError', () => {
    it('clears the error', () => {
      useCommentsStore.setState({ error: 'Some error' });
      act(() => {
        useCommentsStore.getState().clearError();
      });
      expect(useCommentsStore.getState().error).toBeNull();
    });
  });

  describe('clearDrawingComments', () => {
    it('removes comments for a specific drawing', () => {
      useCommentsStore.setState({
        commentsByDrawing: {
          'drawing-1': [makeComment()],
          'drawing-2': [makeComment({ id: 'comment-x', drawing_id: 'drawing-2' })],
        },
      });

      act(() => {
        useCommentsStore.getState().clearDrawingComments('drawing-1');
      });

      const state = useCommentsStore.getState();
      expect(state.commentsByDrawing['drawing-1']).toBeUndefined();
      expect(state.commentsByDrawing['drawing-2']).toHaveLength(1);
    });
  });
});
