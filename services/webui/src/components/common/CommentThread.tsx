import React, { useState } from 'react';
import type { Comment } from '../../types';

interface CommentThreadProps {
  comment: Comment;
  onUpdate: (commentId: string, content: string) => Promise<void>;
  onDelete: (commentId: string) => Promise<void>;
  onReply: (parentId: string, content: string) => Promise<void>;
  onResolve: (commentId: string) => Promise<void>;
  isAuthor: boolean;
  isLoading?: boolean;
}

export const CommentThread: React.FC<CommentThreadProps> = ({
  comment,
  onUpdate,
  onDelete,
  onReply,
  onResolve,
  isAuthor,
  isLoading = false,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(comment.content);
  const [isReplying, setIsReplying] = useState(false);
  const [replyContent, setReplyContent] = useState('');
  const [showReplies, setShowReplies] = useState(false);

  const handleUpdate = async () => {
    if (editContent.trim() && editContent !== comment.content) {
      await onUpdate(comment.id, editContent);
      setIsEditing(false);
    }
  };

  const handleReply = async () => {
    if (replyContent.trim()) {
      await onReply(comment.id, replyContent);
      setReplyContent('');
      setIsReplying(false);
      setShowReplies(true);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="border-l-2 border-gray-300 pl-4 py-2 mb-4">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2 flex-1">
          {comment.author.profile_picture_url && (
            <img
              src={comment.author.profile_picture_url}
              alt={comment.author.full_name}
              className="w-8 h-8 rounded-full"
            />
          )}
          <div className="flex-1 min-w-0">
            <div className="font-semibold text-sm">
              {comment.author.full_name || comment.author.email}
            </div>
            <div className="text-xs text-gray-500">
              {formatDate(comment.created_at)}
              {comment.updated_at !== comment.created_at && ' (edited)'}
            </div>
          </div>
        </div>

        {comment.is_resolved && (
          <span className="bg-green-100 text-green-800 text-xs font-medium px-2 py-1 rounded">
            Resolved
          </span>
        )}
      </div>

      {isEditing ? (
        <div className="mt-2">
          <textarea
            value={editContent}
            onChange={(e) => setEditContent(e.target.value)}
            className="w-full p-2 border border-gray-300 rounded text-sm"
            rows={3}
            disabled={isLoading}
          />
          <div className="flex gap-2 mt-2">
            <button
              onClick={handleUpdate}
              disabled={isLoading}
              className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50"
            >
              Save
            </button>
            <button
              onClick={() => {
                setEditContent(comment.content);
                setIsEditing(false);
              }}
              disabled={isLoading}
              className="px-3 py-1 bg-gray-300 text-gray-700 text-sm rounded hover:bg-gray-400 disabled:opacity-50"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <div className="mt-2 text-sm text-gray-700">{comment.content}</div>
      )}

      <div className="flex gap-3 mt-2 text-xs">
        {isAuthor && !isEditing && (
          <>
            <button
              onClick={() => setIsEditing(true)}
              disabled={isLoading}
              className="text-blue-600 hover:text-blue-800 disabled:opacity-50"
            >
              Edit
            </button>
            <button
              onClick={() => onDelete(comment.id)}
              disabled={isLoading}
              className="text-red-600 hover:text-red-800 disabled:opacity-50"
            >
              Delete
            </button>
          </>
        )}

        {!comment.is_resolved && (
          <button
            onClick={() => onResolve(comment.id)}
            disabled={isLoading}
            className="text-green-600 hover:text-green-800 disabled:opacity-50"
          >
            Resolve
          </button>
        )}

        {!isReplying && (
          <button
            onClick={() => setIsReplying(true)}
            disabled={isLoading}
            className="text-blue-600 hover:text-blue-800 disabled:opacity-50"
          >
            Reply
          </button>
        )}
      </div>

      {isReplying && (
        <div className="mt-3 bg-gray-50 p-2 rounded">
          <textarea
            value={replyContent}
            onChange={(e) => setReplyContent(e.target.value)}
            placeholder="Add a reply..."
            className="w-full p-2 border border-gray-300 rounded text-sm"
            rows={2}
            disabled={isLoading}
          />
          <div className="flex gap-2 mt-2">
            <button
              onClick={handleReply}
              disabled={isLoading || !replyContent.trim()}
              className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 disabled:opacity-50"
            >
              Reply
            </button>
            <button
              onClick={() => {
                setReplyContent('');
                setIsReplying(false);
              }}
              disabled={isLoading}
              className="px-3 py-1 bg-gray-300 text-gray-700 text-sm rounded hover:bg-gray-400 disabled:opacity-50"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {comment.replies && comment.replies.length > 0 && (
        <div className="mt-3">
          <button
            onClick={() => setShowReplies(!showReplies)}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            {showReplies ? 'Hide' : 'Show'} {comment.replies.length} repl{comment.replies.length === 1 ? 'y' : 'ies'}
          </button>

          {showReplies && (
            <div className="mt-2 space-y-2">
              {comment.replies.map((reply) => (
                <CommentThread
                  key={reply.id}
                  comment={reply}
                  onUpdate={onUpdate}
                  onDelete={onDelete}
                  onReply={onReply}
                  onResolve={onResolve}
                  isAuthor={false}
                  isLoading={isLoading}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
