/**
 * Events Page — Historical Security Events Log
 *
 * Full rebuild for Phase 8:
 * - Server-side pagination (50/page)
 * - Server-side filters: decision, safety_state, device, protocol, search
 * - Click row → EventDetailPanel slide-in
 * - Navigate to associated alert from detail panel
 * - Real-time row injection via WebSocket (new events prepend)
 */

import React, { useEffect, useState, useCallback } from 'react';
import { ShieldAlert, RefreshCw, Wifi, WifiOff } from 'lucide-react';
import { SecurityEvent } from '../types';
import { api } from '../services/api';
import { FilterBar } from '../components/common/FilterBar';
import { Pagination } from '../components/common/Pagination';
import { EventDetailPanel } from '../components/events/EventDetailPanel';
import { StatusBadge } from '../components/common/StatusBadge';
import { useWebSocketAlerts } from '../hooks/useWebSocketAlerts';
import { useNavigate, useLocation } from 'react-router-dom';

export const EventsPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedEvent, setSelectedEvent] = useState<SecurityEvent | null>(null);

  // Pagination
  const [page, setPage] = useState(1);
  const pageSize = 50;
  const [total, setTotal] = useState(0);
  const [hasNext, setHasNext] = useState(false);

  // Filters
  const [decisionFilter, setDecisionFilter] = useState('ALL');
  const [safetyStateFilter, setSafetyStateFilter] = useState('ALL');
  const [deviceFilter, setDeviceFilter] = useState('');
  const [protocolFilter, setProtocolFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Reset page on filter change
  useEffect(() => { setPage(1); }, [decisionFilter, safetyStateFilter, deviceFilter, protocolFilter, searchQuery]);

  const loadEvents = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.getEvents(page, pageSize, {
        decision: decisionFilter,
        safety_state: safetyStateFilter,
        device: deviceFilter || undefined,
        protocol: protocolFilter,
        search: searchQuery || undefined,
      });
      setEvents(res.items);
      setTotal(res.total);
      setHasNext(res.has_next);
    } catch (err) {
      console.error('Failed to load events:', err);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, decisionFilter, safetyStateFilter, deviceFilter, protocolFilter, searchQuery]);

  useEffect(() => {
    loadEvents();
    const interval = setInterval(loadEvents, 15000);
    return () => clearInterval(interval);
  }, [loadEvents]);

  // Handle incoming location state (e.g., navigated from Alerts page with selectedEventId)
  useEffect(() => {
    const state = location.state as { selectedEventId?: number } | null;
    if (state?.selectedEventId && events.length > 0) {
      const found = events.find(e => e.id === state.selectedEventId);
      if (found) {
        setSelectedEvent(found);
        // Clear state so it doesn't re-trigger
        navigate('/events', { replace: true, state: {} });
      }
    }
  }, [events, location.state, navigate]);

  // WebSocket — prepend new events in real-time when on page 1 / no filters
  const { wsStatus } = useWebSocketAlerts({
    onMessage: (msg) => {
      if (msg.type === 'security_event' && msg.event_id && page === 1) {
        // Inject a synthetic row at the top so the user sees it immediately
        const synthetic: SecurityEvent = {
          id: msg.event_id,
          timestamp: msg.timestamp,
          device: msg.device_id,
          protocol: msg.protocol || 'modbus_tcp',
          command: msg.command,
          command_value: msg.value,
          predicted_pressure: msg.predicted_pressure,
          predicted_flow: msg.predicted_flow,
          predicted_temperature: msg.predicted_temperature,
          risk_score: msg.risk_score,
          safety_state: msg.safety_state,
          decision: msg.decision,
          reason: msg.reason,
          alert_id: msg.alert_id,
          latency_ms: msg.total_latency_ms,
        };
        setEvents(prev => {
          // Avoid duplicates
          if (prev.some(e => e.id === synthetic.id)) return prev;
          return [synthetic, ...prev.slice(0, pageSize - 1)];
        });
        setTotal(prev => prev + 1);
      }
    },
  });

  const handleNavigateToAlert = (alertId: number) => {
    navigate('/alerts', { state: { selectedAlertId: alertId } });
  };

  const decisionColor = (d?: string) => {
    if (!d) return 'var(--text-muted)';
    if (d === 'BLOCK_CRITICAL') return 'var(--color-catastrophic)';
    if (d === 'BLOCK') return '#f87171';
    if (d === 'MONITOR') return 'var(--color-warning)';
    return 'var(--color-safe)';
  };

  const safetyColor = (s?: string) => {
    if (!s) return 'var(--text-muted)';
    if (s === 'CATASTROPHIC') return 'var(--color-catastrophic)';
    if (s === 'CRITICAL') return '#f87171';
    if (s === 'WARNING') return 'var(--color-warning)';
    return 'var(--color-safe)';
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem', height: '100%' }}>
      <div className="panel-card" style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
        <div className="panel-header">
          <span className="panel-title">
            <ShieldAlert size={18} color="var(--color-accent)" /> Historical Security Events Log
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            {/* WS Status indicator */}
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.75rem', color: wsStatus === 'LIVE' ? 'var(--color-safe)' : 'var(--text-muted)' }}>
              {wsStatus === 'LIVE' ? <Wifi size={13} /> : <WifiOff size={13} />}
              {wsStatus}
            </span>
            <button className="scada-btn" onClick={loadEvents} disabled={loading}>
              <RefreshCw size={14} className={loading ? 'spin' : ''} /> Refresh
            </button>
          </div>
        </div>

        <FilterBar
          filters={[
            {
              key: 'decision', label: 'Decision', value: decisionFilter, onChange: setDecisionFilter,
              options: [
                { value: 'ALL', label: 'All Decisions' },
                { value: 'ALLOW', label: 'ALLOW' },
                { value: 'MONITOR', label: 'MONITOR' },
                { value: 'BLOCK', label: 'BLOCK' },
                { value: 'BLOCK_CRITICAL', label: 'BLOCK_CRITICAL' },
              ]
            },
            {
              key: 'safety_state', label: 'Safety State', value: safetyStateFilter, onChange: setSafetyStateFilter,
              options: [
                { value: 'ALL', label: 'All States' },
                { value: 'SAFE', label: 'SAFE' },
                { value: 'WARNING', label: 'WARNING' },
                { value: 'CRITICAL', label: 'CRITICAL' },
                { value: 'CATASTROPHIC', label: 'CATASTROPHIC' },
              ]
            },
            {
              key: 'protocol', label: 'Protocol', value: protocolFilter, onChange: setProtocolFilter,
              options: [
                { value: 'ALL', label: 'All Protocols' },
                { value: 'modbus', label: 'Modbus/TCP' },
                { value: 'dnp3', label: 'DNP3' },
              ]
            },
          ]}
          searchValue={searchQuery}
          onSearchChange={setSearchQuery}
          placeholder="Search device, command, reason..."
        />

        <div style={{ flex: 1, overflowY: 'auto', minHeight: 0 }}>
          <table className="scada-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={{ width: '140px' }}>Timestamp</th>
                <th style={{ width: '110px' }}>Device</th>
                <th style={{ width: '90px' }}>Protocol</th>
                <th style={{ width: '120px' }}>Command</th>
                <th style={{ width: '60px' }}>Value</th>
                <th style={{ width: '100px' }}>Safety State</th>
                <th style={{ width: '130px' }}>Decision</th>
                <th style={{ width: '60px' }}>Risk</th>
                <th style={{ width: '80px' }}>Latency</th>
                <th>Reason</th>
              </tr>
            </thead>
            <tbody>
              {loading && events.length === 0 ? (
                <tr><td colSpan={10} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>Loading security events...</td></tr>
              ) : events.length === 0 ? (
                <tr><td colSpan={10} style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>No events match the current filters.</td></tr>
              ) : (
                events.map(evt => (
                  <tr
                    key={evt.id}
                    onClick={() => setSelectedEvent(evt)}
                    style={{
                      cursor: 'pointer',
                      borderLeft: `3px solid ${decisionColor(evt.decision)}`,
                      opacity: loading ? 0.6 : 1,
                    }}
                    className={selectedEvent?.id === evt.id ? 'selected' : ''}
                  >
                    <td className="mono" style={{ fontSize: '0.78rem' }}>
                      {new Date(evt.timestamp).toLocaleString()}
                    </td>
                    <td className="mono" style={{ fontSize: '0.82rem', color: 'var(--color-accent)' }}>
                      {evt.device || 'N/A'}
                    </td>
                    <td className="mono" style={{ fontSize: '0.8rem' }}>
                      {evt.protocol || '—'}
                    </td>
                    <td className="mono" style={{ fontSize: '0.8rem' }}>
                      {evt.command || '—'}
                    </td>
                    <td className="mono" style={{ fontSize: '0.8rem' }}>
                      {evt.command_value != null ? evt.command_value.toFixed(1) : '—'}
                    </td>
                    <td>
                      <span style={{ fontSize: '0.75rem', fontWeight: 700, color: safetyColor(evt.safety_state) }}>
                        {evt.safety_state || '—'}
                      </span>
                    </td>
                    <td>
                      <StatusBadge status={evt.decision || 'UNKNOWN'} type="decision" />
                    </td>
                    <td className="mono" style={{ fontSize: '0.82rem', color: (evt.risk_score ?? 0) > 70 ? '#f87171' : 'var(--text-primary)' }}>
                      {evt.risk_score != null ? evt.risk_score.toFixed(1) : '—'}
                    </td>
                    <td className="mono" style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                      {evt.latency_ms != null ? `${evt.latency_ms.toFixed(0)}ms` : '—'}
                    </td>
                    <td style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {evt.reason || '—'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <Pagination page={page} pageSize={pageSize} total={total} hasNext={hasNext} onPageChange={setPage} />
      </div>

      <EventDetailPanel
        event={selectedEvent}
        onClose={() => setSelectedEvent(null)}
        onNavigateToAlert={handleNavigateToAlert}
      />
    </div>
  );
};
