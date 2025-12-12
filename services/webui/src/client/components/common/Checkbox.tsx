import React from 'react';

interface CheckboxProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export default function Checkbox({
  label,
  error,
  id,
  className = '',
  ...props
}: CheckboxProps) {
  const checkboxId = id || `checkbox-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <div className="flex items-start">
      <div className="flex items-center h-6">
        <input
          id={checkboxId}
          type="checkbox"
          className={`h-4 w-4 rounded border-slate-600 bg-slate-800 text-ice-gold-400
            focus:ring-2 focus:ring-ice-gold-400 focus:ring-offset-0 cursor-pointer
            transition-colors duration-200
            ${className}`}
          {...props}
        />
      </div>
      {label && (
        <div className="ml-3">
          <label
            htmlFor={checkboxId}
            className="text-sm font-medium text-slate-300 cursor-pointer"
          >
            {label}
          </label>
          {error && (
            <p className="mt-1 text-sm text-red-400">{error}</p>
          )}
        </div>
      )}
    </div>
  );
}
