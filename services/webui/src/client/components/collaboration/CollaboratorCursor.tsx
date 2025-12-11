import React from 'react';

interface CollaboratorCursorProps {
  username: string;
  x: number;
  y: number;
  color: string;
}

export const CollaboratorCursor: React.FC<CollaboratorCursorProps> = ({
  username,
  x,
  y,
  color,
}) => {
  return (
    <div
      className="collaborator-cursor"
      style={{
        position: 'absolute',
        left: x,
        top: y,
        pointerEvents: 'none',
        zIndex: 9999,
        transform: 'translate(-2px, -2px)',
      }}
    >
      {/* Cursor SVG icon */}
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
          d="M5 3L19 12L12 13L9 20L5 3Z"
          fill={color}
          stroke="white"
          strokeWidth="1.5"
          strokeLinejoin="round"
        />
      </svg>

      {/* Username label */}
      <div
        className="cursor-label absolute left-6 top-0 whitespace-nowrap rounded px-2 py-1 text-xs font-medium text-white shadow-lg"
        style={{
          backgroundColor: color,
          maxWidth: '150px',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
        }}
      >
        {username}
      </div>
    </div>
  );
};
