/**
 * RuntimeSelector - Runtime dropdown with icons
 */

import React from 'react';

interface RuntimeSelectorProps {
  value: string;
  onChange: (runtime: string) => void;
}

const runtimes = [
  { id: 'python3.13', label: 'Python 3.13', icon: '🐍' },
  { id: 'nodejs', label: 'Node.js 20', icon: '📗' },
  { id: 'go', label: 'Go 1.23', icon: '🔷' },
  { id: 'ruby', label: 'Ruby 3.3', icon: '💎' },
  { id: 'bash', label: 'Bash 5.2', icon: '🐚' },
  { id: 'powershell', label: 'PowerShell 7.4', icon: '⚡' },
  { id: 'rust', label: 'Rust 1.75', icon: '🦀' },
];

export const RuntimeSelector: React.FC<RuntimeSelectorProps> = ({ value, onChange }) => {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {runtimes.map((runtime) => (
        <button
          key={runtime.id}
          onClick={() => onChange(runtime.id)}
          className={`p-4 rounded-lg border-2 transition-all ${
            value === runtime.id
              ? 'border-purple-500 bg-purple-500/20'
              : 'border-ice-navy-600 hover:border-ice-navy-500'
          }`}
        >
          <div className="text-4xl mb-2">{runtime.icon}</div>
          <p className="text-white font-medium">{runtime.label}</p>
        </button>
      ))}
    </div>
  );
};
