import React from 'react';
import { SecurityEvent } from '../../types';
import { StatusBadge } from '../common/StatusBadge';

interface EventTableProps {
  events: SecurityEvent[];
  loading?: boolean;
}

export const EventTable: React.FC<EventTableProps> = ({ events, loading = false }) => {
  if (loading) {
    return <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>Loading security events...</div>;
  }

  if (events.length === 0) {
    return <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>No security events recorded.</div>;
  }

  return (
    <div style={{ overflowX: 'auto' }}>
      <table className="scada-table">
        <thead>
          <tr>
            <th>Time</th>
            <th>Device</th>
            <th>Protocol</th>
            <th>Command</th>
            <th>Value</th>
            <th>Pressure</th>
            <th>Risk</th>
            <th>Safety State</th>
            <th>Decision</th>
          </tr>
        </thead>
        <tbody>
          {events.map((evt) => {
            const timeStr = evt.timestamp ? new Date(evt.timestamp).toLocaleTimeString() : 'N/A';
            return (
              <tr key={evt.id || Math.random()}>
                <td className="mono" style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{timeStr}</td>
                <td style={{ fontWeight: 600 }}>{evt.device || 'PLC-01'}</td>
                <td className="mono">{evt.protocol || 'Modbus/TCP'}</td>
                <td className="mono" style={{ color: 'var(--color-accent)' }}>{evt.command || 'N/A'}</td>
                <td className="mono">{evt.command_value !== undefined ? evt.command_value : '-'}</td>
                <td className="mono">{evt.predicted_pressure ? `${evt.predicted_pressure.toFixed(1)} bar` : '-'}</td>
                <td className="mono" style={{ fontWeight: 700 }}>
                  {evt.risk_score !== undefined ? evt.risk_score.toFixed(1) : '-'}
                </td>
                <td><StatusBadge status={evt.safety_state} type="state" /></td>
                <td><StatusBadge status={evt.decision} type="decision" /></td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
