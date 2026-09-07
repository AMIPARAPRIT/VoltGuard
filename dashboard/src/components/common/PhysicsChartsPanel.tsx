import React from 'react';
import { Activity } from 'lucide-react';
import { TelemetryChart, TelemetryDataPoint } from './TelemetryChart';

export interface TelemetryHistory {
  pressure: TelemetryDataPoint[];
  flow: TelemetryDataPoint[];
  temperature: TelemetryDataPoint[];
  rpm: TelemetryDataPoint[];
}

interface PhysicsChartsPanelProps {
  history: TelemetryHistory;
  currentPressure: number | null;
  currentFlow: number | null;
  currentTemperature: number | null;
  currentRpm: number | null;
}

export const PhysicsChartsPanel: React.FC<PhysicsChartsPanelProps> = ({
  history,
  currentPressure,
  currentFlow,
  currentTemperature,
  currentRpm,
}) => {
  return (
    <div className="panel-card">
      <div className="panel-header">
        <span className="panel-title">
          <Activity size={16} color="var(--color-safe)" /> Live Physics Telemetry — Time Series
        </span>
        <span className="mono" style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
          Rolling 60-event window · WebSocket driven
        </span>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(2, 1fr)',
          gap: '1rem',
        }}
      >
        {/* Pipeline Pressure */}
        <TelemetryChart
          data={history.pressure}
          label="Pipeline Pressure"
          unit="bar"
          color="var(--color-accent)"
          limit={80}
          limitLabel="MAX 80 bar"
          domain={[0, 'auto']}
          currentValue={currentPressure}
        />

        {/* Fluid Flow Rate */}
        <TelemetryChart
          data={history.flow}
          label="Fluid Flow Rate"
          unit="L/min"
          color="var(--color-safe)"
          limit={500}
          limitLabel="MAX 500 L/min"
          domain={[0, 'auto']}
          currentValue={currentFlow}
        />

        {/* Fluid Temperature */}
        <TelemetryChart
          data={history.temperature}
          label="Fluid Temperature"
          unit="°C"
          color="#f59e0b"
          limit={120}
          limitLabel="MAX 120 °C"
          domain={[0, 'auto']}
          currentValue={currentTemperature}
        />

        {/* Pump RPM */}
        <TelemetryChart
          data={history.rpm}
          label="Pump RPM"
          unit="RPM"
          color="#a78bfa"
          limit={3600}
          limitLabel="MAX 3600 RPM"
          domain={[0, 'auto']}
          currentValue={currentRpm}
        />
      </div>
    </div>
  );
};
