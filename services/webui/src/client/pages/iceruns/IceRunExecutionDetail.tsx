/**
 * IceRunExecutionDetail - Single execution view with logs
 *
 * Features:
 * - Status badge with real-time updates (WebSocket)
 * - Execution metadata (triggered by, timestamp, duration)
 * - Input/Output JSON (collapsible, syntax-highlighted)
 * - Logs viewer (split pane: stdout | stderr)
 * - Download buttons (logs, artifacts)
 * - Retry button (if failed)
 */

import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { ExecutionStatus } from './components/ExecutionStatus';
import { LogViewer } from './components/LogViewer';

export const IceRunExecutionDetail: React.FC = () => {
  const { executionId } = useParams<{ executionId: string }>();
  const [_execution, _setExecution] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // TODO: Fetch execution details from API
    setLoading(false);
  }, [executionId]);

  if (loading) {
    return <div className="p-6 text-white">Loading...</div>;
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-3xl font-bold text-white">Execution Details</h1>
          <p className="text-ice-navy-300 mt-1 font-mono text-sm">{executionId}</p>
        </div>
        <div className="flex space-x-3">
          <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg">
            Download Logs
          </button>
          <button className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg">
            Retry
          </button>
        </div>
      </div>

      {/* Status Card */}
      <div className="bg-ice-navy-800 rounded-lg p-6 mb-6">
        <ExecutionStatus executionId={executionId!} />
      </div>

      {/* Metadata */}
      <div className="bg-ice-navy-800 rounded-lg p-6 mb-6">
        <h2 className="text-xl font-semibold text-white mb-4">Execution Metadata</h2>
        <div className="grid grid-cols-3 gap-6">
          <div>
            <p className="text-ice-navy-400 text-sm">Triggered By</p>
            <p className="text-white">webhook</p>
          </div>
          <div>
            <p className="text-ice-navy-400 text-sm">Started At</p>
            <p className="text-white">{new Date().toLocaleString()}</p>
          </div>
          <div>
            <p className="text-ice-navy-400 text-sm">Duration</p>
            <p className="text-white">2.34s</p>
          </div>
        </div>
      </div>

      {/* Input/Output */}
      <div className="grid grid-cols-2 gap-6 mb-6">
        <div className="bg-ice-navy-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Input</h3>
          <pre className="bg-ice-navy-900 p-4 rounded text-sm text-ice-navy-300 overflow-x-auto">
            {JSON.stringify({ example: 'input' }, null, 2)}
          </pre>
        </div>
        <div className="bg-ice-navy-800 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Output</h3>
          <pre className="bg-ice-navy-900 p-4 rounded text-sm text-ice-navy-300 overflow-x-auto">
            {JSON.stringify({ example: 'output' }, null, 2)}
          </pre>
        </div>
      </div>

      {/* Logs */}
      <div className="bg-ice-navy-800 rounded-lg p-6">
        <h2 className="text-xl font-semibold text-white mb-4">Execution Logs</h2>
        <LogViewer executionId={executionId!} />
      </div>
    </div>
  );
};

export default IceRunExecutionDetail;
