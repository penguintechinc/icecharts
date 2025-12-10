import React, { useEffect, useState } from 'react';
import { useCommentsStore } from '../../store/commentsStore';
import { useAuthStore } from '../../store/authStore';
import { CommentThread } from '../common/CommentThread';
import type { Comment } from '../../types';

interface CommentsPanelProps {
  drawingId: string;
  selectedShapeId?: string;
  onClose?: () => void;
  isOpen: boolean;
}

export const CommentsPanel: React.FC<CommentsPanelProps> = ({
  drawingId,
  selectedShapeId,
  onClose,
  isOpen,
}) => {
  const user = useAuthStore((state) => state.user);
  const {
    commentsByDrawing,
    summaryByDrawing,
    isLoading,
    error,
    filterType,
    fetchComments,
    fetchSummary,
    createComment,
    updateComment,
    deleteComment,
    resolveComment,
    unresolveComment,
    setFilterType,
    clearError,
  } = useCommentsStore();

  const [newCommentContent, setNewCommentContent] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const comments = commentsByDrawing[drawingId] || [];
  const summary = summaryByDrawing[drawingId];

  useEffect(() => {
    if (isOpen && drawingId) {
      fetchComments(drawingId, { shape_id: selectedShapeId, filter: filterType });
      fetchSummary(drawingId);
    }
  }, [isOpen, drawingId, selectedShapeId, filterType, fetchComments, fetchSummary]);

  const handleCreateComment = async () => {
    if (!newCommentContent.trim() || !user) return;

    setIsSubmitting(true);
    try {
      await createComment(drawingId, newCommentContent, selectedShapeId);
      setNewCommentContent('');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUpdateComment = async (commentId: string, content: string) => {
    await updateComment(drawingId, commentId, content);
  };

  const handleDeleteComment = async (commentId: string) => {
    if (confirm('Are you sure you want to delete this comment?')) {
      await deleteComment(drawingId, commentId);
    }
  };

  const handleResolveComment = async (commentId: string) => {
    const comment = comments.find((c) => c.id === commentId);
    if (comment?.is_resolved) {
      await unresolveComment(drawingId, commentId);
    } else {
      await resolveComment(drawingId, commentId);
    }
  };

  const handleReplyComment = async (parentId: string, content: string) => {
    if (!user) return;
    await createComment(drawingId, content, selectedShapeId, parentId);
  };

  const filteredComments = comments.filter((comment) => {
    if (filterType === 'open') return !comment.is_resolved;
    if (filterType === 'resolved') return comment.is_resolved;
    return true;
  });

  if (!isOpen) return null;

  return (
    <div className="fixed right-0 top-0 h-full w-80 bg-white border-l border-gray-300 shadow-lg flex flex-col z-40">
      <div className="flex items-center justify-between p-4 border-b border-gray-300">
        <h2 className="text-lg font-semibold">Comments</h2>
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-xl"
          >
            ×
          </button>
        )}
      </div>

      {error && (
        <div className="mx-4 mt-2 p-2 bg-red-100 text-red-800 text-sm rounded">
          {error}
          <button
            onClick={clearError}
            className="ml-2 underline hover:no-underline"
          >
            Dismiss
          </button>
        </div>
      )}

      {summary && (
        <div className="px-4 py-2 bg-gray-50 border-b border-gray-300 text-sm">
          <div className="flex justify-between mb-1">
            <span>Total: {summary.total_comments}</span>
            <span className="text-green-600">Resolved: {summary.resolved_comments}</span>
          </div>
          <div className="text-gray-600">Open: {summary.unresolved_comments}</div>
        </div>
      )}

      <div className="flex gap-2 p-4 border-b border-gray-300">
        {(['all', 'open', 'resolved'] as const).map((filter) => (
          <button
            key={filter}
            onClick={() => setFilterType(filter)}
            className={`px-3 py-1 rounded text-sm font-medium transition ${
              filterType === filter
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            {filter.charAt(0).toUpperCase() + filter.slice(1)}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {isLoading ? (
          <div className="text-center text-gray-500 py-8">Loading comments...</div>
        ) : filteredComments.length === 0 ? (
          <div className="text-center text-gray-500 py-8">No comments yet</div>
        ) : (
          <div className="space-y-2">
            {filteredComments.map((comment) => (
              <CommentThread
                key={comment.id}
                comment={comment}
                onUpdate={handleUpdateComment}
                onDelete={handleDeleteComment}
                onReply={handleReplyComment}
                onResolve={handleResolveComment}
                isAuthor={comment.author.id === user?.id}
                isLoading={isSubmitting}
              />
            ))}
          </div>
        )}
      </div>

      <div className="border-t border-gray-300 p-4 bg-gray-50">
        <textarea
          value={newCommentContent}
          onChange={(e) => setNewCommentContent(e.target.value)}
          placeholder="Add a comment..."
          className="w-full p-2 border border-gray-300 rounded text-sm resize-none focus:outline-none focus:border-blue-500"
          rows={3}
          disabled={isSubmitting}
        />
        <div className="flex gap-2 mt-2">
          <button
            onClick={handleCreateComment}
            disabled={!newCommentContent.trim() || isSubmitting}
            className="flex-1 px-3 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50 font-medium"
          >
            {isSubmitting ? 'Posting...' : 'Post'}
          </button>
        </div>
      </div>
    </div>
  );
};
