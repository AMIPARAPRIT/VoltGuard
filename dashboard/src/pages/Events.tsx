import React, { useEffect, useState } from 'react';
import { ShieldAlert, Search, Filter, RefreshCw } from 'lucide-react';
import { SecurityEvent, SafetyState, Decision } from '../types';
import { api } from '../services/api';
import { EventTable } from '../components/tables/EventTable';

export const EventsPage: React.FC = () => {
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [stateFilter, setStateFilter] = useState<string>('ALL');
  const [decisionFilter, setDecisionFilter] = useState<string>('ALL');
  const [protocolFilter, setProtocolFilter] = useState<string>('ALL');

  const loadEvents = async () => {
    setLoading(true);
    try {
      const data = await api.getEvents(100, 0);
      setEvents(data);
    } catch (err) {
      console.error('Failed to load security events:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEvents();
  }, []);

  const filteredEvents = events.filter((evt) => {
    const matchesSearch =
      searchTerm === '' ||
      (evt.device && evt.device.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (evt.command && evt.command.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (evt.source_ip && evt.source_ip.includes(searchTerm)) ||
      (evt.protocol && evt.protocol.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesState = stateFilter === 'ALL' || (evt.safety_state && evt.safety_state.toUpperCase() === stateFilter);
    const matchesDecision = decisionFilter === 'ALL' || (evt.decision && evt.decision.toUpperCase() === decisionFilter);
    const matchesProtocol = protocolFilter === 'ALL' || (evt.protocol && evt.protocol.toLowerCase().includes(protocolFilter.toLowerCase()));

    return matchesSearch && matchesState && matchesDecision && matchesProtocol;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      <div className="panel-card">
        <div className="panel-header" style={{ marginBottom: '1rem' }}>
          <span className="panel-title"><ShieldAlert size={18} color="var(--color-accent)" /> Historical Security Events Log</span>
          <button className="scada-btn" onClick={loadEvents} disabled={loading}>
            <RefreshCw size={14} className={loading ? 'spin' : ''} /> Refresh
          </button>
        </div>

        {/* Filters & Search Controls */}
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr 1fr', gap: '1rem', marginBottom: '1.25rem' }}>
          <div style={{ position: 'relative' }}>
            <Search size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '10px', top: '10px' }} />
            <input
              type="text"
              className="scada-input"
              style={{ paddingLeft: '2.2rem' }}
              placeholder="Search by device, command, or IP address..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          <div>
            <select className="scada-select" value={stateFilter} onChange={(e) => setStateFilter(e.target.value)}>
              <option value="ALL">All Safety States</option>
              <option value="SAFE">SAFE</option>
              <option value="WARNING">WARNING</option>
              <option value="CRITICAL">CRITICAL</option>
              <option value="CATASTROPHIC">CATASTROPHIC</option>
            </select>
          </div>

          <div>
            <select className="scada-select" value={decisionFilter} onChange={(e) => setDecisionFilter(e.target.value)}>
              <option value="ALL">All Decisions</option>
              <option value="ALLOW">ALLOW</option>
              <option value="MONITOR">MONITOR</option>
              <option value="BLOCK">BLOCK</option>
              <option value="BLOCK_CRITICAL">BLOCK_CRITICAL</option>
            </select>
          </div>

          <div>
            <select className="scada-select" value={protocolFilter} onChange={(e) => setProtocolFilter(e.target.value)}>
              <option value="ALL">All Protocols</option>
              <option value="modbus">Modbus/TCP</option>
              <option value="dnp3">DNP3</option>
            </select>
          </div>
        </div>

        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
          Showing {filteredEvents.length} of {events.length} security events
        </div>

        <EventTable events={filteredEvents} loading={loading} />
      </div>
    </div>
  );
};
