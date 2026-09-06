export type SafetyState = 'SAFE' | 'WARNING' | 'CRITICAL' | 'CATASTROPHIC' | 'UNKNOWN';
export type Decision = 'ALLOW' | 'MONITOR' | 'BLOCK' | 'BLOCK_CRITICAL';

export interface SystemStatus {
  backend: string;
  database: string;
  parser: string;
  physics_engine: string;
  decision_engine: string;
  websocket: string;
  websocket_clients: number;
}

export interface SecurityEvent {
  id: number;
  timestamp: string;
  source_ip?: string;
  destination_ip?: string;
  device?: string;
  protocol: string;
  command?: string;
  command_value?: number;
  predicted_pressure?: number;
  predicted_flow?: number;
  predicted_temperature?: number;
  risk_score?: number;
  safety_state?: SafetyState;
  decision?: Decision;
  reason?: string;
  violations?: string;
  explanation?: string;
  function_code?: number;
  register?: number;
  alert_id?: number;
  latency_ms?: number;
}

export interface Alert {
  id: number;
  timestamp: string;
  severity: 'INFO' | 'WARNING' | 'CRITICAL' | 'CATASTROPHIC';
  status: 'ACTIVE' | 'ACKNOWLEDGED' | 'RESOLVED';
  title: string;
  message?: string;
  device?: string;
  event_id?: number;
  acknowledged: boolean;
  acknowledged_at?: string;
  resolved_at?: string;
}

export interface AlertSummary {
  total: number;
  active: number;
  acknowledged: number;
  resolved: number;
  critical: number;
  catastrophic: number;
  warning: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

export interface Device {
  id: number;
  device_id: string;
  name?: string;
  device_type?: string;
  ip_address?: string;
  protocol?: string;
  connection_status: 'ONLINE' | 'OFFLINE' | 'STALE';
  last_seen?: string;
  last_pump_rpm?: number;
  last_valve_position?: number;
  last_pressure?: number;
  last_flow_rate?: number;
  last_temperature?: number;
  last_stress?: number;
  last_risk_score?: number;
  last_safety_state?: SafetyState;
  last_decision?: Decision;
}

export interface Telemetry {
  id?: number;
  timestamp: string;
  device?: string;
  pump_rpm?: number;
  valve_position?: number;
  pressure?: number;
  flow_rate?: number;
  temperature?: number;
  stress?: number;
}

export interface NormalizedCommand {
  timestamp: string;
  source_ip: string;
  destination_ip: string;
  device_id: string;
  protocol: string;
  function_code: number;
  register: number;
  command: string;
  value: number;
  unit: string;
  success: boolean;
  error?: string;
}

export interface PhysicsResult {
  pump_rpm: number;
  valve_position: number;
  current_pressure: number;
  current_temperature: number;
  predicted_flow: number;
  predicted_pressure: number;
  predicted_temperature: number;
  system_stress: number;
  pressure_limit: number;
  rpm_limit: number;
  temperature_limit: number;
  flow_limit: number;
  stress_limit: number;
  risk_score: number;
  safety_state: SafetyState;
  violations: Array<{
    parameter: string;
    value: number;
    limit: number;
    description: string;
  }>;
  explanation: string;
  simulation_time_ms: number;
}

export interface DecisionResult {
  decision: Decision;
  risk_score: number;
  safety_state: SafetyState;
  reason: string;
  timestamp: string;
  decision_latency_us: number;
}

export interface PipelineResponse {
  normalized_command?: NormalizedCommand;
  physics_result?: PhysicsResult;
  decision_result?: DecisionResult;
  event_id?: number;
  alert_id?: number;
  telemetry_id?: number;
  timing_ms?: {
    physics_latency_ms: number;
    total_processing_ms: number;
  };
}

export interface WebSocketMessage {
  type: string;
  timestamp: string;
  device_id?: string;
  protocol?: string;
  command?: string;
  value?: number;
  predicted_pressure?: number;
  predicted_flow?: number;
  predicted_temperature?: number;
  system_stress?: number;
  risk_score?: number;
  safety_state?: SafetyState;
  decision?: Decision;
  reason?: string;
  event_id?: number;
  alert_id?: number;
  total_latency_ms?: number;
}
