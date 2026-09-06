# VoltGuard High-Speed Rust Decision Engine

This document provides complete technical documentation for **Phase 4** of VoltGuard: the **Rust Decision Engine**.

---

## 1. Why VoltGuard Needs a Rust Decision Engine

In Critical Infrastructure / Industrial Control Systems (ICS/SCADA), security evaluation must happen at sub-millisecond speeds directly in line with OT physical processes. 

While Python handles physical differential equations and physics modeling with great flexibility, the final security policy enforcement and fail-closed decision logic require:
- High performance and minimal memory overhead.
- Strict type safety and zero unhandled exception crashes.
- Deterministic fail-closed security enforcement (never defaulting to `ALLOW` under failure).

---

## 2. Responsibilities & Separation of Concerns

```
Industrial Command (Modbus / DNP3 Payload)
                ↓
    C++ Protocol Parser (parser/)
                ↓
    Normalized Command (JSON)
                ↓
 Python Physics Simulation (physics/)  ← Calculates physical metrics (Pressure, Flow, Temp, Stress, Risk)
                ↓
   Physics Result (JSON)
                ↓
   Rust Decision Engine (decision_engine/) ← Enforces security policy & fail-closed safety rule
                ↓
    Decision Result (JSON)
 (ALLOW | MONITOR | BLOCK | BLOCK_CRITICAL)
                ↓
     FastAPI Backend / Database
```

| Component | Language | Primary Responsibility |
| :--- | :--- | :--- |
| **Physics Engine** | Python | Calculates physical fluid dynamics, pressure gain, thermal expansion, hoop stress, and assigns physical `SafetyState`. |
| **Decision Engine** | Rust | Enforces policy decision logic, formats violation reports, measures microsecond latency, and executes fail-closed security rules. |

---

## 3. Data Models

### Input Model (`PhysicsResultInput`)
```json
{
  "pump_rpm": 50000.0,
  "valve_position": 50.0,
  "predicted_pressure": 7226.57,
  "predicted_flow": 2125.0,
  "predicted_temperature": 130.0,
  "system_stress": 11201.19,
  "risk_score": 100.0,
  "safety_state": "CATASTROPHIC",
  "violations": [
    {
      "parameter": "PUMP_RPM",
      "value": 50000.0,
      "limit": 3600.0,
      "description": "Pump RPM exceeds safety limit by 1288.9%"
    }
  ],
  "explanation": "Immediate shutdown recommended.",
  "simulation_time_ms": 0.42
}
```

### Output Model (`DecisionResult`)
```json
{
  "decision": "BLOCK_CRITICAL",
  "risk_score": 100.0,
  "safety_state": "CATASTROPHIC",
  "reason": "CATASTROPHIC PHYSICAL THREAT: Severe safety limit violation detected. Emergency block initiated. (Risk Score: 100.0) Violations: [PUMP_RPM: actual=50000.00, limit=3600.00 (Pump RPM exceeds safety limit by 1288.9%)]",
  "timestamp": "2026-09-06T06:07:06Z",
  "decision_latency_us": 48
}
```

---

## 4. Decision Policy & Fail-Closed Logic

### Decision Policy Mapping

| Physics `SafetyState` | Security `Decision` | Action Description |
| :--- | :--- | :--- |
| `SAFE` | `ALLOW` | Command safe for execution. |
| `WARNING` | `MONITOR` | Command allowed; elevated monitoring & logging enabled. |
| `CRITICAL` | `BLOCK` | Safety limits near threshold; command execution blocked. |
| `CATASTROPHIC` | `BLOCK_CRITICAL` | Severe safety violation; emergency block & alert triggered. |

### Fail-Closed Security Rule
If physical safety validation data is missing, invalid, corrupted, unparseable, or unavailable:
- **Decision:** `BLOCK_CRITICAL`
- **Reason:** `"Physical safety validation unavailable."`
- **Risk Score:** `100.0`
- **Safety State:** `CATASTROPHIC`

This guarantees that an attacker cannot bypass security controls by corrupting or suppressing physics payload data.

---

## 5. Python ↔ Rust Communication Interface

The backend communicates with the Rust engine via:
1. **CLI / Stdin Interface:** The Python `RustDecisionEngineWrapper` (`decision_engine/wrapper.py`) executes `decision_engine.exe --json '<payload>'` or pipes JSON through `stdin`.
2. **Subprocess & Fallback:** If the Rust binary is missing or fails, the wrapper engages a Python mirror of the decision policy retaining full fail-closed security guarantees.

---

## 6. 50000 RPM Attack Pipeline Walkthrough

1. **Parser:** Ingests Modbus packet `00010000000601069C41C350` -> decodes FC 06, Register 40001 (`SET_RPM`), Value `50000`.
2. **Physics:** Computes predicted pressure `7226.57 bar` (Limit: `80 bar`). Classifies physical state as `CATASTROPHIC`, Risk Score `100.0`.
3. **Rust Decision Engine:** Receives physical classification. Checks decision policy mapping (`CATASTROPHIC` -> `BLOCK_CRITICAL`).
4. **Result:** Produces `BLOCK_CRITICAL` with microsecond latency tag (`decision_latency_us`).

---

## 7. Build and Run Commands

### Rust Build Command
```cmd
.\build_decision_engine.bat
```
or
```bash
cargo build --release
```

### Direct CLI Execution
```cmd
.\build\decision_engine.exe --json "{\"risk_score\":100.0,\"safety_state\":\"CATASTROPHIC\",\"violations\":[]}"
```

### Python Backend / Smoke Check
```bash
python scripts/smoke_phase4.py
```
