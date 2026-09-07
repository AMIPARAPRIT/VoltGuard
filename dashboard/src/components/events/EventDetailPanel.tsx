import React from 'react';
import { Zap, Shield, Target, Cpu, Clock, Activity, ArrowRightLeft } from 'lucide-react';
import { DetailPanel } from '../common/DetailPanel';
import { SecurityEvent } from '../../types';
import { StatusBadge } from '../common/StatusBadge';

interface EventDetailPanelProps {
  event: SecurityEvent | null;
  onClose: () => void;
  onNavigateToAlert?: (alertId: number) => void;
}

export const EventDetailPanel: React.FC<EventDetailPanelProps> = ({ event, onClose, onNavigateToAlert }) => {
  if (!event) return null;

  return (
    <DetailPanel 
      isOpen={!!event} 
      onClose={onClose} 
      title={<><Zap size={20} color="var(--color-accent)" /> Security Event Details</>}
      width="650px"
    >
      {/* Top summary cards */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '1rem', borderRadius: '6px', borderLeft: '3px solid var(--color-accent)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <Shield size={14}/> Security Decision
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <StatusBadge status={event.decision || 'UNKNOWN'} type="decision" />
            <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
               Risk: {event.risk_score?.toFixed(1) ?? 'N/A'}
            </span>
          </div>
          <div style={{ marginTop: '0.75rem', fontSize: '0.85rem', color: 'var(--text-primary)' }}>
             {event.reason || 'No decision reason provided.'}
          </div>
        </div>

        <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '1rem', borderRadius: '6px', borderLeft: '3px solid var(--color-safe)' }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
            <Activity size={14}/> Physics State
          </div>
          <StatusBadge status={event.safety_state || 'UNKNOWN'} type="state" />
          
          <div style={{ marginTop: '0.75rem', fontSize: '0.85rem', color: 'var(--text-primary)', fontStyle: 'italic' }}>
             "{event.explanation || 'Normal operational parameters.'}"
          </div>
        </div>
      </div>

      {/* Network & Command */}
      <div>
        <h4 style={{ margin: '0 0 0.75rem 0', color: 'var(--text-primary)', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <ArrowRightLeft size={16} /> Network & Command Context
        </h4>
        <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '1rem', borderRadius: '6px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
           <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>Source IP</div>
              <div className="mono" style={{ fontSize: '0.9rem' }}>{event.source_ip || 'N/A'}</div>
           </div>
           <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>Target Device</div>
              <div className="mono" style={{ fontSize: '0.9rem', color: 'var(--color-accent)' }}>{event.device || 'N/A'} ({event.destination_ip || 'N/A'})</div>
           </div>
           <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>Protocol</div>
              <div className="mono" style={{ fontSize: '0.9rem' }}>{event.protocol}</div>
           </div>
           <div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>Command Payload</div>
              <div className="mono" style={{ fontSize: '0.9rem' }}>{event.command} = {event.command_value}</div>
              {event.function_code !== undefined && (
                <div className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>FC: {event.function_code} | Reg: {event.register}</div>
              )}
           </div>
        </div>
      </div>

      {/* Physics Violations */}
      {event.violations && (
        <div>
          <h4 style={{ margin: '0 0 0.75rem 0', color: '#f87171', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Target size={16} /> Detected Physics Violations
          </h4>
          <div style={{ backgroundColor: 'var(--color-catastrophic-bg)', padding: '1rem', borderRadius: '6px', border: '1px solid rgba(255,0,0,0.2)' }}>
             <ul style={{ margin: 0, paddingLeft: '1.2rem', color: 'var(--text-primary)', fontSize: '0.85rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                 {(() => {
                   try {
                     const viols = JSON.parse(event.violations);
                     if (Array.isArray(viols) && viols.length > 0) {
                       return viols.map((v, i) => (
                         <li key={i}>
                           <strong>{v.parameter}</strong>: {v.value?.toFixed(2)} (Limit: {v.limit?.toFixed(2)}) — <span style={{ color: 'var(--text-secondary)' }}>{v.description}</span>
                         </li>
                       ));
                     }
                     return <li>No explicit violations recorded</li>;
                   } catch(e) {
                     return <li>{event.violations}</li>;
                   }
                 })()}
              </ul>
          </div>
        </div>
      )}

      {/* Timestamps & Linked Alert */}
      <div style={{ marginTop: 'auto', paddingTop: '1rem', borderTop: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
         <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}><Clock size={12}/> {new Date(event.timestamp).toLocaleString()}</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}><Cpu size={12}/> Latency: {event.latency_ms?.toFixed(2)}ms</div>
         </div>
         
         {event.alert_id && onNavigateToAlert && (
            <button 
              onClick={() => onNavigateToAlert(event.alert_id!)}
              className="scada-btn"
              style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem' }}
            >
              View Associated Alert
            </button>
         )}
      </div>

    </DetailPanel>
  );
};
