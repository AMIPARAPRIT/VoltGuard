import React, { useEffect, useState } from 'react';
import { Bell, CheckCircle2, AlertTriangle, Info, RefreshCw } from 'lucide-react';
import { Alert } from '../types';
import { api } from '../services/api';

export const AlertsPage: React.FC = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');

  const loadAlerts = async () => {
    setLoading(true);
    try {
      const data = await api.getAlerts(100, 0);
      setAlerts(data);
    } catch (err) {
      console.error('Failed to load alerts:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, []);

  const handleAcknowledge = async (alertId: number) => {
    try {
      const updated = await api.acknowledgeAlert(alertId);
      setAlerts((prev) => prev.map((a) => (a.id === alertId ? updated : a)));
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    }
  };

  const filteredAlerts = alerts.filter((a) => {
    return severityFilter === 'ALL' || a.severity.toUpperCase() === severityFilter;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      <div className="panel-card">
        <div className="panel-header">
          <span className="panel-title"><Bell size={18} color="var(--color-critical)" /> Security & Safety Alerts</span>
          <button className="scada-btn" onClick={loadAlerts} disabled={loading}>
            <RefreshCw size={14} className={loading ? 'spin' : ''} /> Refresh
          </button>
        </div>

        <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.25rem' }}>
          <select className="scada-select" style={{ width: '200px' }} value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)}>
            <option value="ALL">All Severities</option>
            <option value="CRITICAL">CRITICAL</option>
            <option value="WARNING">WARNING</option>
            <option value="INFO">INFO</option>
          </select>
        </div>

        {loading ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>Loading security alerts...</div>
        ) : filteredAlerts.length === 0 ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>No alerts match the selected criteria.</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {filteredAlerts.map((alert) => {
              const isCrit = alert.severity === 'CRITICAL';
              const isWarn = alert.severity === 'WARNING';

              return (
                <div
                  key={alert.id}
                  style={{
                    padding: '1rem',
                    backgroundColor: 'var(--bg-secondary)',
                    borderRadius: '6px',
                    borderLeft: `4px solid ${isCrit ? 'var(--color-catastrophic)' : isWarn ? 'var(--color-warning)' : 'var(--color-accent)'}`,
                    display: 'flex',
                    alignItems: 'flex-start',
                    justifyContent: 'space-between',
                    gap: '1rem',
                  }}
                >
                  <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'flex-start' }}>
                    <div style={{ marginTop: '0.1rem' }}>
                      {isCrit ? <AlertTriangle size={20} color="#f87171" /> : isWarn ? <AlertTriangle size={20} color="var(--color-warning)" /> : <Info size={20} color="var(--color-accent)" />}
                    </div>

                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                        <span
                          className="mono"
                          style={{
                            fontSize: '0.75rem',
                            fontWeight: 700,
                            padding: '0.15rem 0.4rem',
                            borderRadius: '3px',
                            backgroundColor: isCrit ? 'var(--color-catastrophic-bg)' : isWarn ? 'var(--color-warning-bg)' : 'rgba(56, 189, 248, 0.1)',
                            color: isCrit ? '#f87171' : isWarn ? 'var(--color-warning)' : 'var(--color-accent)',
                          }}
                        >
                          {alert.severity}
                        </span>
                        <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{alert.title}</span>
                        <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                          ({alert.device || 'PLC-01'})
                        </span>
                      </div>

                      <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.35rem' }}>
                        {alert.message || 'No additional alert details available.'}
                      </div>

                      <div className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        Timestamp: {alert.timestamp ? new Date(alert.timestamp).toLocaleString() : 'N/A'}
                      </div>
                    </div>
                  </div>

                  <div>
                    {alert.acknowledged ? (
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.75rem', color: 'var(--color-safe)', fontWeight: 600 }}>
                        <CheckCircle2 size={16} /> Acknowledged
                      </span>
                    ) : (
                      <button className="scada-btn" onClick={() => handleAcknowledge(alert.id)}>
                        Acknowledge
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
