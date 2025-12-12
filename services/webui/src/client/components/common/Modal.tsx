import React, { useEffect } from 'react';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
  size?: 'sm' | 'md' | 'lg';
  closeButton?: boolean;
}

export default function Modal({
  isOpen,
  onClose,
  title,
  children,
  footer,
  size = 'md',
  closeButton = true,
}: ModalProps) {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      const handleEscape = (e: KeyboardEvent) => {
        if (e.key === 'Escape') {
          onClose();
        }
      };
      document.addEventListener('keydown', handleEscape);
      return () => {
        document.removeEventListener('keydown', handleEscape);
        document.body.style.overflow = 'unset';
      };
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const sizeClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />
      <div
        className={`relative bg-slate-800 border border-slate-700 rounded-lg shadow-lg ${sizeClasses[size]} w-full mx-4`}
        role="dialog"
        aria-modal="true"
      >
        {/* Header */}
        {(title || closeButton) && (
          <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700">
            {title && <h2 className="text-lg font-semibold text-ice-gold-400">{title}</h2>}
            {closeButton && (
              <button
                onClick={onClose}
                className="text-slate-400 hover:text-slate-200 transition-colors"
                aria-label="Close dialog"
              >
                <svg
                  className="h-6 w-6"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                >
                  <path d="M18 6L6 18M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        )}

        {/* Body */}
        <div className="px-6 py-4 max-h-96 overflow-y-auto">
          {children}
        </div>

        {/* Footer */}
        {footer && (
          <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-slate-700">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}
