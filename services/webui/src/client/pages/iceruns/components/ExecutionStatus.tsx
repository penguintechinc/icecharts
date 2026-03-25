/**
 * ExecutionStatus - Real-time status indicator with WebSocket
 */

import React, { useEffect, useState } from 'react';

interface ExecutionStatusProps {
  executionId: string;
}

export const ExecutionStatus: React.FC<ExecutionStatusProps> = ({ executionId }) => {
  const [status, _setStatus] = useState('queued');
  const [progress, _setProgress] = useState(0);

  useEffect(() => {
    // TODO: WebSocket connection for real-time updates
    // const ws = new WebSocket(`wss://api.example.com/ws/iceruns/executions/${executionId}`);
    // ws.onmessage = (event) => {
    //   const data = JSON.parse(event.data);
    //   _setStatus(data.status);
    //   _setProgress(data.progress_percent);
    // };
    // return () => ws.close();
  }, [executionId]);

  const getStatusColor = () => {
    switch (status) {
      case 'completed':
        return 'bg-green-500';
      case 'failed':
        return 'bg-red-500';
      case 'running':
        return 'bg-yellow-500';
      default:
        return 'bg-blue-500';
    }
  };

  return (
    <div className="flex items-center space-x-4">
      <div className={`w-4 h-4 rounded-full ${getStatusColor()}`} />
      <div className="flex-1">
        <p className="text-white font-medium capitalize">{status}</p>
        {status === 'running' && (
          <div className="mt-2 bg-ice-navy-700 rounded-full h-2">
            <div
              className="bg-purple-500 h-2 rounded-full transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        )}
      </div>
      <p className="text-ice-navy-400">{progress}%</p>
    </div>
  );
};
