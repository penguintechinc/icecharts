/**
 * IceRunsList - Main list view for IceRuns functions
 *
 * Features:
 * - Paginated table with filters (runtime, status, tags)
 * - Search by name/description
 * - Quick actions: Execute, Edit, Delete
 * - Create button (top-right)
 */

import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';

interface IceRunFunction {
  function_id: string;
  name: string;
  description: string;
  runtime: string;
  status: string;
  execution_count: number;
  last_executed_at: string | null;
  created_at: string;
  tags: string[];
}

export const IceRunsList: React.FC = () => {
  const navigate = useNavigate();
  void navigate; // Will be used for navigation
  const [functions, setFunctions] = useState<IceRunFunction[]>([]);
  void setFunctions; // Will be used when API is connected
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [runtimeFilter, setRuntimeFilter] = useState('all');

  useEffect(() => {
    // TODO: Fetch functions from API
    setLoading(false);
  }, []);

  const filteredFunctions = functions.filter((fn) => {
    const matchesSearch = fn.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         fn.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || fn.status === statusFilter;
    const matchesRuntime = runtimeFilter === 'all' || fn.runtime === runtimeFilter;
    return matchesSearch && matchesStatus && matchesRuntime;
  });

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-white">IceRuns Functions</h1>
          <p className="text-ice-navy-300 mt-1">Serverless function execution platform</p>
        </div>
        <Link
          to="/iceruns/create"
          className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
        >
          + Create Function
        </Link>
      </div>

      {/* Filters */}
      <div className="bg-ice-navy-800 rounded-lg p-4 mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
        <input
          type="text"
          placeholder="Search functions..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="px-4 py-2 bg-ice-navy-700 text-white rounded-lg border border-ice-navy-600 focus:outline-none focus:border-purple-500"
        />
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2 bg-ice-navy-700 text-white rounded-lg border border-ice-navy-600 focus:outline-none focus:border-purple-500"
        >
          <option value="all">All Statuses</option>
          <option value="draft">Draft</option>
          <option value="active">Active</option>
          <option value="paused">Paused</option>
          <option value="archived">Archived</option>
        </select>
        <select
          value={runtimeFilter}
          onChange={(e) => setRuntimeFilter(e.target.value)}
          className="px-4 py-2 bg-ice-navy-700 text-white rounded-lg border border-ice-navy-600 focus:outline-none focus:border-purple-500"
        >
          <option value="all">All Runtimes</option>
          <option value="python3.13">Python 3.13</option>
          <option value="nodejs">Node.js</option>
          <option value="go">Go</option>
          <option value="ruby">Ruby</option>
          <option value="bash">Bash</option>
          <option value="powershell">PowerShell</option>
          <option value="rust">Rust</option>
        </select>
      </div>

      {/* Functions Table */}
      <div className="bg-ice-navy-800 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-ice-navy-700">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-ice-navy-300 uppercase tracking-wider">
                Function
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-ice-navy-300 uppercase tracking-wider">
                Runtime
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-ice-navy-300 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-ice-navy-300 uppercase tracking-wider">
                Executions
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-ice-navy-300 uppercase tracking-wider">
                Last Executed
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-ice-navy-300 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ice-navy-700">
            {filteredFunctions.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-8 text-center text-ice-navy-400">
                  {loading ? 'Loading...' : 'No functions found. Create your first function to get started.'}
                </td>
              </tr>
            ) : (
              filteredFunctions.map((fn) => (
                <tr key={fn.function_id} className="hover:bg-ice-navy-700 transition-colors">
                  <td className="px-6 py-4">
                    <Link to={`/iceruns/${fn.function_id}`} className="text-purple-400 hover:text-purple-300 font-medium">
                      {fn.name}
                    </Link>
                    <p className="text-sm text-ice-navy-400">{fn.description}</p>
                  </td>
                  <td className="px-6 py-4 text-white">{fn.runtime}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      fn.status === 'active' ? 'bg-green-500/20 text-green-400' :
                      fn.status === 'paused' ? 'bg-yellow-500/20 text-yellow-400' :
                      fn.status === 'archived' ? 'bg-gray-500/20 text-gray-400' :
                      'bg-blue-500/20 text-blue-400'
                    }`}>
                      {fn.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-white">{fn.execution_count}</td>
                  <td className="px-6 py-4 text-ice-navy-300">
                    {fn.last_executed_at ? new Date(fn.last_executed_at).toLocaleString() : 'Never'}
                  </td>
                  <td className="px-6 py-4 text-right space-x-2">
                    <button className="text-purple-400 hover:text-purple-300">Execute</button>
                    <Link to={`/iceruns/${fn.function_id}/edit`} className="text-blue-400 hover:text-blue-300">
                      Edit
                    </Link>
                    <button className="text-red-400 hover:text-red-300">Delete</button>
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

export default IceRunsList;
