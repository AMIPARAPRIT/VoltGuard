import React, { useState, useEffect, useCallback } from 'react';
import {
  PlaySquare, Send, Zap, ShieldAlert, Play, Square,
  Terminal, Activity, Shield, Cpu, History, ChevronRight,
  AlertTriangle, CheckCircle, Info, ExternalLink, ChevronDown
} from 'lucide-react';
import { api } from '../services/api';
import { PipelineResponse, SimulationHistoryItem } from '../types';
import { StatusBadge } from '../components/common/StatusBadge';
import { useNavigate } from 'react-router-dom';

/* ─── Scenario definitions (inputs only — backend decides outputs) ─────────── */
const SCENARIOS = {
  NORMAL: {
    label: 'Normal Operation',
    description: 'Typical operational parameters. Expected: SAFE / ALLOW',
    color: 'var(--color-safe)',
    command: 'SET_RPM',
    value: 1500,
    valve: null as number | null,
    protocol: 'modbus',
    device_id: 'Pump-01',
  },
  WARNING: {
    label: 'Warning — Boundary Shift',
    description: 'Near-threshold parameters. Expected: WARNING / MONITOR',
    color: 'var(--color-warning)',
    command: 'SET_RPM',
    value: 3200,
    valve: 88,
    protocol: 'modbus',
    device_id: 'Pump-01',
  },
  CRITICAL: {
    label: 'Critical — High Load',
    description: 'Exceeds recommended operating limits.',
    color: 'var(--color-critical)',
    command: 'SET_RPM',
    value: 4200,
    valve: 95,
    protocol: 'modbus',
    device_id: 'Pump-01',
  },
  ATTACK: {
    label: 'Simulated Attack',
    description: '50 000 RPM command via raw Modbus payload.',
    color: '#f87171',
    hex_payload: '00010000000601069C41C350',
    command: 'SET_RPM',
    value: 50000,
    valve: 100,
    protocol: 'modbus',
    device_id: 'Pump-01',
  },
  CUSTOM: {
    label: 'Custom Command',
    description: 'Manually specify parameters.',
    color: 'var(--color-accent)',
    command: 'SET_RPM',
    value: 1000,
    valve: null as number | null,
    protocol: 'modbus',
    device_id: 'Pump-01',
  },
} as const;

type ScenarioKey = keyof typeof SCENARIOS;

/* ─── Helper components ─────────────────────────────────────────────────────── */
function MetricBox({ label, value, unit = '', color }: { label: string; value?: string | number | null; unit?: string; color?: string }) {
  return (
    <div style={{
      backgroundColor: 'var(--bg-secondary)',
      border: '1px solid var(--border-color)',
      borderRadius: 'var(--radius-sm)',
      padding: '0.75rem',
    }}>
      <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.35rem' }}>{label}</div>
      <div className="mono" style={{ fontSize: '1.05rem', fontWeight: 700, color: color || 'var(--text-primary)' }}>
        {value == null ? '—' : `${value}${unit ? ' ' + unit : ''}`}
      </div>
    </div>
  );
}

function SectionHeader({ icon: Icon, title }: { icon: any; title: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem', paddingBottom: '0.5rem', borderBottom: '1px solid var(--border-color)' }}>
      <Icon size={15} color="var(--color-accent)" />
      <span style={{ fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-secondary)' }}>{title}</span>
    </div>
  );
}

function LimitRow({ label, actual, limit, unit = '' }: { label: string; actual?: number | null; limit?: number | null; unit?: string }) {
  if (actual == null) return null;
  const exceeded = limit != null && actual > limit;
  return (
    <div style={{
      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
      padding: '0.4rem 0.6rem',
      backgroundColor: exceeded ? 'rgba(239,68,68,0.08)' : 'transparent',
      borderRadius: 'var(--radius-sm)',
      border: exceeded ? '1px solid rgba(239,68,68,0.25)' : '1px solid transparent',
      marginBottom: '0.3rem',
    }}>
      <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{label}</span>
      <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
        <span className="mono" style={{ fontSize: '0.85rem', color: exceeded ? 'var(--color-critical)' : 'var(--color-safe)' }}>
          {actual.toFixed(1)}{unit ? ' ' + unit : ''}
        </span>
        {limit != null && (
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>/ {limit.toFixed(1)}</span>
        )}
        {exceeded && <span style={{ fontSize: '0.65rem', fontWeight: 700, color: 'var(--color-critical)', fontFamily: 'var(--font-mono)' }}>EXCEEDED</span>}
      </div>
    </div>
  );
}

function AttackChain({ result }: { result: PipelineResponse }) {
  const physics = result.physics_result;
  const decision = result.decision_result;
  const violations = physics?.violations;
  if (!physics || !decision) return null;
  if (decision.decision === 'ALLOW') return null;

  const steps = [
    { label: 'COMMAND', value: `${result.normalized_command?.command} = ${result.normalized_command?.value} ${result.normalized_command?.unit || ''}` },
    { label: 'PHYSICAL IMPACT', value: `Pressure ${physics.predicted_pressure?.toFixed(1)} bar, RPM ${physics.pump_rpm?.toFixed(0)}, Stress ${(physics.system_stress * 100).toFixed(0)}%` },
    ...(violations && violations.length > 0 ? [{ label: 'SAFETY VIOLATIONS', value: violations.map(v => v.parameter).join(', ') }] : []),
    { label: 'SAFETY STATE', value: physics.safety_state },
    { label: 'RUST DECISION', value: decision.decision },
  ];

  return (
    <div style={{ marginTop: '1rem' }}>
      <SectionHeader icon={AlertTriangle} title="Attack Chain" />
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0' }}>
        {steps.map((step, i) => (
          <div key={i}>
            <div style={{
              display: 'flex', gap: '0.75rem', alignItems: 'flex-start',
              backgroundColor: 'var(--bg-secondary)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-sm)',
              padding: '0.6rem 0.75rem',
            }}>
              <span style={{ fontSize: '0.65rem', fontWeight: 700, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', paddingTop: '1px', minWidth: '110px' }}>{step.label}</span>
              <span className="mono" style={{ fontSize: '0.85rem', color: step.label === 'RUST DECISION' ? 'var(--color-critical)' : 'var(--text-primary)', fontWeight: step.label === 'RUST DECISION' ? 700 : 400 }}>{step.value}</span>
            </div>
            {i < steps.length - 1 && (
              <div style={{ display: 'flex', justifyContent: 'center', padding: '2px 0' }}>
                <ChevronDown size={14} color="var(--color-critical)" />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

/* ─── Main page ─────────────────────────────────────────────────────────────── */
export const SimulationPage: React.FC = () => {
  const navigate = useNavigate();
  const [selectedScenario, setSelectedScenario] = useState<ScenarioKey>('NORMAL');
  const [customCommand, setCustomCommand] = useState('SET_RPM');
  const [customValue, setCustomValue] = useState<number>(1500);
  const [customValve, setCustomValve] = useState<number>(60);
  const [customProtocol, setCustomProtocol] = useState('modbus');
  const [customDevice, setCustomDevice] = useState('Pump-01');
  const [customSrcIp, setCustomSrcIp] = useState('192.168.1.20');

  const [executing, setExecuting] = useState(false);
  const [lastResult, setLastResult] = useState<PipelineResponse | null>(null);
  const [lastError, setLastError] = useState<string | null>(null);

  const [streamRunning, setStreamRunning] = useState(false);
  const [streamMode, setStreamMode] = useState('mixed');

  const [history, setHistory] = useState<SimulationHistoryItem[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [selectedHistoryId, setSelectedHistoryId] = useState<number | null>(null);
  const [historyDetail, setHistoryDetail] = useState<SimulationHistoryItem | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const loadHistory = useCallback(async () => {
    setHistoryLoading(true);
    try {
      const res = await api.getSimulationHistory();
      setHistory(res.items || []);
    } catch {
      // silently fail
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  useEffect(() => { loadHistory(); }, [loadHistory]);

  const runSimulation = async () => {
    setExecuting(true);
    setLastError(null);
    setLastResult(null);
    const sc = SCENARIOS[selectedScenario];

    try {
      let payload: any = { scenario: selectedScenario, protocol: sc.protocol };

      if (selectedScenario === 'ATTACK') {
        payload.hex_payload = (sc as any).hex_payload;
        payload.source_ip = '10.100.2.45';
        payload.destination_ip = '192.168.1.50';
        payload.command = sc.command;
        payload.value = sc.value;
        payload.device_id = sc.device_id;
      } else if (selectedScenario === 'CUSTOM') {
        payload.command = customCommand;
        payload.value = customValue;
        payload.device_id = customDevice;
        payload.protocol = customProtocol;
        payload.source_ip = customSrcIp;
        payload.destination_ip = '192.168.1.50';
        if (customCommand === 'SET_VALVE') payload.value = customValve;
      } else {
        payload.command = sc.command;
        payload.value = sc.value;
        payload.device_id = sc.device_id;
        payload.source_ip = '192.168.1.20';
        payload.destination_ip = '192.168.1.50';
        // If the scenario has a valve override, send a second command? 
        // For now, send RPM only (backend handles physics from RPM)
      }

      const res = await api.sendSimulationCommand(payload);
      setLastResult(res);
      await loadHistory();
    } catch (err: any) {
      setLastError(err?.message || 'Simulation failed');
    } finally {
      setExecuting(false);
    }
  };

  const loadDetail = async (id: number) => {
    if (selectedHistoryId === id) {
      setSelectedHistoryId(null);
      setHistoryDetail(null);
      return;
    }
    setSelectedHistoryId(id);
    setDetailLoading(true);
    try {
      const d = await api.getSimulationDetail(id);
      setHistoryDetail(d);
    } catch { }
    finally { setDetailLoading(false); }
  };

  const handleStartStream = async () => {
    try { const r = await api.startSimulationStream(streamMode, 1.0); if (r.running || r.status === 'STARTED') setStreamRunning(true); } catch { }
  };
  const handleStopStream = async () => {
    try { const r = await api.stopSimulationStream(); if (!r.running) setStreamRunning(false); } catch { }
  };

  const sc = SCENARIOS[selectedScenario];
  const physics = lastResult?.physics_result;
  const decision = lastResult?.decision_result;
  const norm = lastResult?.normalized_command;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>

      {/* ── Scenario Selector ── */}
      <div className="panel-card">
        <div className="panel-header">
          <span className="panel-title"><Zap size={16} color="var(--color-accent)" /> Simulation Center</span>
          <span className="mono" style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>Input → Parser → Physics → Rust Decision Engine</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '0.75rem', marginBottom: '1.25rem' }}>
          {(Object.keys(SCENARIOS) as ScenarioKey[]).map(key => {
            const s = SCENARIOS[key];
            const active = selectedScenario === key;
            return (
              <button
                key={key}
                onClick={() => setSelectedScenario(key)}
                style={{
                  border: `2px solid ${active ? s.color : 'var(--border-color)'}`,
                  backgroundColor: active ? `${s.color}15` : 'var(--bg-secondary)',
                  borderRadius: 'var(--radius-md)',
                  padding: '0.75rem',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all 0.15s ease',
                }}
              >
                <div style={{ fontSize: '0.7rem', fontWeight: 800, color: s.color, fontFamily: 'var(--font-mono)', letterSpacing: '0.06em' }}>{key}</div>
                <div style={{ fontSize: '0.73rem', color: 'var(--text-secondary)', marginTop: '0.3rem', lineHeight: 1.3 }}>{s.label}</div>
                {key !== 'CUSTOM' && (
                  <div className="mono" style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '0.4rem' }}>
                    {(s as any).hex_payload ? 'Raw Hex Payload' : `RPM: ${s.value}`}
                    {(s as any).valve != null ? ` | Valve: ${(s as any).valve}%` : ''}
                  </div>
                )}
              </button>
            );
          })}
        </div>

        {/* Custom form */}
        {selectedScenario === 'CUSTOM' && (
          <div style={{ backgroundColor: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)', padding: '1rem', marginBottom: '1rem', border: '1px solid var(--border-color)' }}>
            <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--color-accent)', marginBottom: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Custom Parameters</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem' }}>
              <div>
                <label style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.3rem' }}>Command</label>
                <select className="scada-select" value={customCommand} onChange={e => setCustomCommand(e.target.value)}>
                  <option value="SET_RPM">SET_RPM</option>
                  <option value="SET_VALVE">SET_VALVE</option>
                  <option value="SET_PRESSURE">SET_PRESSURE</option>
                </select>
              </div>
              <div>
                <label style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.3rem' }}>
                  {customCommand === 'SET_VALVE' ? 'Valve %  (0–100)' : 'RPM  (100–60000)'}
                </label>
                <input
                  type="number"
                  className="scada-input mono"
                  value={customCommand === 'SET_VALVE' ? customValve : customValue}
                  min={customCommand === 'SET_VALVE' ? 0 : 100}
                  max={customCommand === 'SET_VALVE' ? 100 : 60000}
                  onChange={e => customCommand === 'SET_VALVE' ? setCustomValve(Number(e.target.value)) : setCustomValue(Number(e.target.value))}
                />
              </div>
              <div>
                <label style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.3rem' }}>Protocol</label>
                <select className="scada-select" value={customProtocol} onChange={e => setCustomProtocol(e.target.value)}>
                  <option value="modbus">Modbus/TCP</option>
                  <option value="dnp3">DNP3</option>
                </select>
              </div>
              <div>
                <label style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.3rem' }}>Device</label>
                <select className="scada-select" value={customDevice} onChange={e => setCustomDevice(e.target.value)}>
                  <option value="Pump-01">Pump-01</option>
                  <option value="PLC-01">PLC-01</option>
                  <option value="Valve-01">Valve-01</option>
                </select>
              </div>
              <div>
                <label style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.3rem' }}>Source IP</label>
                <input type="text" className="scada-input mono" value={customSrcIp} onChange={e => setCustomSrcIp(e.target.value)} />
              </div>
            </div>
          </div>
        )}

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <button
            className="scada-btn primary"
            onClick={runSimulation}
            disabled={executing}
            style={{ padding: '0.75rem 2rem', fontSize: '0.9rem', fontWeight: 700 }}
          >
            <Play size={16} />
            {executing ? 'Running simulation...' : 'RUN SIMULATION'}
          </button>
          <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>{sc.description}</div>
        </div>
      </div>

      {/* ── Error state ── */}
      {lastError && (
        <div style={{ backgroundColor: 'var(--color-critical-bg)', border: '1px solid var(--color-critical-border)', borderRadius: 'var(--radius-md)', padding: '1rem', color: 'var(--color-critical)' }}>
          <strong>Simulation failed:</strong> {lastError}
        </div>
      )}

      {/* ── Result Panel ── */}
      {lastResult && (
        <div className="panel-card">
          <div className="panel-header">
            <span className="panel-title"><Terminal size={16} color="var(--color-accent)" /> Simulation Result</span>
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              <StatusBadge status={decision?.safety_state} type="state" />
              <StatusBadge status={decision?.decision} type="decision" />
              {lastResult.event_id && (
                <button className="scada-btn" style={{ padding: '0.25rem 0.6rem', fontSize: '0.72rem' }} onClick={() => navigate(`/events`)}>
                  <ExternalLink size={12} /> Event #{lastResult.event_id}
                </button>
              )}
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem' }}>

            {/* Command block */}
            <div>
              <SectionHeader icon={Terminal} title="Command" />
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                <MetricBox label="Device" value={norm?.device_id} />
                <MetricBox label="Protocol" value={norm?.protocol?.toUpperCase()} />
                <MetricBox label="Command" value={norm?.command} />
                <MetricBox label="Value" value={norm ? `${norm.value} ${norm.unit}` : undefined} />
                <MetricBox label="Function Code" value={norm?.function_code} />
                <MetricBox label="Register" value={norm?.register} />
              </div>
            </div>

            {/* Physical Impact */}
            <div>
              <SectionHeader icon={Activity} title="Physical Impact" />
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                <LimitRow label="Pump RPM" actual={physics?.pump_rpm} limit={physics?.rpm_limit} unit="RPM" />
                <LimitRow label="Valve Position" actual={physics?.valve_position} unit="%" />
                <LimitRow label="Predicted Pressure" actual={physics?.predicted_pressure} limit={physics?.pressure_limit} unit="bar" />
                <LimitRow label="Predicted Flow" actual={physics?.predicted_flow} limit={physics?.flow_limit} unit="m³/h" />
                <LimitRow label="Predicted Temp" actual={physics?.predicted_temperature} limit={physics?.temperature_limit} unit="°C" />
                <LimitRow label="System Stress" actual={physics ? physics.system_stress * 100 : undefined} limit={physics ? (physics.stress_limit ?? 1.0) * 100 : undefined} unit="%" />
              </div>
            </div>

            {/* Safety */}
            <div>
              <SectionHeader icon={Shield} title="Safety" />
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginBottom: '0.75rem' }}>
                <MetricBox
                  label="Risk Score"
                  value={physics?.risk_score != null ? physics.risk_score.toFixed(1) : undefined}
                  color={physics?.risk_score != null ? (physics.risk_score > 75 ? 'var(--color-critical)' : physics.risk_score > 40 ? 'var(--color-warning)' : 'var(--color-safe)') : undefined}
                />
                <MetricBox label="Safety State" value={physics?.safety_state} />
              </div>
              {physics?.violations && physics.violations.length > 0 && (
                <div style={{ marginBottom: '0.5rem' }}>
                  {physics.violations.map((v, i) => (
                    <div key={i} style={{
                      backgroundColor: 'var(--color-critical-bg)', border: '1px solid var(--color-critical-border)',
                      borderRadius: 'var(--radius-sm)', padding: '0.4rem 0.6rem', marginBottom: '0.3rem',
                      fontSize: '0.78rem', color: 'var(--color-critical)'
                    }}>
                      <strong>{v.parameter}:</strong> {v.value?.toFixed(2)} / {v.limit?.toFixed(2)} — {v.description}
                    </div>
                  ))}
                </div>
              )}
              {physics?.explanation && (
                <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>{physics.explanation}</div>
              )}
            </div>

            {/* Security Decision */}
            <div>
              <SectionHeader icon={Cpu} title="Security Decision" />
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginBottom: '0.75rem' }}>
                <MetricBox
                  label="Decision"
                  value={decision?.decision}
                  color={decision?.decision === 'ALLOW' ? 'var(--color-safe)' : decision?.decision === 'BLOCK_CRITICAL' ? '#f87171' : 'var(--color-warning)'}
                />
                <MetricBox
                  label="Decision Latency"
                  value={decision?.decision_latency_us != null ? `${decision.decision_latency_us} µs` : undefined}
                  color="var(--color-accent)"
                />
                <MetricBox
                  label="Total Processing"
                  value={lastResult.timing_ms?.total_processing_ms != null ? `${lastResult.timing_ms.total_processing_ms} ms` : undefined}
                  color="var(--color-accent)"
                />
                <MetricBox label="Risk Score" value={decision?.risk_score?.toFixed(1)} />
              </div>
              {decision?.reason && (
                <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.5, backgroundColor: 'var(--bg-secondary)', padding: '0.5rem', borderRadius: 'var(--radius-sm)' }}>
                  <strong style={{ color: 'var(--text-primary)' }}>Reason: </strong>{decision.reason}
                </div>
              )}
            </div>
          </div>

          {/* Attack chain (only for non-ALLOW decisions) */}
          {decision && decision.decision !== 'ALLOW' && <AttackChain result={lastResult} />}
        </div>
      )}

      {/* ── Background stream + History row ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: '1.25rem' }}>

        {/* Background stream */}
        <div className="panel-card">
          <div className="panel-header">
            <span className="panel-title"><PlaySquare size={15} color="var(--color-safe)" /> Traffic Stream</span>
            <span className="mono" style={{ fontSize: '0.7rem', color: streamRunning ? 'var(--color-safe)' : 'var(--text-muted)' }}>
              {streamRunning ? '● RUNNING' : '○ STOPPED'}
            </span>
          </div>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
            Continuous synthetic OT traffic through the full pipeline at 1 pkt/s.
          </p>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.3rem' }}>Mode</label>
            <select className="scada-select" value={streamMode} onChange={e => setStreamMode(e.target.value)} disabled={streamRunning}>
              <option value="mixed">Mixed</option>
              <option value="normal">Normal</option>
              <option value="suspicious">Suspicious</option>
              <option value="attack">Attack</option>
            </select>
          </div>
          {!streamRunning
            ? <button className="scada-btn primary" onClick={handleStartStream} style={{ width: '100%', justifyContent: 'center' }}><Play size={14} /> Start Stream</button>
            : <button className="scada-btn danger" onClick={handleStopStream} style={{ width: '100%', justifyContent: 'center' }}><Square size={14} /> Stop Stream</button>
          }
        </div>

        {/* Simulation History */}
        <div className="panel-card">
          <div className="panel-header">
            <span className="panel-title"><History size={15} color="var(--color-accent)" /> Simulation History</span>
            <button className="scada-btn" style={{ padding: '0.25rem 0.6rem', fontSize: '0.72rem' }} onClick={loadHistory}>Refresh</button>
          </div>

          {historyLoading && <div style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>Loading simulation history...</div>}

          {!historyLoading && history.length === 0 && (
            <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              No simulations yet. Run your first simulation above.
            </div>
          )}

          {!historyLoading && history.length > 0 && (
            <div style={{ overflowY: 'auto', maxHeight: '320px' }}>
              <table className="scada-table">
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Scenario</th>
                    <th>Device</th>
                    <th>Command / Value</th>
                    <th>Risk</th>
                    <th>State</th>
                    <th>Decision</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {history.map(h => (
                    <React.Fragment key={h.id}>
                      <tr
                        style={{ cursor: 'pointer', backgroundColor: selectedHistoryId === h.id ? 'var(--bg-card-hover)' : undefined }}
                        onClick={() => loadDetail(h.id)}
                      >
                        <td className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                          {new Date(h.timestamp).toLocaleTimeString()}
                        </td>
                        <td>
                          <span style={{ fontSize: '0.72rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: SCENARIOS[h.scenario as ScenarioKey]?.color || 'var(--text-secondary)' }}>
                            {h.scenario}
                          </span>
                        </td>
                        <td style={{ fontSize: '0.8rem' }}>{h.device_id}</td>
                        <td className="mono" style={{ fontSize: '0.78rem' }}>{h.command} = {h.command_value}</td>
                        <td className="mono" style={{ fontSize: '0.8rem', color: h.risk_score > 75 ? 'var(--color-critical)' : h.risk_score > 40 ? 'var(--color-warning)' : 'var(--color-safe)' }}>
                          {h.risk_score?.toFixed(0)}
                        </td>
                        <td><StatusBadge status={h.safety_state} type="state" /></td>
                        <td><StatusBadge status={h.decision} type="decision" /></td>
                        <td>
                          <ChevronRight size={14} color="var(--text-muted)" style={{ transform: selectedHistoryId === h.id ? 'rotate(90deg)' : 'none', transition: 'transform 0.2s' }} />
                        </td>
                      </tr>

                      {/* Inline detail */}
                      {selectedHistoryId === h.id && (
                        <tr>
                          <td colSpan={8} style={{ padding: 0, backgroundColor: 'var(--bg-secondary)' }}>
                            {detailLoading ? (
                              <div style={{ padding: '1rem', color: 'var(--text-muted)', fontSize: '0.82rem' }}>Loading detail...</div>
                            ) : historyDetail && (
                              <div style={{ padding: '1rem' }}>
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.5rem', marginBottom: '0.75rem' }}>
                                  <MetricBox label="Protocol" value={historyDetail.protocol?.toUpperCase()} />
                                  <MetricBox label="Risk Score" value={historyDetail.risk_score?.toFixed(1)} />
                                  <MetricBox label="Safety State" value={historyDetail.safety_state} />
                                  <MetricBox label="Decision" value={historyDetail.decision} />
                                </div>
                                <div style={{ display: 'flex', gap: '0.5rem' }}>
                                  {historyDetail.event_id && (
                                    <button className="scada-btn" style={{ fontSize: '0.72rem', padding: '0.25rem 0.6rem' }} onClick={() => navigate('/events')}>
                                      <ExternalLink size={11} /> Event #{historyDetail.event_id}
                                    </button>
                                  )}
                                  {historyDetail.alert_id && (
                                    <button className="scada-btn" style={{ fontSize: '0.72rem', padding: '0.25rem 0.6rem' }} onClick={() => navigate('/alerts')}>
                                      <ExternalLink size={11} /> Alert #{historyDetail.alert_id}
                                    </button>
                                  )}
                                  {historyDetail.raw_result?.physics_result && (
                                    <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', alignSelf: 'center' }}>
                                      Pressure: {historyDetail.raw_result.physics_result.predicted_pressure?.toFixed(1)} bar |
                                      Flow: {historyDetail.raw_result.physics_result.predicted_flow?.toFixed(1)} m³/h |
                                      Temp: {historyDetail.raw_result.physics_result.predicted_temperature?.toFixed(1)}°C
                                    </span>
                                  )}
                                </div>
                              </div>
                            )}
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
