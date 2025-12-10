/**
 * CollaboratorAvatars Component
 * Shows active collaborators in an avatar stack with tooltips
 */

import React, { useState } from 'react';
import { useCollaborationStore } from '../../store/collaborationStore';

interface CollaboratorAvatarProps {
  username: string;
  email: string;
  color: string;
  index: number;
}

const CollaboratorAvatar: React.FC<CollaboratorAvatarProps> = ({
  username,
  email,
  color,
  index,
}) => {
  const [showTooltip, setShowTooltip] = useState(false);

  // Get initials from username or email
  const getInitials = (name: string, emailFallback: string): string => {
    if (name && name !== 'Anonymous') {
      const parts = name.split(' ');
      if (parts.length >= 2) {
        return (parts[0][0] + parts[1][0]).toUpperCase();
      }
      return name.slice(0, 2).toUpperCase();
    }
    return emailFallback.slice(0, 2).toUpperCase();
  };

  const initials = getInitials(username, email);

  return (
    <div
      className="relative"
      style={{
        marginLeft: index > 0 ? '-8px' : '0',
        zIndex: 10 - index,
      }}
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      {/* Avatar circle */}
      <div
        className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-white text-xs font-semibold text-white shadow-md transition-transform hover:scale-110"
        style={{
          backgroundColor: color,
        }}
      >
        {initials}
      </div>

      {/* Tooltip */}
      {showTooltip && (
        <div
          className="absolute left-1/2 top-full mt-2 -translate-x-1/2 whitespace-nowrap rounded bg-gray-900 px-3 py-2 text-xs text-white shadow-lg"
          style={{
            zIndex: 100,
          }}
        >
          <div className="font-medium">{username}</div>
          {email && <div className="text-gray-300">{email}</div>}
          {/* Tooltip arrow */}
          <div
            className="absolute bottom-full left-1/2 -translate-x-1/2 border-4 border-transparent border-b-gray-900"
            style={{
              borderBottomColor: '#111827',
            }}
          />
        </div>
      )}
    </div>
  );
};

interface CollaboratorAvatarsProps {
  position?: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';
  maxVisible?: number;
}

export const CollaboratorAvatars: React.FC<CollaboratorAvatarsProps> = ({
  position = 'top-right',
  maxVisible = 5,
}) => {
  const collaborators = useCollaborationStore((state) => state.getCollaboratorsList());
  const connected = useCollaborationStore((state) => state.connected);
  const myColor = useCollaborationStore((state) => state.myColor);
  const sessionId = useCollaborationStore((state) => state.sessionId);

  // Filter out current user from collaborators list
  const otherCollaborators = collaborators.filter(
    (collab) => collab.sessionId !== sessionId
  );

  const visibleCollaborators = otherCollaborators.slice(0, maxVisible);
  const remainingCount = otherCollaborators.length - maxVisible;

  if (!connected || otherCollaborators.length === 0) {
    return null;
  }

  // Position classes
  const positionClasses = {
    'top-left': 'top-4 left-4',
    'top-right': 'top-4 right-4',
    'bottom-left': 'bottom-4 left-4',
    'bottom-right': 'bottom-4 right-4',
  };

  return (
    <div
      className={`fixed z-40 flex items-center gap-2 ${positionClasses[position]}`}
    >
      {/* Connection indicator */}
      <div className="flex items-center gap-2 rounded-full bg-white px-3 py-1.5 shadow-lg">
        <div className="h-2 w-2 animate-pulse rounded-full bg-green-500" />
        <span className="text-sm font-medium text-gray-700">
          {otherCollaborators.length}{' '}
          {otherCollaborators.length === 1 ? 'collaborator' : 'collaborators'}
        </span>
      </div>

      {/* Avatar stack */}
      <div className="flex items-center rounded-full bg-white px-2 py-1.5 shadow-lg">
        {visibleCollaborators.map((collaborator, index) => (
          <CollaboratorAvatar
            key={collaborator.sessionId}
            username={collaborator.username}
            email={collaborator.email}
            color={collaborator.color}
            index={index}
          />
        ))}

        {/* Remaining count indicator */}
        {remainingCount > 0 && (
          <div
            className="ml-1 flex h-8 w-8 items-center justify-center rounded-full border-2 border-white bg-gray-600 text-xs font-semibold text-white shadow-md"
            style={{
              marginLeft: visibleCollaborators.length > 0 ? '-8px' : '0',
            }}
          >
            +{remainingCount}
          </div>
        )}
      </div>

      {/* Your color indicator */}
      {myColor && (
        <div className="flex items-center gap-2 rounded-full bg-white px-3 py-1.5 shadow-lg">
          <div
            className="h-4 w-4 rounded-full border-2 border-gray-200"
            style={{ backgroundColor: myColor }}
          />
          <span className="text-sm font-medium text-gray-700">You</span>
        </div>
      )}
    </div>
  );
};
