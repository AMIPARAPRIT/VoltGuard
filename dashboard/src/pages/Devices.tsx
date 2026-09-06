/**
 * Devices Page — OT/ICS Asset Inventory
 *
 * Full rebuild for Phase 8:
 * - Fetches real device data from GET /api/devices
 * - Device grid cards with live telemetry from DB
 * - Click device → DeviceDetailPanel (telemetry chart, alerts, events)
 * - WebSocket updates refresh last-seen / safety state in real-time
 * - No hardcoded data
 */

import React, { useEffect, useState, useCallback } from 'react';
import { Server, Activity, WifiOff, Wifi, RefreshCw, AlertTriangle, Gauge } from 'lucide-react';
import { Device } from '../types';
import { api } from '../services/api';
import { StatusBadge } from '../components/common/StatusBadge';
import { DeviceDetailPanel } from '../components/devices/DeviceDetailPanel';
import { useWebSocketAlerts } from '../hooks/useWebSocketAlerts';

export const DevicesPage: React.FC = () => {
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [total, setTotal] = useState(0);
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);

  const loadDevices = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.getDevices();
      setDevices(res.items);
      setTotal(res.total);
    } catch (err) {
      console.error('Failed to load devices:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDevices();
    const interval = setInterval(loadDevices, 20000);
    return () => clearInterval(interval);
  }, [loadDevices]);

  // WebSocket — update device card telemetry in real-time
  const { wsStatus } = useWebSocketAlerts({
    onMessage: (msg) => {
      if (msg.type === 'security_event' && msg.device_id) {
        setDevices(prev => prev.map(d => {
          if (d.device_id !== msg.device_id) return d;
          return {
            ...d,
            last_seen: msg.timestamp,
            connection_status: 'ONLINE' as const,
            last_safety_state: msg.safety_state,
            last_decision: msg.decision,
            last_risk_score: msg.risk_score,
            last_pressure: msg.predicted_pressure,
            last_flow_rate: msg.predicted_flow,
            last_temperature: msg.predicted_temperature,
          };
        }));
        // Also update selected device if it matches
        setSelectedDevice(prev => {
          if (!prev || prev.device_id !== msg.device_id) return prev;
          return {
            ...prev,
            last_seen: msg.timestamp,
            connection_status: 'ONLINE' as const,
            last_safety_state: msg.safety_state,
            last_decision: msg.decision,
            last_risk_score: msg.risk_score,
            last_pressure: msg.predicted_pressure,
            last_flow_rate: msg.predicted_flow,
            last_temperature: msg.predicted_temperature,
          };
        });
      }
    },
  });

  const getDeviceTypeIcon = (type?: string) => {
    switch (type?.toUpperCase()) {
      case 'PUMP': return '⚙';
      case 'VALVE': return '🔧';
      case 'SENSOR': return '📡';
      case 'RTU': return '📟';
      case 'PLC': return '🖥';
      default: return '⬡';
    }
  };

  const statusColor = (status: string) => {
    if (status === 'ONLINE') return 'var(--color-safe)';
    if (status === 'STALE') return 'var(--color-warning)';
    return '#f87171';
  };

  const safetyBorderColor = (state?: string) => {
    if (!state || state === 'SAFE') return 'var(--border-color)';
    if (state === 'CATASTROPHIC') return 'var(--color-catastrophic)';
    if (state === 'CRITICAL') return '#f87171';
    if (state === 'WARNING') return 'var(--color-warning)';
    return 'var(--border-color)';
  };

  const onlineCount = devices.filter(d => d.connection_status === 'ONLINE').length;
  const warningCount = devices.filter(d => d.last_safety_state && d.last_safety_state !== 'SAFE').length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Summary Strip */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
        <SummaryStrip label="Registered Assets" value={total} color="var(--color-accent)" icon={<Server size={16} />} />
        <SummaryStrip label="Online" value={onlineCount} color="var(--color-safe)" icon={<Wifi size={16} />} />
        <SummaryStrip label="Offline/Stale" value={total - onlineCount} color="var(--text-muted)" icon={<WifiOff size={16} />} />
        <SummaryStrip label="Flagged" value={warningCount} color="var(--color-warning)" icon={<AlertTriangle size={16} />} />
      </div>

      <div className="panel-card">
        <div className="panel-header">
          <span className="panel-title">
            <Server size={18} color="var(--color-accent)" /> OT / ICS Asset Inventory
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.75rem', color: wsStatus === 'LIVE' ? 'var(--color-safe)' : 'var(--text-muted)' }}>
              {wsStatus === 'LIVE' ? <Wifi size={13} /> : <WifiOff size={13} />}
              {wsStatus}
            </span>
            <button className="scada-btn" onClick={loadDevices} disabled={loading}>
              <RefreshCw size={14} className={loading ? 'spin' : ''} /> Refresh
            </button>
          </div>
        </div>

        {loading && devices.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
            <RefreshCw size={24} className="spin" style={{ marginBottom: '0.5rem' }} />
            <div>Loading OT asset registry...</div>
          </div>
        ) : devices.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
            <Server size={32} style={{ marginBottom: '1rem', opacity: 0.4 }} />
            <div style={{ fontWeight: 600, marginBottom: '0.5rem' }}>No Devices Registered</div>
            <div style={{ fontSize: '0.85rem' }}>Devices auto-register when they send their first Modbus/DNP3 packet through the pipeline. Start a simulation stream to populate this registry.</div>
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
            {devices.map((dev) => (
              <div
                key={dev.id}
                onClick={() => setSelectedDevice(dev)}
                style={{
                  padding: '1.25rem',
                  backgroundColor: 'var(--bg-secondary)',
                  borderRadius: '6px',
                  border: `1px solid ${safetyBorderColor(dev.last_safety_state)}`,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '1rem',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  boxShadow: selectedDevice?.id === dev.id ? `0 0 0 2px var(--color-accent)` : 'none',
                }}
                onMouseOver={e => (e.currentTarget.style.backgroundColor = 'var(--bg-card-hover)')}
                onMouseOut={e => (e.currentTarget.style.backgroundColor = 'var(--bg-secondary)')}
              >
                {/* Device Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                      <span style={{ fontSize: '1.1rem' }}>{getDeviceTypeIcon(dev.device_type)}</span>
                      <span style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)', fontFamily: 'monospace' }}>{dev.device_id}</span>
                    </div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                      {dev.device_type || 'OT Device'} · {dev.protocol || 'Unknown Protocol'}
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.75rem', color: statusColor(dev.connection_status), fontWeight: 600 }}>
                    <Activity size={13} />
                    {dev.connection_status}
                  </div>
                </div>

                {/* Network Info */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.4rem', fontSize: '0.75rem', backgroundColor: 'var(--bg-primary)', padding: '0.6rem', borderRadius: '4px' }}>
                  <div><span style={{ color: 'var(--text-muted)' }}>IP:</span> <span className="mono">{dev.ip_address || '—'}</span></div>
                  <div><span style={{ color: 'var(--text-muted)' }}>Protocol:</span> <span className="mono">{dev.protocol || '—'}</span></div>
                  <div><span style={{ color: 'var(--text-muted)' }}>Last Seen:</span> <span>{dev.last_seen ? new Date(dev.last_seen).toLocaleTimeString() : 'Never'}</span></div>
                  <div><span style={{ color: 'var(--text-muted)' }}>Risk Score:</span> <span className="mono" style={{ color: (dev.last_risk_score ?? 0) > 60 ? '#f87171' : 'var(--text-primary)' }}>{dev.last_risk_score?.toFixed(1) ?? '—'}</span></div>
                </div>

                {/* Telemetry snapshot */}
                {(dev.last_pressure != null || dev.last_flow_rate != null || dev.last_pump_rpm != null) && (
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.4rem' }}>
                    {dev.last_pressure != null && (
                      <MiniMetric label="Pressure" value={dev.last_pressure} unit="bar" />
                    )}
                    {dev.last_flow_rate != null && (
                      <MiniMetric label="Flow" value={dev.last_flow_rate} unit="m³/h" />
                    )}
                    {dev.last_pump_rpm != null && (
                      <MiniMetric label="RPM" value={dev.last_pump_rpm} unit="rpm" />
                    )}
                  </div>
                )}

                {/* Safety Classification footer */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '0.75rem', borderTop: '1px solid var(--border-color)' }}>
                  <div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>Safety Classification</div>
                    <StatusBadge status={dev.last_safety_state || 'UNKNOWN'} type="state" />
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>Last Decision</div>
                    <StatusBadge status={dev.last_decision || 'UNKNOWN'} type="decision" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <DeviceDetailPanel device={selectedDevice} onClose={() => setSelectedDevice(null)} />
    </div>
  );
};

const SummaryStrip = ({ label, value, color, icon }: { label: string; value: number; color: string; icon: React.ReactNode }) => (
  <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '1rem', borderRadius: '6px', borderTop: `3px solid ${color}` }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)', fontSize: '0.78rem', marginBottom: '0.5rem' }}>
      {React.cloneElement(icon as React.ReactElement, { color })} {label}
    </div>
    <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)' }}>{value}</div>
  </div>
);

const MiniMetric = ({ label, value, unit }: { label: string; value: number; unit: string }) => (
  <div style={{ backgroundColor: 'var(--bg-primary)', padding: '0.5rem', borderRadius: '4px', textAlign: 'center' }}>
    <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.15rem' }}>{label}</div>
    <div className="mono" style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)' }}>
      {value.toFixed(1)}<span style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginLeft: '1px' }}>{unit}</span>
    </div>
  </div>
);
