import { SystemStatus, SecurityEvent, Alert, Telemetry, PipelineResponse } from '../types';

const API_BASE = '/api';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
  return response.json();
}

export const api = {
  async getSystemStatus(): Promise<SystemStatus> {
    return fetchJson<SystemStatus>(`${API_BASE}/system/status`);
  },

  async getEvents(limit: number = 50, offset: number = 0): Promise<SecurityEvent[]> {
    return fetchJson<SecurityEvent[]>(`${API_BASE}/events/?limit=${limit}&offset=${offset}`);
  },

  async getAlerts(limit: number = 50, offset: number = 0): Promise<Alert[]> {
    return fetchJson<Alert[]>(`${API_BASE}/alerts/?limit=${limit}&offset=${offset}`);
  },

  async acknowledgeAlert(alertId: number): Promise<Alert> {
    return fetchJson<Alert>(`${API_BASE}/alerts/${alertId}/acknowledge`, {
      method: 'PATCH',
    });
  },

  async getTelemetry(limit: number = 50, offset: number = 0): Promise<Telemetry[]> {
    return fetchJson<Telemetry[]>(`${API_BASE}/telemetry/?limit=${limit}&offset=${offset}`);
  },

  async sendSimulationCommand(payload: {
    hex_payload?: string;
    protocol?: string;
    source_ip?: string;
    destination_ip?: string;
    command?: string;
    value?: number;
    device_id?: string;
    current_state?: Record<string, number>;
  }): Promise<PipelineResponse> {
    return fetchJson<PipelineResponse>(`${API_BASE}/simulation/command`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
  },

  async startSimulationStream(mode: string = 'mixed', rate_fps: number = 1.0): Promise<{ status: string; running: boolean; mode: string; rate_fps: number; processed_count: number }> {
    return fetchJson(`${API_BASE}/simulation/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode, rate_fps }),
    });
  },

  async stopSimulationStream(): Promise<{ status: string; running: boolean }> {
    return fetchJson(`${API_BASE}/simulation/stop`, {
      method: 'POST',
    });
  },

  async getSimulationStatus(): Promise<{ running: boolean; mode: string; rate_fps: number; processed_count: number }> {
    return fetchJson(`${API_BASE}/simulation/status`);
  },
};
