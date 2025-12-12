import React from 'react';

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  helperText?: string;
  required?: boolean;
}

export default function Textarea({
  label,
  error,
  helperText,
  required,
  id,
  className = '',
  ...props
}: TextareaProps) {
  const textareaId = id || `textarea-${Math.random().toString(36).substr(2, 9)}`;

  return (
    <div className="w-full">
      {label && (
        <label
          htmlFor={textareaId}
          className="block text-sm font-medium text-slate-300 mb-2"
        >
          {label}
          {required && <span className="text-red-400 ml-1">*</span>}
        </label>
      )}
      <textarea
        id={textareaId}
        className={`w-full px-3 py-2 bg-slate-800 border rounded-lg text-slate-100 placeholder-slate-500
          ${error ? 'border-red-500 focus:ring-red-500' : 'border-slate-700 focus:ring-ice-gold-400'}
          focus:outline-none focus:border-ice-gold-400 focus:ring-1
          transition-colors duration-200 resize-none
          ${className}`}
        {...props}
      />
      {error && (
        <p className="mt-1 text-sm text-red-400">{error}</p>
      )}
      {helperText && !error && (
        <p className="mt-1 text-sm text-slate-400">{helperText}</p>
      )}
    </div>
  );
}
