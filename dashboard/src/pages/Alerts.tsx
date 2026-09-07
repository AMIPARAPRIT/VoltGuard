/**
 * Alerts Center — Security & Safety Alerts
 *
 * Phase 8 full implementation:
 * - Summary counters bar (ACTIVE / CATASTROPHIC / CRITICAL / ACKNOWLEDGED / RESOLVED)
 * - Compact filter toolbar (severity, status, search)
 * - Alert table with columns: TIME, SEVERITY, STATUS, DEVICE, TITLE
 * - Click row → AlertDetailPanel slide-in
 * - ACKNOWLEDGE / RESOLVE buttons with toast feedback
 * - WebSocket: new alerts prepend to list + counters update in real-time
 */

import React, { useEffect, useState, useCallback } from 'react';
import { Bell, CheckCircle2, AlertTriangle, ShieldAlert, RefreshCw, Wifi, WifiOff } from 'lucide-react';
import { Alert, AlertSummary } from '../types';
import { api } from '../services/api';
import { toast } from '../services/toast';
import { FilterBar } from '../components/common/FilterBar';
import { Pagination } from '../components/common/Pagination';
import { AlertDetailPanel } from '../components/alerts/AlertDetailPanel';
import { useWebSocketAlerts } from '../hooks/useWebSocketAlerts';
import { useNavigate, useLocation } from 'react-router-dom';

export const AlertsPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [summary, setSummary] = useState<AlertSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Pagination & Filters
  const [page, setPage] = useState(1);
  const pageSize = 20;
  const [total, setTotal] = useState(0);
  const [hasNext, setHasNext] = useState(false);

  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [summaryData, alertsData] = await Promise.all([
        api.getAlertSummary(),
        api.getAlerts(page, pageSize, {
          severity: severityFilter,
          status: statusFilter,
          search: searchQuery,
        })
      ]);
      setSummary(summaryData);
      setAlerts(alertsData.items);
      setTotal(alertsData.total);
      setHasNext(alertsData.has_next);
    } catch (err) {
      console.error('Failed to load alerts:', err);
      toast.error('Failed to load alerts', 'Could not fetch alerts from server.');
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, severityFilter, statusFilter, searchQuery]);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, [loadData]);

  // Reset page when filters change
  useEffect(() => {
    setPage(1);
  }, [severityFilter, statusFilter, searchQuery]);

  // Handle navigation from Events page with selectedAlertId in location state
  useEffect(() => {
    const state = location.state as { selectedAlertId?: number } | null;
    if (state?.selectedAlertId && alerts.length > 0) {
      const found = alerts.find(a => a.id === state.selectedAlertId);
      if (found) {
        setSelectedAlert(found);
        navigate('/alerts', { replace: true, state: {} });
      }
    }
  }, [alerts, location.state, navigate]);

  // WebSocket — prepend new alerts and update summary counter in real-time
  const { wsStatus } = useWebSocketAlerts({
    onNewAlert: (msg) => {
      // Refresh summary counter
      api.getAlertSummary().then(setSummary).catch(() => {});
      // Only inject into table if we are on page 1 with no filters
      if (page === 1 && statusFilter === 'ALL' && severityFilter === 'ALL' && !searchQuery) {
        toast.info('New Alert', `Device ${msg.device_id}: ${msg.decision} — ${msg.reason?.slice(0, 80)}`);
        loadData();
      }
    },
  });

  const handleAlertUpdated = (updatedAlert: Alert) => {
    setAlerts(prev => prev.map(a => a.id === updatedAlert.id ? updatedAlert : a));
    if (selectedAlert?.id === updatedAlert.id) {
      setSelectedAlert(updatedAlert);
    }
    // Reload summary to update counters
    api.getAlertSummary().then(setSummary).catch(() => {});
  };

  const handleNavigateToEvent = (eventId: number) => {
    navigate('/events', { state: { selectedEventId: eventId } });
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', height: '100%' }}>

      {/* Summary Counters Bar */}
      {summary && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '1rem' }}>
          <SummaryCard title="Active Alerts" value={summary.active} color="var(--color-warning)" icon={<Bell size={18} />} />
          <SummaryCard title="Catastrophic" value={summary.catastrophic} color="var(--color-catastrophic)" icon={<ShieldAlert size={18} />} />
          <SummaryCard title="Critical" value={summary.critical} color="#f87171" icon={<AlertTriangle size={18} />} />
          <SummaryCard title="Acknowledged" value={summary.acknowledged} color="var(--color-accent)" icon={<CheckCircle2 size={18} />} />
          <SummaryCard title="Resolved" value={summary.resolved} color="var(--color-safe)" icon={<CheckCircle2 size={18} />} />
        </div>
      )}

      <div className="panel-card" style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <div className="panel-header">
          <span className="panel-title"><Bell size={18} color="var(--color-critical)" /> Security &amp; Safety Alerts</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            {/* WS Status indicator */}
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.75rem', color: wsStatus === 'LIVE' ? 'var(--color-safe)' : 'var(--text-muted)' }}>
              {wsStatus === 'LIVE' ? <Wifi size={13} /> : <WifiOff size={13} />}
              {wsStatus}
            </span>
            <button className="scada-btn" onClick={loadData} disabled={loading}>
              <RefreshCw size={14} className={loading ? 'spin' : ''} /> Refresh
            </button>
          </div>
        </div>

        <FilterBar
          filters={[
            {
              key: 'status', label: 'Status', value: statusFilter, onChange: setStatusFilter,
              options: [
                { value: 'ALL', label: 'All Statuses' },
                { value: 'ACTIVE', label: 'Active' },
                { value: 'ACKNOWLEDGED', label: 'Acknowledged' },
                { value: 'RESOLVED', label: 'Resolved' }
              ]
            },
            {
              key: 'severity', label: 'Severity', value: severityFilter, onChange: setSeverityFilter,
              options: [
                { value: 'ALL', label: 'All Severities' },
                { value: 'CATASTROPHIC', label: 'Catastrophic' },
                { value: 'CRITICAL', label: 'Critical' },
                { value: 'WARNING', label: 'Warning' },
                { value: 'INFO', label: 'Info' }
              ]
            }
          ]}
          searchValue={searchQuery}
          onSearchChange={setSearchQuery}
          placeholder="Search by device, title, message..."
        />

        <div style={{ flex: 1, overflowY: 'auto' }}>
          <table className="scada-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={{ width: '150px' }}>Time</th>
                <th style={{ width: '130px' }}>Severity</th>
                <th style={{ width: '130px' }}>Status</th>
                <th style={{ width: '150px' }}>Device</th>
                <th>Alert Title</th>
              </tr>
            </thead>
            <tbody>
              {loading && alerts.length === 0 ? (
                <tr><td colSpan={5} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>Loading alerts...</td></tr>
              ) : alerts.length === 0 ? (
                <tr><td colSpan={5} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>No alerts found matching criteria.</td></tr>
              ) : (
                alerts.map(alert => {
                  const isCrit = alert.severity === 'CATASTROPHIC' || alert.severity === 'CRITICAL';
                  const isWarn = alert.severity === 'WARNING';
                  const severityColor =
                    alert.severity === 'CATASTROPHIC' ? 'var(--color-catastrophic)'
                    : isCrit ? '#f87171'
                    : isWarn ? 'var(--color-warning)'
                    : 'var(--color-accent)';
                  return (
                    <tr
                      key={alert.id}
                      onClick={() => setSelectedAlert(alert)}
                      style={{
                        cursor: 'pointer',
                        borderLeft: `3px solid ${severityColor}`,
                        opacity: loading ? 0.6 : 1,
                      }}
                      className={selectedAlert?.id === alert.id ? 'selected' : ''}
                    >
                      <td className="mono" style={{ fontSize: '0.8rem' }}>{new Date(alert.timestamp).toLocaleString()}</td>
                      <td>
                        <span style={{
                          fontSize: '0.75rem', fontWeight: 700, padding: '0.2rem 0.5rem', borderRadius: '4px',
                          backgroundColor: alert.severity === 'CATASTROPHIC' ? 'rgba(255,0,0,0.2)' : isCrit ? 'var(--color-catastrophic-bg)' : isWarn ? 'var(--color-warning-bg)' : 'rgba(56, 189, 248, 0.1)',
                          color: severityColor,
                        }}>
                          {alert.severity}
                        </span>
                      </td>
                      <td>
                        <span style={{
                          fontSize: '0.75rem', fontWeight: 600,
                          color: alert.status === 'RESOLVED' ? 'var(--color-safe)' : alert.status === 'ACKNOWLEDGED' ? 'var(--color-accent)' : 'var(--color-warning)'
                        }}>
                          {alert.status}
                        </span>
                      </td>
                      <td className="mono" style={{ fontSize: '0.85rem' }}>{alert.device || 'N/A'}</td>
                      <td style={{ fontWeight: alert.status === 'ACTIVE' ? 600 : 400 }}>{alert.title}</td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        <Pagination page={page} pageSize={pageSize} total={total} hasNext={hasNext} onPageChange={setPage} />
      </div>

      <AlertDetailPanel
        alert={selectedAlert}
        onClose={() => setSelectedAlert(null)}
        onAlertUpdated={handleAlertUpdated}
        onNavigateToEvent={handleNavigateToEvent}
      />
    </div>
  );
};

const SummaryCard = ({ title, value, color, icon }: { title: string; value: number; color: string; icon: React.ReactNode }) => (
  <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '1rem', borderRadius: '6px', borderTop: `3px solid ${color}` }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: '0.5rem' }}>
      {React.cloneElement(icon as React.ReactElement, { color })} {title}
    </div>
    <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)' }}>{value}</div>
  </div>
);
