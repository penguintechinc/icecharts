import {
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  ResponsiveContainer,
} from 'recharts';
import Card from '../common/Card';
import Spinner from '../common/Spinner';

interface LatencyGaugeProps {
  title?: string;
  subtitle?: string;
  value: number;
  max?: number;
  unit?: string;
  thresholds?: {
    good: number;
    warning: number;
    critical: number;
  };
  isLoading?: boolean;
}

export default function LatencyGauge({
  title = 'Latency',
  subtitle,
  value,
  max = 1000,
  unit = 'ms',
  thresholds = {
    good: 100,
    warning: 300,
    critical: 500,
  },
  isLoading = false,
}: LatencyGaugeProps) {
  if (isLoading) {
    return (
      <Card title={title} subtitle={subtitle} padding="lg">
        <div className="flex items-center justify-center h-64">
          <Spinner text="Loading..." />
        </div>
      </Card>
    );
  }

  // Determine the status based on thresholds
  let statusColor = '#10b981'; // emerald
  let statusText = 'Excellent';

  if (value > thresholds.critical) {
    statusColor = '#ef4444'; // red
    statusText = 'Critical';
  } else if (value > thresholds.warning) {
    statusColor = '#f59e0b'; // amber
    statusText = 'Warning';
  }

  // Create gauge data
  const gaugeData = [
    { name: 'Used', value: Math.min(value, max) },
    { name: 'Remaining', value: Math.max(0, max - value) },
  ];

  const percentage = (value / max) * 100;

  return (
    <Card title={title} subtitle={subtitle} padding="lg">
      <div className="flex flex-col items-center justify-center">
        <ResponsiveContainer width="100%" height={250}>
          <RechartsPieChart>
            <Pie
              data={gaugeData}
              cx="50%"
              cy="50%"
              startAngle={180}
              endAngle={0}
              innerRadius={80}
              outerRadius={120}
              fill="#8884d8"
              dataKey="value"
              stroke="none"
            >
              <Cell fill={statusColor} />
              <Cell fill="#334e68" />
            </Pie>
          </RechartsPieChart>
        </ResponsiveContainer>

        <div className="mt-4 text-center">
          <div className="text-5xl font-bold text-ice-gold-400">
            {value.toFixed(1)}
          </div>
          <div className="text-sm text-slate-400 mt-1">{unit}</div>
          <div
            className="inline-block mt-3 px-3 py-1 rounded-full text-sm font-medium"
            style={{ backgroundColor: `${statusColor}20`, color: statusColor }}
          >
            {statusText}
          </div>
          <div className="mt-3 text-xs text-slate-500">
            {percentage.toFixed(1)}% of {max}{unit}
          </div>
        </div>
      </div>
    </Card>
  );
}
