import React from 'react';
import {
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  Legend,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import Card from '../common/Card';
import Spinner from '../common/Spinner';

interface PieData {
  name: string;
  value: number;
}

interface PieChartProps {
  title?: string;
  subtitle?: string;
  data: PieData[];
  colors?: string[];
  isLoading?: boolean;
  height?: number;
}

const DEFAULT_COLORS = [
  '#fbbf24', // ice-gold-400
  '#f59e0b', // ice-gold-500
  '#0ea5e9', // ice-blue-500
  '#0284c7', // ice-blue-600
  '#075985', // ice-blue-800
  '#9fb3c8', // ice-navy-300
  '#827e93', // ice-navy-500
  '#6b6a7a', // slate-600
];

export default function PieChart({
  title = 'Distribution',
  subtitle,
  data,
  colors = DEFAULT_COLORS,
  isLoading = false,
  height = 300,
}: PieChartProps) {
  if (isLoading) {
    return (
      <Card title={title} subtitle={subtitle} padding="lg">
        <div className="flex items-center justify-center" style={{ height: `${height}px` }}>
          <Spinner text="Loading data..." />
        </div>
      </Card>
    );
  }

  if (!data || data.length === 0) {
    return (
      <Card title={title} subtitle={subtitle} padding="lg">
        <div className="flex items-center justify-center" style={{ height: `${height}px` }}>
          <p className="text-slate-400">No data available</p>
        </div>
      </Card>
    );
  }

  return (
    <Card title={title} subtitle={subtitle} padding="lg">
      <ResponsiveContainer width="100%" height={height}>
        <RechartsPieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, value }) => `${name}: ${value}`}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {data.map((_, index) => (
              <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: '#243b53',
              border: '1px solid #334e68',
              borderRadius: '8px',
              color: '#e0e7ff',
            }}
            formatter={(value: number) => value.toLocaleString()}
          />
          <Legend
            wrapperStyle={{ color: '#9fb3c8', paddingTop: '20px' }}
          />
        </RechartsPieChart>
      </ResponsiveContainer>
    </Card>
  );
}
