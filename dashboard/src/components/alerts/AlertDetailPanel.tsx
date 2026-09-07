import React, { useEffect, useState } from 'react';
import { AlertTriangle, Info, CheckCircle2, ShieldAlert, Cpu, Clock, Zap, Target } from 'lucide-react';
import { DetailPanel } from '../common/DetailPanel';
import { Alert, SecurityEvent } from '../../types';
import { api } from '../../services/api';
import { toast } from '../../services/toast';

interface AlertDetailPanelProps {
  alert: Alert | null;
  onClose: () => void;
  onAlertUpdated: (alert: Alert) => void;
  onNavigateToEvent?: (eventId: number) => void;
}

export const AlertDetailPanel: React.FC<AlertDetailPanelProps> = ({ alert, onClose, onAlertUpdated, onNavigateToEvent }) => {
  const [eventDetails, setEventDetails] = useState<SecurityEvent | null>(null);
  const [loadingEvent, setLoadingEvent] = useState(false);

  useEffect(() => {
    if (alert?.event_id) {
      setLoadingEvent(true);
      api.getEventDetail(alert.event_id)
        .then(setEventDetails)
        .catch((err) => {
          console.error("Failed to load event details", err);
        })
        .finally(() => setLoadingEvent(false));
    } else {
      setEventDetails(null);
    }
  }, [alert]);

  if (!alert) return null;

  const isCrit = alert.severity === 'CATASTROPHIC' || alert.severity === 'CRITICAL';
  const isWarn = alert.severity === 'WARNING';

  const icon = isCrit ? <AlertTriangle size={24} color={alert.severity === 'CATASTROPHIC' ? 'var(--color-catastrophic)' : '#f87171'} /> 
               : isWarn ? <AlertTriangle size={24} color="var(--color-warning)" /> 
               : <Info size={24} color="var(--color-accent)" />;

  const handleAcknowledge = async () => {
    try {
      const updated = await api.acknowledgeAlert(alert.id);
      onAlertUpdated(updated);
      toast.success('Alert Acknowledged', `Alert #${alert.id} has been acknowledged.`);
    } catch (e: any) {
      toast.error('Failed to acknowledge alert', e.message);
    }
  };

  const handleResolve = async () => {
    try {
      const updated = await api.resolveAlert(alert.id);
      onAlertUpdated(updated);
      toast.success('Alert Resolved', `Alert #${alert.id} has been marked as resolved.`);
      onClose(); // Auto close on resolve
    } catch (e: any) {
      toast.error('Failed to resolve alert', e.message);
    }
  };

  return (
    <DetailPanel 
      isOpen={!!alert} 
      onClose={onClose} 
      title={<><ShieldAlert size={20} color="var(--color-accent)" /> Alert Investigation</>}
      width="600px"
    >
      {/* Header Summary */}
      <div style={{
        padding: '1.25rem',
        backgroundColor: 'var(--bg-secondary)',
        borderRadius: '6px',
        borderLeft: `4px solid ${alert.severity === 'CATASTROPHIC' ? 'var(--color-catastrophic)' : isCrit ? '#f87171' : isWarn ? 'var(--color-warning)' : 'var(--color-accent)'}`,
        display: 'flex',
        gap: '1rem',
        alignItems: 'flex-start'
      }}>
        {icon}
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
             <span
                className="mono"
                style={{
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  padding: '0.15rem 0.4rem',
                  borderRadius: '3px',
                  backgroundColor: alert.severity === 'CATASTROPHIC' ? 'rgba(255,0,0,0.2)' : isCrit ? 'var(--color-catastrophic-bg)' : isWarn ? 'var(--color-warning-bg)' : 'rgba(56, 189, 248, 0.1)',
                  color: alert.severity === 'CATASTROPHIC' ? 'var(--color-catastrophic)' : isCrit ? '#f87171' : isWarn ? 'var(--color-warning)' : 'var(--color-accent)',
                }}
              >
                {alert.severity}
              </span>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>ID: #{alert.id}</span>
          </div>
          <h3 style={{ margin: '0 0 0.5rem 0', color: 'var(--text-primary)', fontSize: '1.1rem' }}>{alert.title}</h3>
          <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: 1.5 }}>
            {alert.message}
          </p>
        </div>
      </div>

      {/* Lifecycle Actions */}
      <div style={{ display: 'flex', gap: '1rem', padding: '1rem', backgroundColor: 'var(--bg-secondary)', borderRadius: '6px' }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Current Status</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600, color: alert.status === 'RESOLVED' ? 'var(--color-safe)' : alert.status === 'ACKNOWLEDGED' ? 'var(--color-accent)' : 'var(--color-warning)' }}>
            {alert.status === 'RESOLVED' && <CheckCircle2 size={16} />}
            {alert.status === 'ACTIVE' && <AlertTriangle size={16} />}
            {alert.status}
          </div>
        </div>
        
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {alert.status === 'ACTIVE' && (
            <button className="scada-btn" onClick={handleAcknowledge}>Acknowledge</button>
          )}
          {alert.status !== 'RESOLVED' && (
            <button className="scada-btn" style={{ backgroundColor: 'var(--color-safe)' }} onClick={handleResolve}>Resolve</button>
          )}
        </div>
      </div>

      {/* Identity & Timing */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
         <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '1rem', borderRadius: '6px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: '0.5rem' }}><Cpu size={14}/> Target Device</div>
            <div className="mono" style={{ fontSize: '0.95rem', color: 'var(--text-primary)' }}>{alert.device || 'Unknown'}</div>
         </div>
         <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '1rem', borderRadius: '6px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-muted)', fontSize: '0.8rem', marginBottom: '0.5rem' }}><Clock size={14}/> Detection Time</div>
            <div className="mono" style={{ fontSize: '0.9rem', color: 'var(--text-primary)' }}>{new Date(alert.timestamp).toLocaleString()}</div>
         </div>
      </div>

      {/* Linked Event Details */}
      {alert.event_id && (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
             <h4 style={{ margin: 0, color: 'var(--text-primary)', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}><Zap size={16} color="var(--color-accent)"/> Underlying Security Event</h4>
             {onNavigateToEvent && (
                <button 
                  onClick={() => onNavigateToEvent(alert.event_id!)}
                  style={{ background: 'none', border: 'none', color: 'var(--color-accent)', cursor: 'pointer', fontSize: '0.8rem' }}
                >
                  View Full Event →
                </button>
             )}
          </div>
          
          <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '1rem', borderRadius: '6px' }}>
            {loadingEvent ? (
              <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Loading event details...</div>
            ) : eventDetails ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.85rem' }}>
                  <div><span style={{ color: 'var(--text-muted)' }}>Command:</span> <span className="mono">{eventDetails.command || 'UNKNOWN'}</span></div>
                  <div><span style={{ color: 'var(--text-muted)' }}>Value:</span> <span className="mono">{eventDetails.command_value ?? 'N/A'}</span></div>
                  <div><span style={{ color: 'var(--text-muted)' }}>Protocol:</span> <span className="mono">{eventDetails.protocol}</span></div>
                  <div><span style={{ color: 'var(--text-muted)' }}>Source:</span> <span className="mono">{eventDetails.source_ip || 'N/A'}</span></div>
                </div>

                {eventDetails.violations && (
                  <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '1rem' }}>
                    <div style={{ fontSize: '0.85rem', color: '#f87171', fontWeight: 600, marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                       <Target size={14}/> Physics Violations
                    </div>
                    <ul style={{ margin: 0, paddingLeft: '1.2rem', color: 'var(--text-secondary)', fontSize: '0.85rem', display: 'flex', flexDirection: 'column', gap: '0.3rem' }}>
                       {(() => {
                         try {
                           const viols = JSON.parse(eventDetails.violations);
                           if (Array.isArray(viols) && viols.length > 0) {
                             return viols.map((v, i) => <li key={i}>{v.description || `${v.parameter} exceeded limit`}</li>);
                           }
                           return <li>No explicit violations recorded</li>;
                         } catch(e) {
                           return <li>{eventDetails.violations}</li>;
                         }
                       })()}
                    </ul>
                  </div>
                )}
                
                {eventDetails.explanation && (
                  <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '0.75rem' }}>
                    <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>Physics Context</div>
                    <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontStyle: 'italic' }}>
                      "{eventDetails.explanation}"
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Event details unavailable.</div>
            )}
          </div>
        </div>
      )}

      {/* Timestamps */}
      <div style={{ marginTop: 'auto', paddingTop: '1rem', borderTop: '1px solid var(--border-color)', fontSize: '0.75rem', color: 'var(--text-muted)', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
        <div>Created: {new Date(alert.timestamp).toLocaleString()}</div>
        {alert.acknowledged_at && <div>Ack'd: {new Date(alert.acknowledged_at).toLocaleString()}</div>}
        {alert.resolved_at && <div>Resolved: {new Date(alert.resolved_at).toLocaleString()}</div>}
      </div>
    </DetailPanel>
  );
};
