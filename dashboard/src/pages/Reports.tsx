import React, { useState, useEffect, useCallback } from 'react';
import {
  FileText, Download, Eye, RefreshCw, Filter, Plus,
  Shield, Activity, Terminal, AlertTriangle, BarChart2, Clock
} from 'lucide-react';
import { api } from '../services/api';
import { ReportMetadata, SecurityEvent } from '../types';
import { StatusBadge } from '../components/common/StatusBadge';

/* ─── Types ─────────────────────────────────────────────────────────────────── */
const REPORT_TYPES = [
  { key: 'SECURITY_EVENT', label: 'Security Event Report', icon: Shield, description: 'Detailed analysis of a specific security event.' },
  { key: 'PHYSICAL_SAFETY', label: 'Physical Safety Report', icon: Activity, description: 'Physical parameter violations and safety state review.' },
  { key: 'SIMULATION', label: 'Simulation Report', icon: Terminal, description: 'Summary of simulation runs and their outcomes.' },
  { key: 'INCIDENT_SUMMARY', label: 'Incident Summary', icon: AlertTriangle, description: 'Comprehensive incident report with timeline and traceability.' },
  { key: 'SYSTEM_ACTIVITY', label: 'System Activity Report', icon: BarChart2, description: 'Overall system activity, events, and alert counts.' },
];

/* ─── Small sub-components ─────────────────────────────────────────────────── */
function SectionHeader({ icon: Icon, title }: { icon: any; title: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem', paddingBottom: '0.5rem', borderBottom: '1px solid var(--border-color)' }}>
      <Icon size={15} color="var(--color-accent)" />
      <span style={{ fontSize: '0.8rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--text-secondary)' }}>{title}</span>
    </div>
  );
}

function DataRow({ label, value, mono = false }: { label: string; value?: string | number | null; mono?: boolean }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.4rem 0', borderBottom: '1px solid var(--border-color)' }}>
      <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{label}</span>
      <span className={mono ? 'mono' : ''} style={{ fontSize: '0.82rem', color: 'var(--text-primary)', fontWeight: 500 }}>
        {value ?? '—'}
      </span>
    </div>
  );
}

/* ─── Report Preview ────────────────────────────────────────────────────────── */
function ReportPreview({ report }: { report: { metadata: ReportMetadata; data: any } | null }) {
  if (!report) {
    return (
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: '0.9rem', flexDirection: 'column', gap: '0.5rem' }}>
        <FileText size={32} color="var(--text-muted)" />
        <span>Generate a report to see its preview.</span>
      </div>
    );
  }

  const { metadata, data } = report;
  const evt = data.event;
  const events = data.events || [];

  return (
    <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1rem' }}>

      {/* Header */}
      <div style={{
        background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
        border: '1px solid var(--border-color)',
        borderRadius: 'var(--radius-md)',
        padding: '1.25rem',
      }}>
        <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--color-accent)', letterSpacing: '0.1em', textTransform: 'uppercase' }}>VoltGuard</div>
        <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>Physics-Aware ICS/SCADA Security Report</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem' }}>
          <DataRow label="Report ID" value={metadata.report_id} mono />
          <DataRow label="Report Type" value={metadata.report_type.replace('_', ' ')} />
          <DataRow label="Generated" value={new Date(metadata.generated_at).toLocaleString()} />
          {metadata.primary_device && <DataRow label="Primary Device" value={metadata.primary_device} />}
          {metadata.severity && <DataRow label="Severity Filter" value={metadata.severity} />}
          <DataRow label="Status" value={metadata.status} />
        </div>
      </div>

      {/* Specific Event Report */}
      {evt && (
        <>
          <div className="panel-card">
            <SectionHeader icon={Terminal} title="Event Details" />
            <DataRow label="Event ID" value={`#${evt.id}`} mono />
            <DataRow label="Timestamp" value={new Date(evt.timestamp).toLocaleString()} />
            <DataRow label="Device" value={evt.device} />
            <DataRow label="Protocol" value={evt.protocol} />
            <DataRow label="Command" value={evt.command} />
            <DataRow label="Value" value={evt.command_value} />
          </div>

          <div className="panel-card">
            <SectionHeader icon={Activity} title="Physical Analysis" />
            <DataRow label="Predicted Pressure" value={evt.predicted_pressure != null ? `${Number(evt.predicted_pressure).toFixed(2)} bar` : undefined} />
            <DataRow label="Predicted Flow" value={evt.predicted_flow != null ? `${Number(evt.predicted_flow).toFixed(2)} m³/h` : undefined} />
            <DataRow label="Predicted Temperature" value={evt.predicted_temperature != null ? `${Number(evt.predicted_temperature).toFixed(2)} °C` : undefined} />
            <DataRow label="Risk Score" value={evt.risk_score != null ? Number(evt.risk_score).toFixed(1) : undefined} />
            <DataRow label="Safety State" value={evt.safety_state} />
          </div>

          <div className="panel-card">
            <SectionHeader icon={Shield} title="Security Decision" />
            <div style={{ marginBottom: '0.5rem' }}><StatusBadge status={evt.decision} type="decision" /></div>
            <DataRow label="Reason" value={evt.reason} />
            {evt.violations && <DataRow label="Violations" value={evt.violations} />}
            {evt.explanation && (
              <div style={{ marginTop: '0.75rem', padding: '0.6rem', backgroundColor: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', fontSize: '0.8rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                <strong style={{ color: 'var(--text-primary)' }}>Explanation: </strong>{evt.explanation}
              </div>
            )}
          </div>
        </>
      )}

      {/* Events Table Report */}
      {events.length > 0 && (
        <div className="panel-card">
          <SectionHeader icon={BarChart2} title={`Events Summary (${events.length} records)`} />
          <div style={{ overflowX: 'auto' }}>
            <table className="scada-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Timestamp</th>
                  <th>Device</th>
                  <th>Command / Value</th>
                  <th>Safety State</th>
                  <th>Decision</th>
                </tr>
              </thead>
              <tbody>
                {events.map((e: any) => (
                  <tr key={e.id}>
                    <td className="mono" style={{ fontSize: '0.75rem' }}>#{e.id}</td>
                    <td className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{new Date(e.timestamp).toLocaleString()}</td>
                    <td style={{ fontSize: '0.8rem' }}>{e.device}</td>
                    <td className="mono" style={{ fontSize: '0.78rem' }}>{e.command} {e.command_value}</td>
                    <td><StatusBadge status={e.safety_state} type="state" /></td>
                    <td><StatusBadge status={e.decision} type="decision" /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {!evt && events.length === 0 && (
        <div style={{ padding: '1rem', color: 'var(--text-muted)', fontSize: '0.85rem', textAlign: 'center' }}>
          No event data found for this report's filters.
        </div>
      )}
    </div>
  );
}

/* ─── Main Reports Page ─────────────────────────────────────────────────────── */
export const ReportsPage: React.FC = () => {
  const [reportType, setReportType] = useState('SECURITY_EVENT');
  const [filterDevice, setFilterDevice] = useState('');
  const [filterSeverity, setFilterSeverity] = useState('');
  const [filterEventId, setFilterEventId] = useState('');
  const [filterAlertId, setFilterAlertId] = useState('');

  const [generating, setGenerating] = useState(false);
  const [generateError, setGenerateError] = useState<string | null>(null);
  const [currentReport, setCurrentReport] = useState<{ metadata: ReportMetadata; data: any } | null>(null);

  const [history, setHistory] = useState<ReportMetadata[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  const [downloading, setDownloading] = useState<number | null>(null);

  const loadHistory = useCallback(async () => {
    setHistoryLoading(true);
    try {
      const list = await api.getReports();
      setHistory(list);
    } catch { }
    finally { setHistoryLoading(false); }
  }, []);

  useEffect(() => { loadHistory(); }, [loadHistory]);

  const generateReport = async () => {
    setGenerating(true);
    setGenerateError(null);
    try {
      const payload: any = { report_type: reportType };
      if (filterDevice.trim()) payload.primary_device = filterDevice.trim();
      if (filterSeverity) payload.severity = filterSeverity;
      if (filterEventId.trim()) payload.event_id = parseInt(filterEventId);
      if (filterAlertId.trim()) payload.alert_id = parseInt(filterAlertId);

      const result = await api.generateReport(payload);
      setCurrentReport(result);
      await loadHistory();
    } catch (err: any) {
      setGenerateError(err?.message || 'Report generation failed');
    } finally {
      setGenerating(false);
    }
  };

  const downloadPdf = async (reportDbId: number) => {
    setDownloading(reportDbId);
    try {
      const url = api.getReportDownloadUrl(reportDbId);
      const link = document.createElement('a');
      link.href = url;
      link.download = `voltguard-report-${reportDbId}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err: any) {
      alert('PDF download failed: ' + err.message);
    } finally {
      setDownloading(null);
    }
  };

  const selectedTypeMeta = REPORT_TYPES.find(r => r.key === reportType);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>

      {/* ── Title ── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)' }}>
            <FileText size={20} style={{ verticalAlign: 'middle', marginRight: '0.5rem' }} color="var(--color-accent)" />
            Report Center
          </h1>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
            Generate professional security and physics audit reports from real backend data.
          </p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: '1.25rem', alignItems: 'start' }}>

        {/* Left: Configuration */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>

          {/* Report Type Selector */}
          <div className="panel-card">
            <div className="panel-header">
              <span className="panel-title"><Filter size={15} color="var(--color-accent)" /> Report Type</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {REPORT_TYPES.map(rt => {
                const Icon = rt.icon;
                const active = reportType === rt.key;
                return (
                  <button
                    key={rt.key}
                    onClick={() => setReportType(rt.key)}
                    style={{
                      display: 'flex', gap: '0.75rem', alignItems: 'flex-start',
                      padding: '0.65rem 0.75rem',
                      border: `1px solid ${active ? 'var(--color-accent)' : 'var(--border-color)'}`,
                      borderRadius: 'var(--radius-sm)',
                      backgroundColor: active ? 'rgba(56,189,248,0.08)' : 'var(--bg-secondary)',
                      cursor: 'pointer',
                      textAlign: 'left',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    <Icon size={16} color={active ? 'var(--color-accent)' : 'var(--text-muted)'} style={{ marginTop: '2px', flexShrink: 0 }} />
                    <div>
                      <div style={{ fontSize: '0.82rem', fontWeight: 600, color: active ? 'var(--color-accent)' : 'var(--text-primary)' }}>{rt.label}</div>
                      <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>{rt.description}</div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Filters */}
          <div className="panel-card">
            <div className="panel-header">
              <span className="panel-title"><Filter size={15} color="var(--color-accent)" /> Filters</span>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div>
                <label style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.3rem' }}>Device ID (optional)</label>
                <input type="text" className="scada-input" placeholder="e.g. Pump-01" value={filterDevice} onChange={e => setFilterDevice(e.target.value)} />
              </div>
              <div>
                <label style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.3rem' }}>Safety State / Severity</label>
                <select className="scada-select" value={filterSeverity} onChange={e => setFilterSeverity(e.target.value)}>
                  <option value="">All Severities</option>
                  <option value="SAFE">SAFE</option>
                  <option value="WARNING">WARNING</option>
                  <option value="CRITICAL">CRITICAL</option>
                  <option value="CATASTROPHIC">CATASTROPHIC</option>
                </select>
              </div>
              <div>
                <label style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.3rem' }}>Event ID (optional)</label>
                <input type="number" className="scada-input mono" placeholder="e.g. 42" value={filterEventId} onChange={e => setFilterEventId(e.target.value)} />
              </div>
              <div>
                <label style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginBottom: '0.3rem' }}>Alert ID (optional)</label>
                <input type="number" className="scada-input mono" placeholder="e.g. 7" value={filterAlertId} onChange={e => setFilterAlertId(e.target.value)} />
              </div>
            </div>
          </div>

          {/* Generate Button */}
          {generateError && (
            <div style={{ backgroundColor: 'var(--color-critical-bg)', border: '1px solid var(--color-critical-border)', borderRadius: 'var(--radius-sm)', padding: '0.75rem', color: 'var(--color-critical)', fontSize: '0.82rem' }}>
              Report generation failed: {generateError}
            </div>
          )}

          <button
            className="scada-btn primary"
            onClick={generateReport}
            disabled={generating}
            style={{ justifyContent: 'center', padding: '0.85rem', fontSize: '0.9rem', fontWeight: 700 }}
          >
            <Plus size={16} />
            {generating ? 'Generating report...' : 'GENERATE REPORT'}
          </button>

          {currentReport && (
            <button
              className="scada-btn"
              onClick={() => downloadPdf(currentReport.metadata.id)}
              disabled={downloading === currentReport.metadata.id}
              style={{ justifyContent: 'center', padding: '0.75rem', border: '1px solid var(--color-accent)', color: 'var(--color-accent)' }}
            >
              <Download size={16} />
              {downloading === currentReport.metadata.id ? 'Preparing PDF...' : 'EXPORT PDF'}
            </button>
          )}
        </div>

        {/* Right: Preview + History */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>

          {/* Preview Panel */}
          <div className="panel-card" style={{ minHeight: '400px', display: 'flex', flexDirection: 'column' }}>
            <div className="panel-header">
              <span className="panel-title"><Eye size={15} color="var(--color-accent)" /> Report Preview</span>
              {currentReport && (
                <span className="mono" style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>{currentReport.metadata.report_id}</span>
              )}
            </div>
            <ReportPreview report={currentReport} />
          </div>

          {/* Report History */}
          <div className="panel-card">
            <div className="panel-header">
              <span className="panel-title"><Clock size={15} color="var(--color-accent)" /> Report History</span>
              <button className="scada-btn" style={{ padding: '0.25rem 0.6rem', fontSize: '0.72rem' }} onClick={loadHistory}>
                <RefreshCw size={12} /> Refresh
              </button>
            </div>

            {historyLoading && <div style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>Loading report history...</div>}

            {!historyLoading && history.length === 0 && (
              <div style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                No reports generated yet.
              </div>
            )}

            {!historyLoading && history.length > 0 && (
              <div style={{ overflowX: 'auto' }}>
                <table className="scada-table">
                  <thead>
                    <tr>
                      <th>Report ID</th>
                      <th>Type</th>
                      <th>Generated</th>
                      <th>Device</th>
                      <th>Severity</th>
                      <th>Status</th>
                      <th>Export</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.map(r => (
                      <tr key={r.id}>
                        <td className="mono" style={{ fontSize: '0.75rem', color: 'var(--color-accent)' }}>{r.report_id}</td>
                        <td style={{ fontSize: '0.78rem' }}>{r.report_type.replace('_', ' ')}</td>
                        <td className="mono" style={{ fontSize: '0.73rem', color: 'var(--text-muted)' }}>{new Date(r.generated_at).toLocaleString()}</td>
                        <td style={{ fontSize: '0.8rem' }}>{r.primary_device || '—'}</td>
                        <td>{r.severity ? <StatusBadge status={r.severity} type="state" /> : <span style={{ color: 'var(--text-muted)' }}>—</span>}</td>
                        <td>
                          <span style={{
                            fontSize: '0.72rem', fontWeight: 700, fontFamily: 'var(--font-mono)',
                            color: r.status === 'READY' ? 'var(--color-safe)' : 'var(--text-muted)'
                          }}>{r.status}</span>
                        </td>
                        <td>
                          <button
                            className="scada-btn"
                            style={{ padding: '0.2rem 0.5rem', fontSize: '0.7rem' }}
                            onClick={() => downloadPdf(r.id)}
                            disabled={downloading === r.id}
                          >
                            <Download size={11} />
                            {downloading === r.id ? '...' : 'PDF'}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
