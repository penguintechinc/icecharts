import React, { useState, useRef, useEffect } from 'react';

interface DropdownItem {
  id: string;
  label: string;
  icon?: React.ReactNode;
  onClick: () => void;
  divider?: boolean;
  danger?: boolean;
}

interface DropdownProps {
  items: DropdownItem[];
  trigger: React.ReactNode;
  align?: 'left' | 'right';
}

export default function Dropdown({
  items,
  trigger,
  align = 'left',
}: DropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }
  }, [isOpen]);

  const handleItemClick = (callback: () => void) => {
    callback();
    setIsOpen(false);
  };

  const alignClasses = {
    left: 'left-0',
    right: 'right-0',
  };

  return (
    <div ref={containerRef} className="relative inline-block">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center"
      >
        {trigger}
      </button>

      {isOpen && (
        <div
          className={`absolute top-full mt-2 w-48 rounded-lg bg-slate-800 border border-slate-700 shadow-lg z-50 py-1 ${alignClasses[align]}`}
          role="menu"
        >
          {items.map((item) => (
            item.divider ? (
              <div key={item.id} className="border-t border-slate-700 my-1" />
            ) : (
              <button
                key={item.id}
                onClick={() => handleItemClick(item.onClick)}
                className={`w-full flex items-center gap-3 px-4 py-2 text-sm
                  ${item.danger ? 'text-red-400 hover:bg-red-900/20' : 'text-slate-300 hover:bg-slate-700'}
                  transition-colors duration-150`}
                role="menuitem"
              >
                {item.icon && <span className="flex-shrink-0">{item.icon}</span>}
                <span>{item.label}</span>
              </button>
            )
          ))}
        </div>
      )}
    </div>
  );
}
