import React, { useEffect, useState, useRef } from 'react';
import { ShieldCheck, ShieldAlert, Cpu, AlertTriangle, Activity, Zap } from 'lucide-react';
import { SecurityEvent, Alert, Telemetry, WebSocketMessage } from '../types';
import { api } from '../services/api';
import { wsService } from '../services/websocket';
import { StatusBadge } from '../components/common/StatusBadge';
import { RiskGauge } from '../components/common/RiskGauge';
import { EventTable } from '../components/tables/EventTable';
import { PhysicsChartsPanel, TelemetryHistory } from '../components/common/PhysicsChartsPanel';
import { TelemetryDataPoint } from '../components/common/TelemetryChart';

const MAX_HISTORY = 60;

function formatTime(ts?: string): string {
  if (!ts) return '--:--';
  try {
    return new Date(ts).toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
  } catch {
    return '--:--';
  }
}

function appendHistory(
  prev: TelemetryDataPoint[],
  value: number | undefined,
  ts: string,
): TelemetryDataPoint[] {
  if (value === undefined || value === null) return prev;
  const next = [...prev, { t: formatTime(ts), value }];
  return next.length > MAX_HISTORY ? next.slice(next.length - MAX_HISTORY) : next;
}

export const Dashboard: React.FC = () => {
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [telemetry, setTelemetry] = useState<Telemetry | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [liveStream, setLiveStream] = useState<WebSocketMessage[]>([]);

  // Rolling history for Recharts
  const [history, setHistory] = useState<TelemetryHistory>({
    pressure: [],
    flow: [],
    temperature: [],
    rpm: [],
  });

  // Seed history from REST telemetry data on first load
  const historySeeded = useRef(false);

  useEffect(() => {
    async function loadInitialData() {
      try {
        const [evtData, alertData, telemData] = await Promise.all([
          api.getEvents(1, 20),
          api.getAlerts(1, 10),
          api.getTelemetry(60, 0),
        ]);
        setEvents(evtData.items);
        setAlerts(alertData.items);

        // Seed charts from historical REST data (most-recent telemetry rows, oldest first)
        if (!historySeeded.current && telemData && telemData.items.length > 0) {
          historySeeded.current = true;
          const sorted = [...telemData.items].reverse(); // oldest → newest
          const seedPressure: TelemetryDataPoint[] = sorted
            .filter((t) => t.pressure !== undefined)
            .map((t) => ({ t: formatTime(t.timestamp), value: t.pressure! }));
          const seedFlow: TelemetryDataPoint[] = sorted
            .filter((t) => t.flow_rate !== undefined)
            .map((t) => ({ t: formatTime(t.timestamp), value: t.flow_rate! }));
          const seedTemp: TelemetryDataPoint[] = sorted
            .filter((t) => t.temperature !== undefined)
            .map((t) => ({ t: formatTime(t.timestamp), value: t.temperature! }));
          const seedRpm: TelemetryDataPoint[] = sorted
            .filter((t) => t.pump_rpm !== undefined)
            .map((t) => ({ t: formatTime(t.timestamp), value: t.pump_rpm! }));

          setHistory({
            pressure: seedPressure.slice(-MAX_HISTORY),
            flow: seedFlow.slice(-MAX_HISTORY),
            temperature: seedTemp.slice(-MAX_HISTORY),
            rpm: seedRpm.slice(-MAX_HISTORY),
          });

          // Set current telemetry snapshot from most recent record
          setTelemetry(telemData.items[0]);
        }
      } catch (err) {
        console.error('Failed to load dashboard data:', err);
      } finally {
        setLoading(false);
      }
    }

    loadInitialData();

    // Subscribe to live WebSocket updates
    const unsub = wsService.subscribeMessage((msg) => {
      setLiveStream((prev) => [msg, ...prev.slice(0, 15)]);

      if (msg.type === 'security_event') {
        const newEvt: SecurityEvent = {
          id: msg.event_id || Math.floor(Math.random() * 10000),
          timestamp: msg.timestamp || new Date().toISOString(),
          device: msg.device_id || 'PLC-01',
          protocol: msg.protocol || 'Modbus/TCP',
          command: msg.command,
          command_value: msg.value,
          predicted_pressure: msg.predicted_pressure,
          predicted_flow: msg.predicted_flow,
          predicted_temperature: msg.predicted_temperature,
          risk_score: msg.risk_score,
          safety_state: msg.safety_state,
          decision: msg.decision,
          latency_ms: msg.total_latency_ms,
        };
        setEvents((prev) => [newEvt, ...prev.slice(0, 19)]);

        // Update live snapshot telemetry
        if (msg.predicted_pressure !== undefined) {
          setTelemetry({
            timestamp: msg.timestamp,
            device: msg.device_id,
            pump_rpm: msg.command === 'SET_RPM' && msg.value !== undefined ? msg.value : undefined,
            valve_position: 50,
            pressure: msg.predicted_pressure,
            flow_rate: msg.predicted_flow,
            temperature: msg.predicted_temperature,
          });
        }

        // Append to rolling chart history
        const ts = msg.timestamp || new Date().toISOString();
        setHistory((prev) => ({
          pressure: appendHistory(prev.pressure, msg.predicted_pressure, ts),
          flow: appendHistory(prev.flow, msg.predicted_flow, ts),
          temperature: appendHistory(prev.temperature, msg.predicted_temperature, ts),
          rpm:
            msg.command === 'SET_RPM' && msg.value !== undefined
              ? appendHistory(prev.rpm, msg.value, ts)
              : prev.rpm,
        }));
      }
    });

    return () => unsub();
  }, []);

  const latestEvent = events.length > 0 ? events[0] : null;
  const currentRisk = latestEvent?.risk_score ?? 0;
  const currentSafetyState = latestEvent?.safety_state ?? 'SAFE';
  const currentDecision = latestEvent?.decision ?? 'ALLOW';

  const blockedCount = events.filter((e) => e.decision === 'BLOCK' || e.decision === 'BLOCK_CRITICAL').length;
  const criticalAlertsCount = alerts.filter((a) => a.severity === 'CRITICAL' && !a.acknowledged).length;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Top KPI Status Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
        <div className="panel-card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ padding: '0.6rem', backgroundColor: 'var(--color-safe-bg)', borderRadius: '6px', border: '1px solid var(--color-safe-border)' }}>
            <Activity color="var(--color-safe)" size={22} />
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>System Mode</div>
            <div style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--color-safe)' }}>OPERATIONAL</div>
          </div>
        </div>

        <div className="panel-card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ padding: '0.6rem', backgroundColor: 'rgba(56, 189, 248, 0.1)', borderRadius: '6px', border: '1px solid rgba(56, 189, 248, 0.3)' }}>
            <Cpu color="var(--color-accent)" size={22} />
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>Active OT Assets</div>
            <div className="mono" style={{ fontSize: '1.2rem', fontWeight: 700 }}>6 Devices</div>
          </div>
        </div>

        <div className="panel-card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ padding: '0.6rem', backgroundColor: 'rgba(148, 163, 184, 0.1)', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
            <ShieldCheck color="var(--text-secondary)" size={22} />
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>Total Events</div>
            <div className="mono" style={{ fontSize: '1.2rem', fontWeight: 700 }}>{events.length}</div>
          </div>
        </div>

        <div className="panel-card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ padding: '0.6rem', backgroundColor: 'var(--color-critical-bg)', borderRadius: '6px', border: '1px solid var(--color-critical-border)' }}>
            <ShieldAlert color="var(--color-critical)" size={22} />
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>Blocked Threats</div>
            <div className="mono" style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--color-critical)' }}>{blockedCount}</div>
          </div>
        </div>

        <div className="panel-card" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ padding: '0.6rem', backgroundColor: 'var(--color-catastrophic-bg)', borderRadius: '6px', border: '1px solid var(--color-catastrophic-border)' }}>
            <AlertTriangle color="#f87171" size={22} />
          </div>
          <div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>Critical Alerts</div>
            <div className="mono" style={{ fontSize: '1.2rem', fontWeight: 700, color: '#f87171' }}>{criticalAlertsCount}</div>
          </div>
        </div>
      </div>

      {/* Risk Assessment & Live Event Stream Row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '1.25rem' }}>
        {/* Risk & Decision Status */}
        <div className="panel-card" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          <div>
            <div className="panel-header">
              <span className="panel-title"><Zap size={16} color="var(--color-accent)" /> Risk Assessment</span>
              <StatusBadge status={currentDecision} type="decision" />
            </div>

            <div style={{ margin: '1rem 0' }}>
              <RiskGauge score={currentRisk} state={currentSafetyState} />
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.75rem', backgroundColor: 'var(--bg-secondary)', borderRadius: '6px', margin: '1rem 0' }}>
              <div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Safety State</div>
                <div style={{ marginTop: '0.2rem' }}><StatusBadge status={currentSafetyState} type="state" /></div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Enforced Policy</div>
                <div style={{ marginTop: '0.2rem' }}><StatusBadge status={currentDecision} type="decision" /></div>
              </div>
            </div>
          </div>

          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', backgroundColor: 'var(--bg-primary)', padding: '0.75rem', borderRadius: '4px', border: '1px solid var(--border-color)' }}>
            <strong>Reason:</strong> {latestEvent?.reason || latestEvent?.command || 'System operating within safe bounds.'}
          </div>
        </div>

        {/* Live Event Stream Panel */}
        <div className="panel-card">
          <div className="panel-header">
            <span className="panel-title"><Zap size={16} color="var(--color-safe)" /> Live Event Stream</span>
            <span className="mono" style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>WebSocket</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', maxHeight: '280px', overflowY: 'auto' }}>
            {liveStream.length === 0 ? (
              <div style={{ padding: '1.5rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                Waiting for WebSocket live traffic...
              </div>
            ) : (
              liveStream.map((msg, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '0.5rem 0.75rem',
                    backgroundColor: 'var(--bg-secondary)',
                    borderRadius: '4px',
                    borderLeft: `3px solid ${
                      msg.decision === 'BLOCK_CRITICAL' ? 'var(--color-catastrophic)' : msg.decision === 'BLOCK' ? 'var(--color-critical)' : 'var(--color-safe)'
                    }`,
                    fontSize: '0.8rem',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.2rem' }}>
                    <span style={{ fontWeight: 600 }}>{msg.device_id || 'PLC-01'}</span>
                    <span className="mono" style={{ color: 'var(--text-muted)' }}>
                      {msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString() : ''}
                    </span>
                  </div>
                  <div style={{ color: 'var(--text-secondary)' }}>
                    Command: <span className="mono" style={{ color: 'var(--color-accent)' }}>{msg.command || 'PACKET'}</span> (val: {msg.value ?? '-'})
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.25rem' }}>
                    <StatusBadge status={msg.safety_state} type="state" />
                    <StatusBadge status={msg.decision} type="decision" />
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Live Physics Telemetry Charts (2x2 grid) */}
      <PhysicsChartsPanel
        history={history}
        currentPressure={telemetry?.pressure ?? null}
        currentFlow={telemetry?.flow_rate ?? null}
        currentTemperature={telemetry?.temperature ?? null}
        currentRpm={telemetry?.pump_rpm ?? null}
      />

      {/* Recent Security Events Table */}
      <div className="panel-card">
        <div className="panel-header">
          <span className="panel-title"><ShieldAlert size={16} color="var(--color-accent)" /> Recent Security Events</span>
          <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Showing {events.length} latest</span>
        </div>
        <EventTable events={events} loading={loading} />
      </div>
    </div>
  );
};
