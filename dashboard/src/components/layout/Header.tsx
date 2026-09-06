import React, { useEffect, useState } from 'react';
import { ShieldAlert, Activity, Database, Cpu, Zap, Radio } from 'lucide-react';
import { SystemStatus } from '../../types';
import { wsService } from '../../services/websocket';

interface HeaderProps {
  systemStatus: SystemStatus | null;
}

export const Header: React.FC<HeaderProps> = ({ systemStatus }) => {
  const [wsStatus, setWsStatus] = useState<'LIVE' | 'DISCONNECTED' | 'CONNECTING'>('DISCONNECTED');
  const [timeStr, setTimeStr] = useState<string>('');

  useEffect(() => {
    const unsub = wsService.subscribeStatus(setWsStatus);
    const interval = setInterval(() => {
      setTimeStr(new Date().toLocaleTimeString());
    }, 1000);
    setTimeStr(new Date().toLocaleTimeString());

    return () => {
      unsub();
      clearInterval(interval);
    };
  }, []);

  return (
    <header
      style={{
        height: '60px',
        backgroundColor: 'var(--bg-secondary)',
        borderBottom: '1px solid var(--border-color)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 1.5rem',
        zIndex: 10,
      }}
    >
      {/* Brand Identity */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <div style={{ background: 'linear-gradient(135deg, #0284c7, #0369a1)', padding: '0.4rem', borderRadius: '6px', display: 'flex' }}>
          <ShieldAlert size={20} color="#ffffff" />
        </div>
        <div>
          <div style={{ fontSize: '1.1rem', fontWeight: 700, letterSpacing: '0.05em', color: '#ffffff' }}>
            VOLTGUARD <span style={{ fontSize: '0.75rem', fontWeight: 400, color: 'var(--text-secondary)' }}>ICS/SCADA CONSOLE</span>
          </div>
        </div>
      </div>

      {/* Subsystem Health Indicators */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem', fontSize: '0.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
          <Activity size={14} color={systemStatus?.backend === 'OPERATIONAL' ? 'var(--color-safe)' : 'var(--color-critical)'} />
          <span style={{ color: 'var(--text-muted)' }}>BACKEND:</span>
          <span style={{ fontWeight: 600, color: systemStatus?.backend === 'OPERATIONAL' ? 'var(--color-safe)' : 'var(--color-critical)' }}>
            {systemStatus?.backend || 'CHECKING'}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
          <Database size={14} color={systemStatus?.database === 'OPERATIONAL' ? 'var(--color-safe)' : 'var(--color-critical)'} />
          <span style={{ color: 'var(--text-muted)' }}>DB:</span>
          <span style={{ fontWeight: 600, color: systemStatus?.database === 'OPERATIONAL' ? 'var(--color-safe)' : 'var(--color-critical)' }}>
            {systemStatus?.database || 'CHECKING'}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
          <Zap size={14} color="var(--color-safe)" />
          <span style={{ color: 'var(--text-muted)' }}>PHYSICS:</span>
          <span style={{ fontWeight: 600, color: 'var(--color-safe)' }}>OPERATIONAL</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
          <Cpu size={14} color={systemStatus?.decision_engine === 'OPERATIONAL' ? 'var(--color-safe)' : 'var(--color-warning)'} />
          <span style={{ color: 'var(--text-muted)' }}>RUST DECISION:</span>
          <span style={{ fontWeight: 600, color: systemStatus?.decision_engine === 'OPERATIONAL' ? 'var(--color-safe)' : 'var(--color-warning)' }}>
            {systemStatus?.decision_engine || 'OPERATIONAL'}
          </span>
        </div>

        {/* WebSocket Live Indicator */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem',
            padding: '0.25rem 0.6rem',
            borderRadius: '4px',
            backgroundColor: wsStatus === 'LIVE' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
            border: `1px solid ${wsStatus === 'LIVE' ? 'var(--color-safe-border)' : 'var(--color-critical-border)'}`,
          }}
        >
          <Radio size={14} color={wsStatus === 'LIVE' ? 'var(--color-safe)' : 'var(--color-critical)'} />
          <span style={{ fontWeight: 700, fontFamily: 'var(--font-mono)', color: wsStatus === 'LIVE' ? 'var(--color-safe)' : 'var(--color-critical)' }}>
            {wsStatus === 'LIVE' ? '● LIVE WS' : '○ DISCONNECTED'}
          </span>
        </div>

        <div className="mono" style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', paddingLeft: '0.5rem', borderLeft: '1px solid var(--border-color)' }}>
          {timeStr}
        </div>
      </div>
    </header>
  );
};
