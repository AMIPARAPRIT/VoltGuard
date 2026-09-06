# VoltGuard End-to-End System Pipeline & Architecture

This document provides technical documentation for **Phase 5** of VoltGuard: the **Full End-to-End Backend Integration & Pipeline Orchestration**.

---

## 1. System Target Architecture

```text
                ┌──────────────────────┐
                │ Industrial Traffic   │
                │ / Simulation Stream  │
                └──────────┬───────────┘
                           ↓
                ┌──────────────────────┐
                │ Protocol Parser      │
                │ Modbus/TCP & DNP3    │
                └──────────┬───────────┘
                           ↓
                ┌──────────────────────┐
                │ Normalized Command   │
                └──────────┬───────────┘
                           ↓
                ┌──────────────────────┐
                │ Physics Engine       │
                │ Fluid Dynamics &     │
                │ Safety Boundaries    │
                └──────────┬───────────┘
                           ↓
                ┌──────────────────────┐
                │ Physics Result       │
                │ Safety State / Risk  │
                └──────────┬───────────┘
                           ↓
                ┌──────────────────────┐
                │ Rust Decision Engine │
                │ Policy & Fail-Closed │
                └──────────┬───────────┘
                           ↓
                 ┌─────────┴─────────┐
                 ↓                   ↓
             ALLOW/MONITOR      BLOCK/BLOCK_CRITICAL
                 │                   │
                 └─────────┬─────────┘
                           ↓
                ┌──────────────────────┐
                │ Database Persistence │
                │ Event / Alert / Telem│
                └──────────┬───────────┘
                           ↓
                ┌──────────────────────┐
                │ WebSocket Broadcast  │
                │ /ws/telemetry        │
                └──────────┬───────────┘
                           ↓
                 Future Phase 6 Dashboard
```

---

## 2. Central Pipeline Orchestration (`PipelineService`)

All industrial commands pass through a single entry point in [`backend/services/pipeline_service.py`](file:///d:/infotach/VoltGuard/VoltGuard-1/backend/services/pipeline_service.py): `pipeline_service.process_pipeline()`.

### Step 1: Protocol Parsing
- Ingests raw hex frame or command dict.
- Uses `ProtocolParserWrapper` (C++ parser binary or Python fallback) to extract `NormalizedCommand`:
  `{timestamp, source_ip, destination_ip, device_id, protocol, function_code, register, command, value, unit}`

### Step 2: Physics Simulation
- Passes extracted parameters to `physics.simulator.simulate()`.
- Calculates predicted physical values: `predicted_pressure`, `predicted_flow`, `predicted_temperature`, `system_stress`.
- Evaluates physical safety constraints and computes `risk_score` (0–100) and `safety_state` (`SAFE`, `WARNING`, `CRITICAL`, `CATASTROPHIC`).

### Step 3: Rust Policy Evaluation & Fail-Closed Protection
- Passes `PhysicsResult` to `RustDecisionEngineWrapper`.
- Evaluates security decision:
  - `SAFE` → `ALLOW`
  - `WARNING` → `MONITOR`
  - `CRITICAL` → `BLOCK`
  - `CATASTROPHIC` → `BLOCK_CRITICAL`
- If parser, physics engine, or decision engine fails, the system **fails closed**: returns `BLOCK_CRITICAL` with reason `"Physical safety validation unavailable."`

### Step 4: Database Persistence & Alert Generation
- **`SecurityEvent`:** Automatically persists every parsed packet, physical metrics, decision, and total latency into SQLite.
- **`Alert`:** Automatically creates an alert when decision is `MONITOR` (Warning), `BLOCK` (Critical), or `BLOCK_CRITICAL` (Emergency).
- **`Telemetry`:** Automatically updates real-time sensor history with latest physical state.

### Step 5: WebSocket Live Event Broadcast
- Broadcasts real-time JSON payloads to all clients connected to `/ws/telemetry`.

```json
{
  "type": "security_event",
  "timestamp": "2026-09-06T06:13:33Z",
  "device_id": "Pump-01",
  "protocol": "Modbus/TCP",
  "command": "SET_RPM",
  "value": 50000.0,
  "predicted_pressure": 7226.57,
  "predicted_flow": 2125.0,
  "predicted_temperature": 130.0,
  "system_stress": 11201.19,
  "risk_score": 100.0,
  "safety_state": "CATASTROPHIC",
  "decision": "BLOCK_CRITICAL",
  "reason": "CATASTROPHIC PHYSICAL THREAT: Severe safety limit violation detected.",
  "event_id": 3,
  "alert_id": 2,
  "total_latency_ms": 9.32
}
```

---

## 3. REST API Endpoint Specifications

| HTTP Method | Endpoint Path | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Service health status. |
| `GET` | `/api/system/status` | System health check reporting actual subsystem status (`backend`, `database`, `parser`, `physics_engine`, `decision_engine`, `websocket`). |
| `POST` | `/api/simulation/command` | Submit command or hex payload for full pipeline execution. |
| `POST` | `/api/simulation/start` | Start automated background traffic simulation stream. |
| `POST` | `/api/simulation/stop` | Stop active background traffic simulation stream. |
| `GET` | `/api/events` | Query paginated historical security events. |
| `GET` | `/api/alerts` | Query security and safety alerts. |
| `GET` | `/api/telemetry` | Query physical sensor telemetry history. |
| `WS` | `/ws/telemetry` | WebSocket stream for live pipeline events and telemetry. |

---

## 4. Phase 6 Dashboard Integration Guide

The backend is configured to serve as the single source of truth for the upcoming Phase 6 Dashboard:
- Connect to `/ws/telemetry` for live event updates.
- Fetch initial states and paginated history from `/api/events`, `/api/alerts`, `/api/telemetry`.
- Monitor system status from `/api/system/status`.
- Send manual setpoint injections or attack scenarios via `/api/simulation/command`.
