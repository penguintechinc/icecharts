import React from 'react';
import Card from '../common/Card';
import Spinner from '../common/Spinner';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: React.ReactNode;
  change?: number;
  changeLabel?: string;
  variant?: 'default' | 'positive' | 'negative' | 'warning';
  isLoading?: boolean;
  className?: string;
}

export default function MetricCard({
  title,
  value,
  subtitle,
  icon,
  change,
  changeLabel = 'from last period',
  variant = 'default',
  isLoading = false,
  className = '',
}: MetricCardProps) {
  if (isLoading) {
    return (
      <Card padding="lg" className={`min-h-24 flex items-center justify-center ${className}`}>
        <Spinner size="sm" />
      </Card>
    );
  }

  const getChangeColor = () => {
    if (change === undefined) return 'text-slate-400';
    if (variant === 'positive') {
      return change >= 0 ? 'text-emerald-400' : 'text-red-400';
    }
    if (variant === 'negative') {
      return change <= 0 ? 'text-emerald-400' : 'text-red-400';
    }
    if (variant === 'warning') {
      return change >= 0 ? 'text-amber-400' : 'text-emerald-400';
    }
    return 'text-slate-400';
  };

  const getChangeIcon = () => {
    if (change === undefined) return null;
    if (change > 0) return '↑';
    if (change < 0) return '↓';
    return '→';
  };

  return (
    <Card padding="md" className={className}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-slate-400">{title}</p>
          <div className="mt-2 flex items-baseline gap-2">
            <div className="text-3xl font-bold text-white">
              {typeof value === 'number' ? value.toLocaleString() : value}
            </div>
          </div>

          {change !== undefined && (
            <div className={`mt-2 text-xs font-medium ${getChangeColor()}`}>
              <span className="inline-block mr-1">{getChangeIcon()}</span>
              {Math.abs(change).toFixed(1)}%
              <span className="text-slate-400 ml-1">{changeLabel}</span>
            </div>
          )}

          {subtitle && (
            <p className="mt-2 text-xs text-slate-500">{subtitle}</p>
          )}
        </div>

        {icon && (
          <div className="ml-4 flex-shrink-0 text-ice-gold-400">
            {icon}
          </div>
        )}
      </div>
    </Card>
  );
}
