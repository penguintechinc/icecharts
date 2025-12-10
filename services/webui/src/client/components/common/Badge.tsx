import React from 'react';

type BadgeVariant = 'default' | 'success' | 'warning' | 'error' | 'info' | 'admin' | 'maintainer' | 'viewer';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  size?: 'sm' | 'md';
  icon?: React.ReactNode;
  className?: string;
}

export default function Badge({
  children,
  variant = 'default',
  size = 'sm',
  icon,
  className = '',
}: BadgeProps) {
  const variantClasses = {
    default: 'bg-slate-700 text-slate-200',
    success: 'bg-emerald-900/50 text-emerald-300',
    warning: 'bg-amber-900/50 text-amber-300',
    error: 'bg-red-900/50 text-red-300',
    info: 'bg-blue-900/50 text-blue-300',
    admin: 'bg-red-900/50 text-red-400',
    maintainer: 'bg-blue-900/50 text-blue-400',
    viewer: 'bg-green-900/50 text-green-400',
  };

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-3 py-1 text-sm',
  };

  return (
    <span
      className={`inline-flex items-center gap-1 font-medium rounded-full ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
    >
      {icon && <span className="flex-shrink-0">{icon}</span>}
      {children}
    </span>
  );
}
