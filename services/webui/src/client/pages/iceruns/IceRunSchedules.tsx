/**
 * IceRunSchedules - Cron schedule management
 */

import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { CronBuilder } from './components/CronBuilder';

interface Schedule {
  schedule_id: string;
  cron_expression: string;
  timezone: string;
  is_active: boolean;
  next_run_at: string;
  last_run_at: string | null;
}

export const IceRunSchedules: React.FC = () => {
  const { id: _id } = useParams<{ id: string }>();
  const [schedules, _setSchedules] = useState<Schedule[]>([]);
  const [showCreateForm, setShowCreateForm] = useState(false);

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold text-white">Schedules</h1>
        <button
          onClick={() => setShowCreateForm(true)}
          className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg"
        >
          + Add Schedule
        </button>
      </div>

      {showCreateForm && (
        <div className="bg-ice-navy-800 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold text-white mb-4">Create Schedule</h2>
          <CronBuilder
            value=""
            onChange={(cron) => console.log('Cron:', cron)}
          />
          <div className="flex justify-end space-x-3 mt-4">
            <button
              onClick={() => setShowCreateForm(false)}
              className="px-4 py-2 bg-ice-navy-700 text-white rounded-lg"
            >
              Cancel
            </button>
            <button className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg">
              Create Schedule
            </button>
          </div>
        </div>
      )}

      <div className="bg-ice-navy-800 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-ice-navy-700">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-ice-navy-300 uppercase">
                Cron Expression
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-ice-navy-300 uppercase">
                Timezone
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-ice-navy-300 uppercase">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-ice-navy-300 uppercase">
                Next Run
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-ice-navy-300 uppercase">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ice-navy-700">
            {schedules.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-6 py-8 text-center text-ice-navy-400">
                  No schedules configured.
                </td>
              </tr>
            ) : (
              schedules.map((schedule) => (
                <tr key={schedule.schedule_id} className="hover:bg-ice-navy-700">
                  <td className="px-6 py-4 font-mono text-white">{schedule.cron_expression}</td>
                  <td className="px-6 py-4 text-white">{schedule.timezone}</td>
                  <td className="px-6 py-4">
                    <span
                      className={`px-2 py-1 rounded text-xs font-medium ${
                        schedule.is_active
                          ? 'bg-green-500/20 text-green-400'
                          : 'bg-gray-500/20 text-gray-400'
                      }`}
                    >
                      {schedule.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-ice-navy-300">
                    {new Date(schedule.next_run_at).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 text-right space-x-2">
                    <button className="text-blue-400 hover:text-blue-300">Edit</button>
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

export default IceRunSchedules;
