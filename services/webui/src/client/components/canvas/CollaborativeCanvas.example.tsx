/**
 * CollaborativeCanvas - Example Usage Component
 * Demonstrates how to integrate the collaboration system into a canvas
 */

import React, { useEffect, useCallback } from 'react';
import { useCollaboration } from '../../hooks/useCollaboration';
import { CollaboratorCursors } from './CollaboratorCursors';
import { CollaboratorAvatars } from './CollaboratorAvatars';
import { useCollaborationStore } from '../../store/collaborationStore';

interface CollaborativeCanvasProps {
  drawingId: string;
}

export const CollaborativeCanvas: React.FC<CollaborativeCanvasProps> = ({
  drawingId,
}) => {
  const {
    sendCursorPosition,
    lockShape,
    unlockShape,
    sendShapeUpdate,
    requestPresence,
  } = useCollaboration({
    roomId: drawingId,
    enabled: true,
    onConnected: () => {
      console.log('Connected to collaboration server');
    },
    onDisconnected: () => {
      console.log('Disconnected from collaboration server');
    },
    onError: (error) => {
      console.error('Collaboration error:', error);
    },
  });

  const connected = useCollaborationStore((state) => state.connected);
  const isShapeLocked = useCollaborationStore((state) => state.isShapeLocked);

  // Handle mouse move to send cursor position
  const handleMouseMove = useCallback(
    (event: React.MouseEvent<HTMLDivElement>) => {
      if (!connected) return;

      const rect = event.currentTarget.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;

      sendCursorPosition(x, y);
    },
    [connected, sendCursorPosition]
  );

  // Handle shape selection and locking
  const handleShapeSelect = useCallback(
    async (shapeId: string) => {
      if (!connected) return;

      // Check if shape is already locked
      if (isShapeLocked(shapeId)) {
        alert('This shape is locked by another user');
        return;
      }

      try {
        // Request lock
        await lockShape(shapeId);
        console.log(`Locked shape: ${shapeId}`);

        // Now you can edit the shape
        // When done editing, call unlockShape(shapeId)
      } catch (error) {
        console.error('Failed to lock shape:', error);
        alert('Could not lock shape for editing');
      }
    },
    [connected, isShapeLocked, lockShape]
  );

  // Handle shape updates
  const handleShapeUpdate = useCallback(
    (shapeId: string, newData: any) => {
      if (!connected) return;

      // Send update to other collaborators
      sendShapeUpdate(shapeId, newData);
    },
    [connected, sendShapeUpdate]
  );

  // Listen for shape updates from other users
  useEffect(() => {
    const handleRemoteUpdate = (event: CustomEvent) => {
      const { shape_id, shape_data, user_id } = event.detail;
      console.log(`Shape ${shape_id} updated by user ${user_id}`, shape_data);

      // Apply the update to your canvas
      // updateLocalShape(shape_id, shape_data);
    };

    window.addEventListener(
      'collaboration:shape_updated',
      handleRemoteUpdate as EventListener
    );

    return () => {
      window.removeEventListener(
        'collaboration:shape_updated',
        handleRemoteUpdate as EventListener
      );
    };
  }, []);

  // Request initial presence when component mounts
  useEffect(() => {
    if (connected) {
      requestPresence();
    }
  }, [connected, requestPresence]);

  return (
    <div className="relative h-full w-full">
      {/* Connection status banner */}
      {!connected && (
        <div className="absolute left-1/2 top-4 z-50 -translate-x-1/2 transform rounded-lg bg-yellow-100 px-4 py-2 text-sm font-medium text-yellow-800 shadow-lg">
          Connecting to collaboration server...
        </div>
      )}

      {/* Canvas area */}
      <div
        className="h-full w-full bg-gray-50"
        onMouseMove={handleMouseMove}
        onClick={() => {
          // Example: clicking on a shape
          const exampleShapeId = 'shape-123';
          handleShapeSelect(exampleShapeId);
        }}
      >
        {/* Your canvas content goes here */}
        <div className="flex h-full items-center justify-center text-gray-500">
          <div className="text-center">
            <h2 className="mb-2 text-2xl font-bold">Collaborative Canvas</h2>
            <p className="mb-4">Drawing ID: {drawingId}</p>
            <p className="text-sm">
              {connected ? (
                <span className="text-green-600">Connected - Move your mouse to see cursor tracking</span>
              ) : (
                <span className="text-yellow-600">Connecting...</span>
              )}
            </p>
          </div>
        </div>
      </div>

      {/* Render other users' cursors */}
      <CollaboratorCursors />

      {/* Show active collaborators */}
      <CollaboratorAvatars position="top-right" maxVisible={5} />
    </div>
  );
};

/**
 * Usage Example:
 *
 * import { CollaborativeCanvas } from './components/canvas/CollaborativeCanvas';
 *
 * function MyDrawingApp() {
 *   const drawingId = 'drawing-123'; // Get from route params or props
 *
 *   return <CollaborativeCanvas drawingId={drawingId} />;
 * }
 */
