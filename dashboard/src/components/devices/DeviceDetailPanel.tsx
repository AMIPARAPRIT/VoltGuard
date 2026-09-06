import React, { useEffect, useState } from 'react';
import { Server, Activity, ShieldCheck, Zap, Database, Clock, RefreshCw } from 'lucide-react';
import { DetailPanel } from '../common/DetailPanel';
import { Device, Telemetry } from '../../types';
import { api } from '../../services/api';
import { StatusBadge } from '../common/StatusBadge';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface DeviceDetailPanelProps {
  device: Device | null;
  onClose: () => void;
}

export const DeviceDetailPanel: React.FC<DeviceDetailPanelProps> = ({ device, onClose }) => {
  const [telemetry, setTelemetry] = useState<Telemetry[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (device) {
      setLoading(true);
      api.getDeviceTelemetry(device.device_id)
        .then(res => setTelemetry(res.items.reverse())) // Reverse to put oldest first for chart
        .catch(console.error)
        .finally(() => setLoading(false));
    } else {
      setTelemetry([]);
    }
  }, [device]);

  if (!device) return null;

  return (
    <DetailPanel 
      isOpen={!!device} 
      onClose={onClose} 
      title={<><Server size={20} color="var(--color-accent)" /> Device Inspector: {device.device_id}</>}
      width="700px"
    >
      {/* Identity & Status */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
         <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '1.25rem', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
            <h4 style={{ margin: '0 0 1rem 0', color: 'var(--text-primary)', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Database size={16} /> Asset Profile
            </h4>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', fontSize: '0.85rem' }}>
               <div><span style={{ color: 'var(--text-muted)' }}>IP Address:</span> <br/><span className="mono">{device.ip_address || 'Unknown'}</span></div>
               <div><span style={{ color: 'var(--text-muted)' }}>Protocol:</span> <br/><span className="mono">{device.protocol || 'Unknown'}</span></div>
               <div><span style={{ color: 'var(--text-muted)' }}>Status:</span> <br/><span style={{ color: device.connection_status === 'ONLINE' ? 'var(--color-safe)' : 'var(--text-muted)' }}>{device.connection_status}</span></div>
               <div><span style={{ color: 'var(--text-muted)' }}>Last Seen:</span> <br/><span>{device.last_seen ? new Date(device.last_seen).toLocaleTimeString() : 'N/A'}</span></div>
            </div>
         </div>

         <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '1.25rem', borderRadius: '6px', border: '1px solid var(--border-color)' }}>
            <h4 style={{ margin: '0 0 1rem 0', color: 'var(--text-primary)', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <ShieldCheck size={16} /> Latest Security State
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
               <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                 <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Physical Safety</span>
                 <StatusBadge status={device.last_safety_state || 'UNKNOWN'} type="state" />
               </div>
               <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                 <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Latest Decision</span>
                 <StatusBadge status={device.last_decision || 'UNKNOWN'} type="decision" />
               </div>
               <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                 <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Threat Score</span>
                 <span className="mono" style={{ fontSize: '0.9rem', color: (device.last_risk_score ?? 0) > 50 ? '#f87171' : 'var(--color-safe)' }}>
                    {device.last_risk_score?.toFixed(1) || '0.0'}
                 </span>
               </div>
            </div>
         </div>
      </div>

      {/* Snapshot Telemetry */}
      <div>
        <h4 style={{ margin: '0 0 0.75rem 0', color: 'var(--text-primary)', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Activity size={16} color="var(--color-accent)"/> Live Physics Telemetry
        </h4>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.5rem' }}>
           <MetricBox label="Pressure" value={device.last_pressure} unit="bar" />
           <MetricBox label="Flow Rate" value={device.last_flow_rate} unit="m³/h" />
           <MetricBox label="Temperature" value={device.last_temperature} unit="°C" />
           <MetricBox label="Pump RPM" value={device.last_pump_rpm} unit="rpm" />
        </div>
      </div>

      {/* Telemetry Chart */}
      <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '1rem', borderRadius: '6px', border: '1px solid var(--border-color)', height: '250px', display: 'flex', flexDirection: 'column' }}>
        <h4 style={{ margin: '0 0 1rem 0', color: 'var(--text-primary)', fontSize: '0.85rem' }}>Pressure & Flow Trend (Last 60 readings)</h4>
        {loading ? (
          <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}><RefreshCw size={16} className="spin" /></div>
        ) : telemetry.length > 0 ? (
          <div style={{ flex: 1 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={telemetry} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorPressure" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--color-accent)" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="var(--color-accent)" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorFlow" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" vertical={false} />
                <XAxis dataKey="timestamp" tick={false} axisLine={false} />
                <YAxis tick={{ fontSize: 10, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: 'var(--bg-primary)', border: '1px solid var(--border-color)', borderRadius: '4px' }}
                  itemStyle={{ fontSize: '0.8rem' }}
                  labelStyle={{ display: 'none' }}
                />
                <Area type="monotone" dataKey="pressure" stroke="var(--color-accent)" fillOpacity={1} fill="url(#colorPressure)" name="Pressure (bar)" />
                <Area type="monotone" dataKey="flow_rate" stroke="#10b981" fillOpacity={1} fill="url(#colorFlow)" name="Flow (m³/h)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        ) : (
           <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>No telemetry available.</div>
        )}
      </div>

    </DetailPanel>
  );
};

const MetricBox = ({ label, value, unit }: { label: string, value: number | undefined, unit: string }) => (
  <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '0.75rem', borderRadius: '4px', border: '1px solid var(--border-color)', textAlign: 'center' }}>
     <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.25rem', textTransform: 'uppercase' }}>{label}</div>
     <div className="mono" style={{ fontSize: '1.1rem', color: 'var(--text-primary)', fontWeight: 600 }}>
       {value !== undefined ? value.toFixed(1) : '--'}<span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginLeft: '2px' }}>{unit}</span>
     </div>
  </div>
);
