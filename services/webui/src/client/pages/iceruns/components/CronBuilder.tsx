/**
 * CronBuilder - Visual cron expression builder
 */

import React, { useState } from 'react';

interface CronBuilderProps {
  value: string;
  onChange: (cron: string) => void;
}

export const CronBuilder: React.FC<CronBuilderProps> = ({ value: _value, onChange }) => {
  const [minute, setMinute] = useState('*');
  const [hour, setHour] = useState('*');
  const [day, setDay] = useState('*');
  const [month, setMonth] = useState('*');
  const [weekday, setWeekday] = useState('*');

  const buildCron = () => {
    return `${minute} ${hour} ${day} ${month} ${weekday}`;
  };

  const handleChange = () => {
    onChange(buildCron());
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-5 gap-4">
        <div>
          <label className="block text-sm font-medium text-ice-navy-300 mb-2">
            Minute
          </label>
          <input
            type="text"
            value={minute}
            onChange={(e) => {
              setMinute(e.target.value);
              handleChange();
            }}
            placeholder="*"
            className="w-full px-4 py-2 bg-ice-navy-700 text-white rounded-lg border border-ice-navy-600 focus:outline-none focus:border-purple-500 font-mono"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-ice-navy-300 mb-2">
            Hour
          </label>
          <input
            type="text"
            value={hour}
            onChange={(e) => {
              setHour(e.target.value);
              handleChange();
            }}
            placeholder="*"
            className="w-full px-4 py-2 bg-ice-navy-700 text-white rounded-lg border border-ice-navy-600 focus:outline-none focus:border-purple-500 font-mono"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-ice-navy-300 mb-2">
            Day
          </label>
          <input
            type="text"
            value={day}
            onChange={(e) => {
              setDay(e.target.value);
              handleChange();
            }}
            placeholder="*"
            className="w-full px-4 py-2 bg-ice-navy-700 text-white rounded-lg border border-ice-navy-600 focus:outline-none focus:border-purple-500 font-mono"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-ice-navy-300 mb-2">
            Month
          </label>
          <input
            type="text"
            value={month}
            onChange={(e) => {
              setMonth(e.target.value);
              handleChange();
            }}
            placeholder="*"
            className="w-full px-4 py-2 bg-ice-navy-700 text-white rounded-lg border border-ice-navy-600 focus:outline-none focus:border-purple-500 font-mono"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-ice-navy-300 mb-2">
            Weekday
          </label>
          <input
            type="text"
            value={weekday}
            onChange={(e) => {
              setWeekday(e.target.value);
              handleChange();
            }}
            placeholder="*"
            className="w-full px-4 py-2 bg-ice-navy-700 text-white rounded-lg border border-ice-navy-600 focus:outline-none focus:border-purple-500 font-mono"
          />
        </div>
      </div>

      <div className="bg-ice-navy-900 p-4 rounded-lg">
        <p className="text-sm text-ice-navy-400 mb-2">Cron Expression:</p>
        <p className="text-white font-mono">{buildCron()}</p>
      </div>

      <div className="text-sm text-ice-navy-400">
        <p>Examples:</p>
        <ul className="list-disc list-inside mt-2 space-y-1">
          <li><code className="font-mono">0 * * * *</code> - Every hour</li>
          <li><code className="font-mono">0 0 * * *</code> - Daily at midnight</li>
          <li><code className="font-mono">0 0 * * 0</code> - Weekly on Sunday</li>
          <li><code className="font-mono">0 0 1 * *</code> - Monthly on the 1st</li>
        </ul>
      </div>
    </div>
  );
};
