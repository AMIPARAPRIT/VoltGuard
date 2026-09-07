# VoltGuard Phase 9 — Simulation Console & Security Reporting

VoltGuard provides a physics-aware industrial simulation and security reporting suite integrated with the core operational pipeline.

---

## 1. Simulation Architecture

All simulations execute through the central VoltGuard pipeline:

```text
Simulation Input
      ↓
Parser / Normalized Command
      ↓
Physics Engine
      ↓
Safety State & Risk Score
      ↓
Rust Decision Engine
      ↓
Database Persistence & Traceability
      ↓
WebSocket Live Broadcast
      ↓
Simulation Console Result
```

> [!IMPORTANT]
> The backend remains the sole authoritative source of truth. The frontend does not calculate pressure, flow, risk scores, safety states, or policy decisions.

---

## 2. Predefined Scenarios

Simulations accept predefined scenarios or custom parameters. The inputs drive the existing Physics Engine and Rust Decision Engine:

| Scenario | Pump RPM | Valve Position | Protocol | Description | Expected Output |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **NORMAL** | 1500 RPM | 60% | Modbus/TCP | Baseline operating load | `SAFE` / `ALLOW` |
| **WARNING** | 3200 RPM | 88% | Modbus/TCP | High operating load near limit | `WARNING` / `MONITOR` |
| **CRITICAL** | 4200 RPM | 95% | Modbus/TCP | Exceeds safe operating envelope | `CRITICAL` / `BLOCK` |
| **ATTACK** | 50 000 RPM | 100% | Modbus/TCP (Hex) | Extreme malicious over-speed payload | `CATASTROPHIC` / `BLOCK_CRITICAL` |
| **CUSTOM** | Variable | Variable | Modbus/DNP3 | Manual parameter testing | Physics-determined |

---

## 3. Custom Simulation

Operators can manually specify parameters for controlled testing:
- **Command**: `SET_RPM`, `SET_VALVE`, `SET_PRESSURE`
- **Value**: Numeric parameter target (RPM: 100–60 000, Valve: 0–100%)
- **Protocol**: Modbus/TCP or DNP3
- **Device ID**: Target SCADA device (`Pump-01`, `PLC-01`, `Valve-01`)
- **Source IP**: IP address of the commanding origin

---

## 4. Technical Attack Chain Visualization

For hazardous commands resulting in non-ALLOW security decisions, VoltGuard visualizes the causal attack chain using empirical backend metrics:

```text
COMMAND ISSUED (e.g. 50 000 RPM)
   ↓
PHYSICAL IMPACT (Pressure: 288.0 bar, Stress: 345.6 MPa)
   ↓
SAFETY VIOLATION DETECTED (MAX_PRESSURE_EXCEEDED, MAX_STRESS_EXCEEDED)
   ↓
SAFETY STATE EVALUATION (CATASTROPHIC)
   ↓
RUST DECISION ENGINE POLICY (BLOCK_CRITICAL)
```

---

## 5. Security & Physics Report Center

VoltGuard features a dedicated Report Center allowing operators to generate authoritative audit reports:

### Report Types
1. **SECURITY EVENT REPORT**: In-depth analysis of specific industrial security events.
2. **PHYSICAL SAFETY REPORT**: Physical parameter limit checks, parameter violations, and safety state breakdown.
3. **SIMULATION REPORT**: Audit summary of simulation runs, inputs, and security outcomes.
4. **INCIDENT SUMMARY**: Comprehensive incident report featuring System Summary, Target Incident, Physical Analysis, Safety Violations, Security Policy Evaluation, Related Events/Alerts, and a Chronological Incident Timeline.
5. **SYSTEM ACTIVITY REPORT**: Overall system operational activity, event counts, alert counts, and device health status.

---

## 6. PDF Export Service

Reports are compiled on the backend using `fpdf2` and downloaded directly via HTTP response:
- **Header & Metadata**: Project title, Report ID, UTC timestamp, and filter criteria.
- **System Summary**: Real operational counts for devices, events, alerts, blocked commands, and critical violations.
- **Physical Analysis & Authoritative Limits**: Tabular view of actual values vs configured safety thresholds (`max_pressure: 80 bar`, `max_rpm: 3600 RPM`, `max_temperature: 120 °C`, `max_flow: 500 L/min`, `max_stress: 130 MPa`).
- **Incident Timeline**: Chronological steps from command ingest to physics evaluation, violation detection, Rust decision, and alert creation.
- **Security Policy Details**: Exact decision, policy reason, safety state, and physics explanation.

---

## 7. Operational Traceability

Complete end-to-end traceability is enforced across the system:

$$\text{Report} \longrightarrow \text{Incident} \longrightarrow \text{Alert} \longrightarrow \text{Security Event} \longrightarrow \text{Device} \longrightarrow \text{Physics Consequence} \longrightarrow \text{Rust Decision}$$
