import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  CartesianGrid,
} from 'recharts';

export interface TelemetryDataPoint {
  t: string;         // display time label
  value: number;
}

interface TelemetryChartProps {
  data: TelemetryDataPoint[];
  label: string;
  unit: string;
  color: string;
  limit?: number;
  limitLabel?: string;
  domain?: [number | 'auto', number | 'auto'];
  currentValue: number | null;
}

const CustomTooltip: React.FC<{ active?: boolean; payload?: Array<{ value: number }>; label?: string; unit: string }> = ({
  active,
  payload,
  label,
  unit,
}) => {
  if (active && payload && payload.length) {
    return (
      <div
        style={{
          background: 'var(--bg-secondary)',
          border: '1px solid var(--border-highlight)',
          borderRadius: '4px',
          padding: '0.4rem 0.75rem',
          fontSize: '0.75rem',
          fontFamily: 'var(--font-mono)',
          color: 'var(--text-primary)',
        }}
      >
        <div style={{ color: 'var(--text-muted)', marginBottom: '0.15rem' }}>{label}</div>
        <div style={{ fontWeight: 700 }}>
          {payload[0].value.toFixed(2)} {unit}
        </div>
      </div>
    );
  }
  return null;
};

export const TelemetryChart: React.FC<TelemetryChartProps> = ({
  data,
  label,
  unit,
  color,
  limit,
  limitLabel,
  domain,
  currentValue,
}) => {
  const safeData = data.length > 0 ? data : [{ t: '--', value: 0 }];

  // Determine if current value exceeds the limit
  const isOverLimit = limit !== undefined && currentValue !== null && currentValue > limit;
  const displayColor = isOverLimit ? 'var(--color-critical)' : color;

  return (
    <div
      style={{
        padding: '1rem',
        backgroundColor: 'var(--bg-secondary)',
        borderRadius: '6px',
        border: `1px solid ${isOverLimit ? 'var(--color-critical-border)' : 'var(--border-color)'}`,
        transition: 'border-color 0.3s ease',
      }}
    >
      {/* Header row */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '0.5rem' }}>
        <span style={{ fontSize: '0.7rem', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          {label}
        </span>
        <span
          style={{
            fontFamily: 'var(--font-mono)',
            fontWeight: 700,
            fontSize: '1.1rem',
            color: displayColor,
            transition: 'color 0.3s ease',
          }}
        >
          {currentValue !== null ? currentValue.toFixed(1) : '--'}{' '}
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 400 }}>{unit}</span>
        </span>
      </div>

      {/* Recharts Area Chart */}
      <ResponsiveContainer width="100%" height={90}>
        <AreaChart data={safeData} margin={{ top: 4, right: 4, bottom: 0, left: -24 }}>
          <defs>
            <linearGradient id={`grad-${label.replace(/\s/g, '')}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={displayColor} stopOpacity={0.3} />
              <stop offset="95%" stopColor={displayColor} stopOpacity={0.0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" vertical={false} />
          <XAxis
            dataKey="t"
            tick={{ fontSize: 9, fill: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}
            tickLine={false}
            axisLine={false}
            interval="preserveStartEnd"
          />
          <YAxis
            domain={domain || ['auto', 'auto']}
            tick={{ fontSize: 9, fill: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}
            tickLine={false}
            axisLine={false}
            width={40}
          />
          <Tooltip content={<CustomTooltip unit={unit} />} />
          {limit !== undefined && (
            <ReferenceLine
              y={limit}
              stroke="var(--color-critical)"
              strokeDasharray="4 3"
              strokeWidth={1.5}
              label={{
                value: limitLabel || `LIMIT: ${limit}`,
                position: 'insideTopRight',
                fontSize: 9,
                fill: 'var(--color-critical)',
                fontFamily: 'var(--font-mono)',
              }}
            />
          )}
          <Area
            type="monotone"
            dataKey="value"
            stroke={displayColor}
            strokeWidth={2}
            fill={`url(#grad-${label.replace(/\s/g, '')})`}
            dot={false}
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>

      {/* Limit indicator */}
      {limit !== undefined && (
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.35rem' }}>
          <span style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', color: isOverLimit ? 'var(--color-critical)' : 'var(--text-muted)' }}>
            {isOverLimit ? '⚠ LIMIT EXCEEDED' : `LIMIT: ${limit} ${unit}`}
          </span>
        </div>
      )}
    </div>
  );
};
