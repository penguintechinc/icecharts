/**
 * IceRunExecutions - Execution history for a function
 */

import React, { useState, useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';

interface Execution {
  execution_id: string;
  status: string;
  trigger_type: string;
  started_at: string;
  duration_ms: number;
  exit_code: number;
}

export const IceRunExecutions: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [executions, _setExecutions] = useState<Execution[]>([]);
  const [_loading, setLoading] = useState(true);

  useEffect(() => {
    // TODO: Fetch executions from API
    setLoading(false);
  }, [id]);

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold text-white mb-6">Execution History</h1>

      <div className="bg-ice-navy-800 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-ice-navy-700">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-ice-navy-300 uppercase">
                Execution ID
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-ice-navy-300 uppercase">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-ice-navy-300 uppercase">
                Trigger
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-ice-navy-300 uppercase">
                Started
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-ice-navy-300 uppercase">
                Duration
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-ice-navy-300 uppercase">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ice-navy-700">
            {executions.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-8 text-center text-ice-navy-400">
                  No executions found.
                </td>
              </tr>
            ) : (
              executions.map((exec) => (
                <tr key={exec.execution_id} className="hover:bg-ice-navy-700">
                  <td className="px-6 py-4 font-mono text-sm text-white">
                    {exec.execution_id.substring(0, 8)}...
                  </td>
                  <td className="px-6 py-4">
                    <span
                      className={`px-2 py-1 rounded text-xs font-medium ${
                        exec.status === 'completed'
                          ? 'bg-green-500/20 text-green-400'
                          : exec.status === 'failed'
                          ? 'bg-red-500/20 text-red-400'
                          : 'bg-yellow-500/20 text-yellow-400'
                      }`}
                    >
                      {exec.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-white">{exec.trigger_type}</td>
                  <td className="px-6 py-4 text-ice-navy-300">
                    {new Date(exec.started_at).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 text-white">{exec.duration_ms}ms</td>
                  <td className="px-6 py-4 text-right">
                    <Link
                      to={`/iceruns/executions/${exec.execution_id}`}
                      className="text-purple-400 hover:text-purple-300"
                    >
                      Details
                    </Link>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default IceRunExecutions;
