import React, { useState } from 'react';

interface ToggleProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label?: string;
  onChange?: (checked: boolean) => void;
}

export default function Toggle({
  label,
  onChange,
  checked: controlledChecked,
  defaultChecked,
  className = '',
  ...props
}: ToggleProps) {
  const [internalChecked, setInternalChecked] = useState(defaultChecked || false);
  const isControlled = controlledChecked !== undefined;
  const checked = isControlled ? controlledChecked : internalChecked;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newChecked = e.target.checked;
    if (!isControlled) {
      setInternalChecked(newChecked);
    }
    onChange?.(newChecked);
  };

  return (
    <div className="flex items-center gap-3">
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => handleChange({ target: { checked: !checked } } as any)}
        className={`relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent
          transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-ice-gold-400 focus:ring-offset-2 focus:ring-offset-slate-900
          ${checked ? 'bg-ice-gold-400' : 'bg-slate-700'}
          ${className}`}
      >
        <span
          className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0
            transition duration-200 ease-in-out
            ${checked ? 'translate-x-5' : 'translate-x-0'}`}
        />
      </button>
      {label && (
        <label className="text-sm font-medium text-slate-300 cursor-pointer">
          {label}
        </label>
      )}
    </div>
  );
}
