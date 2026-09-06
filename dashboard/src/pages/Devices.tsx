import React from 'react';
import { Server, Activity, ShieldCheck, Zap } from 'lucide-react';
import { StatusBadge } from '../components/common/StatusBadge';

interface DeviceItem {
  id: string;
  name: string;
  type: string;
  ip: string;
  protocol: string;
  status: 'ONLINE' | 'OFFLINE';
  rpm?: number;
  pressure?: number;
  safetyState: 'SAFE' | 'WARNING' | 'CRITICAL' | 'CATASTROPHIC';
}

export const DevicesPage: React.FC = () => {
  const devices: DeviceItem[] = [
    { id: 'PLC-01', name: 'Master Programmable Logic Controller', type: 'PLC', ip: '192.168.1.10', protocol: 'Modbus/TCP', status: 'ONLINE', rpm: 1200, pressure: 8.5, safetyState: 'SAFE' },
    { id: 'Pump-01', name: 'Main High-Pressure Feed Pump', type: 'PUMP', ip: '192.168.1.20', protocol: 'Modbus/TCP', status: 'ONLINE', rpm: 1500, pressure: 8.5, safetyState: 'SAFE' },
    { id: 'Pump-02', name: 'Auxiliary Water Transfer Pump', type: 'PUMP', ip: '192.168.1.21', protocol: 'Modbus/TCP', status: 'ONLINE', rpm: 1200, pressure: 6.2, safetyState: 'SAFE' },
    { id: 'Valve-01', name: 'Proportional Flow Control Valve', type: 'VALVE', ip: '192.168.1.30', protocol: 'Modbus/TCP', status: 'ONLINE', pressure: 8.5, safetyState: 'SAFE' },
    { id: 'Pressure-Sensor-01', name: 'Pipeline Transducer Array', type: 'SENSOR', ip: '192.168.1.40', protocol: 'Modbus/TCP', status: 'ONLINE', pressure: 8.5, safetyState: 'SAFE' },
    { id: 'RTU-01', name: 'Substation Remote Terminal Unit', type: 'RTU', ip: '192.168.1.50', protocol: 'DNP3', status: 'ONLINE', safetyState: 'SAFE' },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      <div className="panel-card">
        <div className="panel-header">
          <span className="panel-title"><Server size={18} color="var(--color-accent)" /> OT / ICS Asset Inventory</span>
          <span className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>6 Registered Assets</span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
          {devices.map((dev) => (
            <div
              key={dev.id}
              style={{
                padding: '1.25rem',
                backgroundColor: 'var(--bg-secondary)',
                borderRadius: '6px',
                border: '1px solid var(--border-color)',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                gap: '1rem',
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                  <span style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-primary)' }}>{dev.id}</span>
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.75rem', color: 'var(--color-safe)', fontWeight: 600 }}>
                    <Activity size={14} /> {dev.status}
                  </span>
                </div>

                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
                  {dev.name}
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.75rem', backgroundColor: 'var(--bg-primary)', padding: '0.6rem', borderRadius: '4px' }}>
                  <div><span style={{ color: 'var(--text-muted)' }}>IP:</span> <span className="mono">{dev.ip}</span></div>
                  <div><span style={{ color: 'var(--text-muted)' }}>Protocol:</span> <span className="mono">{dev.protocol}</span></div>
                  <div><span style={{ color: 'var(--text-muted)' }}>Type:</span> <span className="mono">{dev.type}</span></div>
                  <div><span style={{ color: 'var(--text-muted)' }}>Health:</span> <span style={{ color: 'var(--color-safe)' }}>NORMAL</span></div>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '0.75rem', borderTop: '1px solid var(--border-color)' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Safety Classification</span>
                <StatusBadge status={dev.safetyState} type="state" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
