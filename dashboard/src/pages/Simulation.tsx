import React, { useState } from 'react';
import { PlaySquare, Send, Zap, ShieldAlert, Play, Square } from 'lucide-react';
import { api } from '../services/api';
import { PipelineResponse } from '../types';
import { StatusBadge } from '../components/common/StatusBadge';

export const SimulationPage: React.FC = () => {
  const [commandName, setCommandName] = useState<string>('SET_RPM');
  const [commandValue, setCommandValue] = useState<number>(1500);
  const [protocol, setProtocol] = useState<string>('modbus');
  const [srcIp, setSrcIp] = useState<string>('192.168.1.20');
  const [executing, setExecuting] = useState<boolean>(false);
  const [lastResponse, setLastResponse] = useState<PipelineResponse | null>(null);

  const [streamRunning, setStreamRunning] = useState<boolean>(false);
  const [streamMode, setStreamMode] = useState<string>('mixed');

  const executeCommand = async (cmdOverride?: string, valOverride?: number) => {
    const cmd = cmdOverride || commandName;
    const val = valOverride !== undefined ? valOverride : commandValue;

    setExecuting(true);
    try {
      const res = await api.sendSimulationCommand({
        command: cmd,
        value: val,
        protocol: protocol,
        source_ip: srcIp,
        destination_ip: '192.168.1.50',
      });
      setLastResponse(res);
    } catch (err) {
      console.error('Failed to execute simulation command:', err);
    } finally {
      setExecuting(false);
    }
  };

  const executeAttackPayload = async () => {
    setExecuting(true);
    try {
      const res = await api.sendSimulationCommand({
        hex_payload: '00010000000601069C41C350',
        protocol: 'modbus',
        source_ip: '10.100.2.45',
        destination_ip: '192.168.1.50',
      });
      setLastResponse(res);
    } catch (err) {
      console.error('Failed to execute attack payload:', err);
    } finally {
      setExecuting(false);
    }
  };

  const handleStartStream = async () => {
    try {
      const res = await api.startSimulationStream(streamMode, 1.0);
      if (res.running || res.status === 'STARTED') {
        setStreamRunning(true);
      }
    } catch (err) {
      console.error('Failed to start stream:', err);
    }
  };

  const handleStopStream = async () => {
    try {
      const res = await api.stopSimulationStream();
      if (!res.running) {
        setStreamRunning(false);
      }
    } catch (err) {
      console.error('Failed to stop stream:', err);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      {/* Quick Scenario Preset Buttons */}
      <div className="panel-card">
        <div className="panel-header">
          <span className="panel-title"><Zap size={18} color="var(--color-accent)" /> Quick Attack & Operation Presets</span>
          <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Executes through full Parser → Physics → Rust pipeline</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1rem' }}>
          <button className="scada-btn" onClick={() => executeCommand('SET_RPM', 1500)} disabled={executing} style={{ padding: '0.85rem' }}>
            <Zap size={16} color="var(--color-safe)" />
            <div>
              <div style={{ fontWeight: 700, color: 'var(--color-safe)' }}>Normal Setpoint</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>SET_RPM = 1500 (SAFE → ALLOW)</div>
            </div>
          </button>

          <button className="scada-btn" onClick={() => executeCommand('SET_RPM', 3000)} disabled={executing} style={{ padding: '0.85rem' }}>
            <Zap size={16} color="var(--color-warning)" />
            <div>
              <div style={{ fontWeight: 700, color: 'var(--color-warning)' }}>Boundary Shift</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>SET_RPM = 3000 (WARNING → MONITOR)</div>
            </div>
          </button>

          <button className="scada-btn" onClick={() => executeCommand('SET_RPM', 3500)} disabled={executing} style={{ padding: '0.85rem' }}>
            <ShieldAlert size={16} color="var(--color-critical)" />
            <div>
              <div style={{ fontWeight: 700, color: 'var(--color-critical)' }}>Near-Threshold Breach</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>SET_RPM = 3500 (CRITICAL → BLOCK)</div>
            </div>
          </button>

          <button className="scada-btn danger" onClick={executeAttackPayload} disabled={executing} style={{ padding: '0.85rem' }}>
            <ShieldAlert size={16} color="#ffffff" />
            <div>
              <div style={{ fontWeight: 700 }}>50000 RPM Attack</div>
              <div style={{ fontSize: '0.7rem', opacity: 0.9 }}>Raw Hex Modbus CATASTROPHIC</div>
            </div>
          </button>
        </div>
      </div>

      {/* Grid: Manual Injection Form & Background Stream Control */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem' }}>
        {/* Manual Command Form */}
        <div className="panel-card">
          <div className="panel-header">
            <span className="panel-title"><Send size={16} color="var(--color-accent)" /> Manual Command Injection</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: '0.35rem' }}>
                Command Name
              </label>
              <select className="scada-select" value={commandName} onChange={(e) => setCommandName(e.target.value)}>
                <option value="SET_RPM">SET_RPM (Pump RPM Setpoint)</option>
                <option value="SET_VALVE">SET_VALVE (Valve Opening %)</option>
                <option value="SET_PRESSURE">SET_PRESSURE (Pipeline Pressure Setpoint)</option>
              </select>
            </div>

            <div>
              <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: '0.35rem' }}>
                Command Value
              </label>
              <input
                type="number"
                className="scada-input mono"
                value={commandValue}
                onChange={(e) => setCommandValue(Number(e.target.value))}
              />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: '0.35rem' }}>
                  Protocol
                </label>
                <select className="scada-select" value={protocol} onChange={(e) => setProtocol(e.target.value)}>
                  <option value="modbus">Modbus/TCP</option>
                  <option value="dnp3">DNP3</option>
                </select>
              </div>

              <div>
                <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: '0.35rem' }}>
                  Source IP
                </label>
                <input
                  type="text"
                  className="scada-input mono"
                  value={srcIp}
                  onChange={(e) => setSrcIp(e.target.value)}
                />
              </div>
            </div>

            <button className="scada-btn primary" onClick={() => executeCommand()} disabled={executing} style={{ justifyContent: 'center', marginTop: '0.5rem' }}>
              <Send size={16} /> Submit Command to Pipeline
            </button>
          </div>
        </div>

        {/* Background Stream Control */}
        <div className="panel-card">
          <div className="panel-header">
            <span className="panel-title"><PlaySquare size={16} color="var(--color-safe)" /> Background Traffic Stream</span>
            <span className="mono" style={{ fontSize: '0.75rem', color: streamRunning ? 'var(--color-safe)' : 'var(--text-muted)' }}>
              {streamRunning ? '● RUNNING (1 FPS)' : '○ STOPPED'}
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Continuously streams synthetic industrial OT traffic payloads (Normal, Suspicious, Attack, Mixed) through the pipeline at 1 packet per second.
            </p>

            <div>
              <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: '0.35rem' }}>
                Traffic Scenario Mode
              </label>
              <select className="scada-select" value={streamMode} onChange={(e) => setStreamMode(e.target.value)} disabled={streamRunning}>
                <option value="mixed">Mixed (Normal + Suspicious + Attack)</option>
                <option value="normal">Normal Operational Stream</option>
                <option value="suspicious">Suspicious Boundary Operations</option>
                <option value="attack">Malicious Exploit Stream</option>
              </select>
            </div>

            <div style={{ display: 'flex', gap: '1rem' }}>
              {!streamRunning ? (
                <button className="scada-btn primary" onClick={handleStartStream} style={{ flex: 1, justifyContent: 'center' }}>
                  <Play size={16} /> Start Traffic Stream
                </button>
              ) : (
                <button className="scada-btn danger" onClick={handleStopStream} style={{ flex: 1, justifyContent: 'center' }}>
                  <Square size={16} /> Stop Traffic Stream
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Execution Output Panel */}
      {lastResponse && (
        <div className="panel-card">
          <div className="panel-header">
            <span className="panel-title"><Zap size={16} color="var(--color-accent)" /> Pipeline Execution Output</span>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <StatusBadge status={lastResponse.decision_result?.safety_state} type="state" />
              <StatusBadge status={lastResponse.decision_result?.decision} type="decision" />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '0.75rem', borderRadius: '4px' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Target Parameter</div>
              <div className="mono" style={{ fontSize: '1.1rem', fontWeight: 700 }}>
                {lastResponse.normalized_command?.command} = {lastResponse.normalized_command?.value} {lastResponse.normalized_command?.unit}
              </div>
            </div>

            <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '0.75rem', borderRadius: '4px' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Predicted Pressure</div>
              <div className="mono" style={{ fontSize: '1.1rem', fontWeight: 700, color: (lastResponse.physics_result?.predicted_pressure ?? 0) > 80 ? 'var(--color-critical)' : 'var(--color-safe)' }}>
                {lastResponse.physics_result?.predicted_pressure?.toFixed(1) ?? 'N/A'} bar
              </div>
            </div>

            <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '0.75rem', borderRadius: '4px' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Total Processing Time</div>
              <div className="mono" style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--color-accent)' }}>
                {lastResponse.timing_ms?.total_processing_ms} ms
              </div>
            </div>
          </div>

          <div className="mono" style={{ backgroundColor: 'var(--bg-primary)', padding: '1rem', borderRadius: '4px', border: '1px solid var(--border-color)', fontSize: '0.75rem', color: 'var(--text-secondary)', overflowX: 'auto' }}>
            {JSON.stringify(lastResponse, null, 2)}
          </div>
        </div>
      )}
    </div>
  );
};
