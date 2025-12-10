import React, { useMemo } from 'react';
import { useCommentsStore } from '../../store/commentsStore';

interface CommentMarkerProps {
  shapeId: string;
  drawingId: string;
  onClickMarker?: (shapeId: string) => void;
}

export const CommentMarker: React.FC<CommentMarkerProps> = ({
  shapeId,
  drawingId,
  onClickMarker,
}) => {
  const { commentsByDrawing } = useCommentsStore();

  const shapeComments = useMemo(() => {
    const allComments = commentsByDrawing[drawingId] || [];
    return allComments.filter((comment) => comment.shape_id === shapeId);
  }, [commentsByDrawing, drawingId, shapeId]);

  const unresolvedCount = useMemo(() => {
    return shapeComments.filter((comment) => !comment.is_resolved).length;
  }, [shapeComments]);

  if (shapeComments.length === 0) {
    return null;
  }

  const hasUnresolved = unresolvedCount > 0;

  return (
    <div
      onClick={() => onClickMarker?.(shapeId)}
      className={`
        inline-flex items-center justify-center
        w-6 h-6 rounded-full text-xs font-bold cursor-pointer
        transition-all hover:scale-110
        ${hasUnresolved
          ? 'bg-red-500 text-white shadow-md'
          : 'bg-green-500 text-white shadow-md'
        }
      `}
      title={`${unresolvedCount} unresolved, ${shapeComments.length - unresolvedCount} resolved comments`}
    >
      {shapeComments.length}
    </div>
  );
};

interface CommentBadgeProps {
  commentCount: number;
  unresolvedCount: number;
  onClick?: () => void;
}

export const CommentBadge: React.FC<CommentBadgeProps> = ({
  commentCount,
  unresolvedCount,
  onClick,
}) => {
  if (commentCount === 0) {
    return null;
  }

  const hasUnresolved = unresolvedCount > 0;

  return (
    <button
      onClick={onClick}
      className={`
        inline-flex items-center justify-center gap-1
        px-2 py-1 rounded-full text-xs font-semibold
        cursor-pointer transition-all hover:scale-105
        ${hasUnresolved
          ? 'bg-red-100 text-red-700 hover:bg-red-200'
          : 'bg-green-100 text-green-700 hover:bg-green-200'
        }
      `}
      title={`${commentCount} comments (${unresolvedCount} unresolved)`}
    >
      <span>=¬</span>
      <span>{commentCount}</span>
      {unresolvedCount > 0 && <span className="font-bold">"</span>}
    </button>
  );
};
