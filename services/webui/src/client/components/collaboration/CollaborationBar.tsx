import React from 'react';

interface Collaborator {
  user_id: number;
  username: string;
  permission: 'viewer' | 'editor' | 'admin';
  cursor?: { x: number; y: number };
  color: string;
}

interface CollaborationBarProps {
  collaborators: Collaborator[];
  isConnected: boolean;
}

export const CollaborationBar: React.FC<CollaborationBarProps> = ({
  collaborators,
  isConnected,
}) => {
  return (
    <div className="collaboration-bar border-b border-dark-700 bg-dark-900 px-4 py-2 flex items-center justify-between">
      <div className="flex items-center gap-4">
        {/* Connection status indicator */}
        <div className={`status flex items-center gap-2 ${isConnected ? 'connected' : 'disconnected'}`}>
          <div
            className={`status-dot h-2.5 w-2.5 rounded-full ${
              isConnected ? 'bg-green-500' : 'bg-orange-500 animate-pulse'
            }`}
          />
          <span className="text-xs font-medium text-gold-400">
            {isConnected ? 'Live' : 'Reconnecting...'}
          </span>
        </div>

        {/* Collaborator avatars */}
        {collaborators.length > 0 && (
          <div className="collaborators flex items-center gap-2">
            <span className="text-xs text-dark-400">Collaborators:</span>
            <div className="flex -space-x-2">
              {collaborators.map((collaborator) => (
                <div
                  key={collaborator.user_id}
                  className="collaborator-avatar relative flex h-7 w-7 items-center justify-center rounded-full border-2 border-dark-800 text-xs font-bold text-white transition-transform hover:z-10 hover:scale-110"
                  style={{ backgroundColor: collaborator.color }}
                  title={`${collaborator.username} (${collaborator.permission})`}
                >
                  {collaborator.username.charAt(0).toUpperCase()}
                  <div className="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full border border-dark-900 bg-green-400" />
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Instructions */}
      {collaborators.length > 0 && (
        <div className="instructions">
          <span className="text-xs text-dark-500">
            Ctrl+Click to grab attention
          </span>
        </div>
      )}
    </div>
  );
};
