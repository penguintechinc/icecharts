/**
 * IceRunTest - Test function UI
 *
 * Features:
 * - JSON editor for input payload
 * - "Run Test" button
 * - Real-time execution progress
 * - Results display (output, logs, exit code)
 */

import React, { useState } from 'react';
import { useParams } from 'react-router-dom';

export const IceRunTest: React.FC = () => {
  const { id: _id } = useParams<{ id: string }>();
  const [input, setInput] = useState('{\n  "example": "data"\n}');
  const [output, setOutput] = useState<any>(null);
  const [running, setRunning] = useState(false);

  const handleTest = async () => {
    setRunning(true);
    // TODO: Call test API
    setTimeout(() => {
      setOutput({
        status: 'completed',
        result: { message: 'Test successful' },
        duration_ms: 234,
        exit_code: 0,
      });
      setRunning(false);
    }, 2000);
  };

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold text-white mb-6">Test Function</h1>

      <div className="grid grid-cols-2 gap-6">
        {/* Input Editor */}
        <div className="bg-ice-navy-800 rounded-lg p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Input JSON</h2>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className="w-full h-64 px-4 py-2 bg-ice-navy-900 text-white font-mono text-sm rounded-lg border border-ice-navy-600 focus:outline-none focus:border-purple-500"
          />
          <button
            onClick={handleTest}
            disabled={running}
            className="mt-4 w-full px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg disabled:opacity-50"
          >
            {running ? 'Running...' : 'Run Test'}
          </button>
        </div>

        {/* Output Display */}
        <div className="bg-ice-navy-800 rounded-lg p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Output</h2>
          {output ? (
            <div className="space-y-4">
              <div>
                <p className="text-ice-navy-400 text-sm">Status</p>
                <p className="text-white">{output.status}</p>
              </div>
              <div>
                <p className="text-ice-navy-400 text-sm">Duration</p>
                <p className="text-white">{output.duration_ms}ms</p>
              </div>
              <div>
                <p className="text-ice-navy-400 text-sm">Exit Code</p>
                <p className="text-white">{output.exit_code}</p>
              </div>
              <div>
                <p className="text-ice-navy-400 text-sm">Result</p>
                <pre className="bg-ice-navy-900 p-4 rounded text-sm text-ice-navy-300 overflow-x-auto">
                  {JSON.stringify(output.result, null, 2)}
                </pre>
              </div>
            </div>
          ) : (
            <p className="text-ice-navy-400">Run a test to see output...</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default IceRunTest;
