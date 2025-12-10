/**
 * CollaboratorCursors Component
 * Renders real-time cursors for other collaborators with smooth interpolation
 */

import React, { useEffect, useState, useRef } from 'react';
import { useCollaborationStore } from '../../store/collaborationStore';

interface CursorPosition {
  x: number;
  y: number;
  targetX: number;
  targetY: number;
  color: string;
  username: string;
  sessionId: string;
}

export const CollaboratorCursors: React.FC = () => {
  const cursors = useCollaborationStore((state) => state.cursors);
  const [cursorPositions, setCursorPositions] = useState<Map<string, CursorPosition>>(
    new Map()
  );
  const animationFrameRef = useRef<number>();

  // Update target positions when cursors change
  useEffect(() => {
    const newPositions = new Map(cursorPositions);

    // Add/update cursors
    cursors.forEach((cursor, sessionId) => {
      const existing = newPositions.get(sessionId);
      if (existing) {
        // Update target position
        newPositions.set(sessionId, {
          ...existing,
          targetX: cursor.x,
          targetY: cursor.y,
          color: cursor.color,
          username: cursor.username,
        });
      } else {
        // New cursor
        newPositions.set(sessionId, {
          x: cursor.x,
          y: cursor.y,
          targetX: cursor.x,
          targetY: cursor.y,
          color: cursor.color,
          username: cursor.username,
          sessionId,
        });
      }
    });

    // Remove cursors that are no longer present
    Array.from(newPositions.keys()).forEach((sessionId) => {
      if (!cursors.has(sessionId)) {
        newPositions.delete(sessionId);
      }
    });

    setCursorPositions(newPositions);
  }, [cursors]);

  // Smooth interpolation animation
  useEffect(() => {
    const animate = () => {
      setCursorPositions((prevPositions) => {
        const newPositions = new Map(prevPositions);
        let hasChanges = false;

        newPositions.forEach((pos, sessionId) => {
          const dx = pos.targetX - pos.x;
          const dy = pos.targetY - pos.y;
          const distance = Math.sqrt(dx * dx + dy * dy);

          if (distance > 0.5) {
            // Interpolate position (ease-out)
            const speed = 0.2;
            const newX = pos.x + dx * speed;
            const newY = pos.y + dy * speed;

            newPositions.set(sessionId, {
              ...pos,
              x: newX,
              y: newY,
            });
            hasChanges = true;
          } else if (distance > 0) {
            // Snap to target when very close
            newPositions.set(sessionId, {
              ...pos,
              x: pos.targetX,
              y: pos.targetY,
            });
            hasChanges = true;
          }
        });

        return hasChanges ? newPositions : prevPositions;
      });

      animationFrameRef.current = requestAnimationFrame(animate);
    };

    animationFrameRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, []);

  return (
    <div
      className="pointer-events-none fixed inset-0 z-50"
      style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }}
    >
      {Array.from(cursorPositions.values()).map((cursor) => (
        <div
          key={cursor.sessionId}
          className="absolute transition-opacity duration-200"
          style={{
            left: cursor.x,
            top: cursor.y,
            transform: 'translate(-2px, -2px)',
          }}
        >
          {/* Cursor SVG */}
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            style={{
              filter: 'drop-shadow(0 1px 2px rgba(0, 0, 0, 0.3))',
            }}
          >
            <path
              d="M5.5 3L19 16.5L13 15L9.5 21L7.5 20L11 14L5.5 3Z"
              fill={cursor.color}
              stroke="white"
              strokeWidth="1.5"
              strokeLinejoin="round"
            />
          </svg>

          {/* Username label */}
          <div
            className="absolute left-6 top-0 whitespace-nowrap rounded px-2 py-1 text-xs font-medium text-white shadow-lg"
            style={{
              backgroundColor: cursor.color,
              maxWidth: '150px',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            {cursor.username}
          </div>
        </div>
      ))}
    </div>
  );
};
