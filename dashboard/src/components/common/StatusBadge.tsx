import React from 'react';
import { SafetyState, Decision } from '../../types';

interface StatusBadgeProps {
  status?: SafetyState | Decision | string;
  type?: 'state' | 'decision';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, type = 'state' }) => {
  if (!status) {
    return <span className="status-badge">UNKNOWN</span>;
  }

  const s = String(status).toUpperCase();
  const cssClass = s.toLowerCase().replace(/[^a-z0-9]/g, '_');

  return (
    <span className={`status-badge ${cssClass}`}>
      <span style={{ fontSize: '0.65rem' }}>●</span>
      {s}
    </span>
  );
};
