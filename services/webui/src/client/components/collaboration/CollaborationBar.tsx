import React from 'react';
import { Collaborator } from '../../types';
import './CollaborationBar.css';

interface CollaborationBarProps {
  collaborators: Collaborator[];
  isConnected: boolean;
}

const getColorForCollaborator = (username: string): string => {
  // Generate a consistent color based on username
  const colors = [
    '#FF6B6B', // Red
    '#4ECDC4', // Teal
    '#45B7D1', // Blue
    '#FFA07A', // Light Salmon
    '#98D8C8', // Mint
    '#F7DC6F', // Yellow
    '#BB8FCE', // Purple
    '#85C1E2', // Light Blue
    '#F8B88B', // Peach
    '#ABEBC6', // Green
  ];

  let hash = 0;
  for (let i = 0; i < username.length; i++) {
    hash = username.charCodeAt(i) + ((hash << 5) - hash);
  }

  return colors[Math.abs(hash) % colors.length];
};

export const CollaborationBar: React.FC<CollaborationBarProps> = ({
  collaborators,
  isConnected,
}) => {
  return (
    <div className="collaboration-bar sticky top-0 z-40 border-b border-slate-700 bg-slate-900 px-4 py-3 shadow-md">
      <div className="flex items-center justify-between gap-4">
        {/* Connection status indicator */}
        <div className={`status flex items-center gap-2 ${isConnected ? 'connected' : 'disconnected'}`}>
          <div
            className={`status-dot h-3 w-3 rounded-full ${
              isConnected ? 'bg-green-500 animate-pulse' : 'bg-orange-500'
            }`}
          />
          <span className="text-sm font-medium text-slate-200">
            {isConnected ? 'Live' : 'Reconnecting...'}
          </span>
        </div>

        {/* Collaborator avatars */}
        <div className="collaborators flex items-center gap-2">
          {collaborators.length > 0 && (
            <>
              <span className="text-xs text-slate-400">Collaborators:</span>
              <div className="flex -space-x-2">
                {collaborators.map((collaborator) => {
                  const avatarColor = collaborator.cursor_position?.color || getColorForCollaborator(collaborator.username);
                  return (
                    <div
                      key={collaborator.user_id}
                      className="collaborator-avatar relative flex h-8 w-8 items-center justify-center rounded-full border-2 border-slate-800 text-xs font-bold text-white transition-transform hover:z-10 hover:scale-110"
                      style={{ backgroundColor: avatarColor }}
                      title={`${collaborator.username} (${collaborator.permission})`}
                    >
                      {collaborator.username.charAt(0).toUpperCase()}
                      {collaborator.is_online && (
                        <div className="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border border-slate-900 bg-green-400" />
                      )}
                    </div>
                  );
                })}
              </div>
            </>
          )}
        </div>

        {/* Instructions */}
        <div className="instructions">
          {collaborators.length > 0 && (
            <span className="text-xs text-slate-400">
              Ctrl+Click to grab attention
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
