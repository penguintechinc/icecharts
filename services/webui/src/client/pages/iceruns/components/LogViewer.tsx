/**
 * LogViewer - Syntax-highlighted logs with split pane (stdout | stderr)
 */

import React, { useState, useEffect } from 'react';

interface LogViewerProps {
  executionId: string;
}

export const LogViewer: React.FC<LogViewerProps> = ({ executionId }) => {
  const [stdout, setStdout] = useState('');
  const [stderr, setStderr] = useState('');
  const [activePane, setActivePane] = useState<'stdout' | 'stderr'>('stdout');

  useEffect(() => {
    // TODO: Fetch logs from API
    setStdout('Example stdout logs...\nLine 2\nLine 3');
    setStderr('Example stderr logs...');
  }, [executionId]);

  return (
    <div>
      {/* Tab Selector */}
      <div className="flex border-b border-ice-navy-700 mb-4">
        <button
          onClick={() => setActivePane('stdout')}
          className={`px-4 py-2 ${
            activePane === 'stdout'
              ? 'border-b-2 border-purple-500 text-purple-400'
              : 'text-ice-navy-400 hover:text-white'
          }`}
        >
          stdout
        </button>
        <button
          onClick={() => setActivePane('stderr')}
          className={`px-4 py-2 ${
            activePane === 'stderr'
              ? 'border-b-2 border-purple-500 text-purple-400'
              : 'text-ice-navy-400 hover:text-white'
          }`}
        >
          stderr
        </button>
      </div>

      {/* Log Content */}
      <div className="bg-ice-navy-900 rounded-lg p-4 h-96 overflow-y-auto">
        <pre className="text-sm text-ice-navy-300 font-mono whitespace-pre-wrap">
          {activePane === 'stdout' ? stdout : stderr}
        </pre>
      </div>
    </div>
  );
};
