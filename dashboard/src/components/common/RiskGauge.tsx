import React from 'react';

interface RiskGaugeProps {
  score?: number;
  state?: string;
}

export const RiskGauge: React.FC<RiskGaugeProps> = ({ score = 0, state = 'SAFE' }) => {
  const safeScore = Math.min(100, Math.max(0, score));

  let barColor = 'var(--color-safe)';
  if (safeScore >= 90 || state === 'CATASTROPHIC') {
    barColor = 'var(--color-catastrophic)';
  } else if (safeScore >= 70 || state === 'CRITICAL') {
    barColor = 'var(--color-critical)';
  } else if (safeScore >= 30 || state === 'WARNING') {
    barColor = 'var(--color-warning)';
  }

  return (
    <div style={{ width: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '0.35rem' }}>
        <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
          Physical Risk Score
        </span>
        <span style={{ fontSize: '1.25rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: barColor }}>
          {safeScore.toFixed(1)} <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>/ 100</span>
        </span>
      </div>
      <div style={{ height: '8px', backgroundColor: 'var(--bg-primary)', borderRadius: '4px', overflow: 'hidden', border: '1px solid var(--border-color)' }}>
        <div
          style={{
            height: '100%',
            width: `${safeScore}%`,
            backgroundColor: barColor,
            transition: 'width 0.3s ease, background-color 0.3s ease',
            boxShadow: `0 0 8px ${barColor}`,
          }}
        />
      </div>
    </div>
  );
};
