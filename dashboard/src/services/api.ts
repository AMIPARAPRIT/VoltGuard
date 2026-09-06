import { SystemStatus, SecurityEvent, Alert, Telemetry, PipelineResponse, AlertSummary, PaginatedResponse, Device, SimulationHistoryItem, ReportMetadata } from '../types';

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

  async getEvents(
    page: number = 1,
    pageSize: number = 50,
    filters?: { decision?: string; safety_state?: string; device?: string; protocol?: string; search?: string }
  ): Promise<PaginatedResponse<SecurityEvent>> {
    const params = new URLSearchParams({ page: page.toString(), page_size: pageSize.toString() });
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, value);
      });
    }
    return fetchJson<PaginatedResponse<SecurityEvent>>(`${API_BASE}/events/?${params.toString()}`);
  },

  async getEventDetail(eventId: number): Promise<SecurityEvent> {
    return fetchJson<SecurityEvent>(`${API_BASE}/events/${eventId}`);
  },

  async getAlertSummary(): Promise<AlertSummary> {
    return fetchJson<AlertSummary>(`${API_BASE}/alerts/summary`);
  },

  async getAlerts(
    page: number = 1,
    pageSize: number = 50,
    filters?: { severity?: string; status?: string; device?: string; search?: string }
  ): Promise<PaginatedResponse<Alert>> {
    const params = new URLSearchParams({ page: page.toString(), page_size: pageSize.toString() });
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value && value !== 'ALL') params.append(key, value);
      });
    }
    return fetchJson<PaginatedResponse<Alert>>(`${API_BASE}/alerts/?${params.toString()}`);
  },

  async acknowledgeAlert(alertId: number): Promise<Alert> {
    return fetchJson<Alert>(`${API_BASE}/alerts/${alertId}/acknowledge`, {
      method: 'PATCH',
    });
  },

  async resolveAlert(alertId: number): Promise<Alert> {
    return fetchJson<Alert>(`${API_BASE}/alerts/${alertId}/resolve`, {
      method: 'PATCH',
    });
  },

  async getTelemetry(limit: number = 50, offset: number = 0): Promise<{items: Telemetry[], total: number}> {
    const items = await fetchJson<Telemetry[]>(`${API_BASE}/telemetry/?limit=${limit}&offset=${offset}`);
    return { items, total: items.length };
  },

  async getDevices(): Promise<{items: Device[], total: number}> {
    return fetchJson<{items: Device[], total: number}>(`${API_BASE}/devices/`);
  },

  async getDeviceDetail(deviceId: string): Promise<Device> {
    return fetchJson<Device>(`${API_BASE}/devices/${deviceId}`);
  },

  async getDeviceEvents(deviceId: string, page: number = 1, pageSize: number = 20): Promise<PaginatedResponse<SecurityEvent>> {
    return fetchJson<PaginatedResponse<SecurityEvent>>(`${API_BASE}/devices/${deviceId}/events?page=${page}&page_size=${pageSize}`);
  },

  async getDeviceAlerts(deviceId: string, page: number = 1, pageSize: number = 20): Promise<PaginatedResponse<Alert>> {
    return fetchJson<PaginatedResponse<Alert>>(`${API_BASE}/devices/${deviceId}/alerts?page=${page}&page_size=${pageSize}`);
  },

  async getDeviceTelemetry(deviceId: string): Promise<{items: Telemetry[], total: number}> {
    return fetchJson<{items: Telemetry[], total: number}>(`${API_BASE}/devices/${deviceId}/telemetry`);
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

  async getSimulationHistory(): Promise<{ items: SimulationHistoryItem[] }> {
    return fetchJson<{ items: SimulationHistoryItem[] }>(`${API_BASE}/simulation/history`);
  },

  async getSimulationDetail(simId: number): Promise<SimulationHistoryItem> {
    return fetchJson<SimulationHistoryItem>(`${API_BASE}/simulation/history/${simId}`);
  },

  async getReports(): Promise<ReportMetadata[]> {
    return fetchJson<ReportMetadata[]>(`${API_BASE}/reports`);
  },

  async generateReport(payload: any): Promise<{ metadata: ReportMetadata, data: any }> {
    return fetchJson<{ metadata: ReportMetadata, data: any }>(`${API_BASE}/reports`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
  },

  getReportDownloadUrl(reportId: number): string {
    return `${API_BASE}/reports/${reportId}/export`;
  }
};
