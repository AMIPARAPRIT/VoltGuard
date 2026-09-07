# VoltGuard Physics Engine — Technical Documentation

> **DISCLAIMER:** This is a simplified prototype physics model for controlled
> demonstration and is **not intended to control real industrial equipment.**

---

## 1. Why VoltGuard Needs Physics Validation

Traditional ICS/SCADA intrusion detection systems inspect network packets and
ask: *"Is this Modbus command syntactically valid?"*

VoltGuard goes further and asks: *"If this command reaches the machine, what
will happen physically?"*

A Modbus write command that sets pump RPM to 50,000 is syntactically valid.
A packet firewall will pass it. But the physical consequence — catastrophic
pipeline over-pressure — is detected immediately by the physics engine before
the command can be forwarded.

```
INDUSTRIAL COMMAND
      ↓
PHYSICS ENGINE          ← VoltGuard's differentiator
      ↓
PREDICTED PHYSICAL STATE
      ↓
SAFETY ANALYSIS
      ↓
RISK SCORE (0–100)
      ↓
SAFE / WARNING / CRITICAL / CATASTROPHIC
```

---

## 2. Pipeline Model

The physics engine models a simplified industrial fluid pipeline:

```
  ┌─────────┐    ┌─────────┐    ┌────────────┐    ┌──────────────────┐
  │  Pump   │───▶│  Valve  │───▶│  Pipeline  │───▶│  Pressure Sensor │
  └─────────┘    └─────────┘    └────────────┘    └──────────────────┘
   pump_rpm      valve_position   resistance         predicted_pressure
```

The pump drives flow. The valve controls it. The pipeline provides
resistance. The pressure sensor (simulated) reads the result.

---

## 3. Inputs

| Parameter            | Type  | Unit         | Description                              |
|----------------------|-------|--------------|------------------------------------------|
| `pump_rpm`           | float | RPM          | Current pump speed. Required. ≥ 0.       |
| `valve_position`     | float | % (0–100)    | Valve opening. Required. 0=closed.       |
| `current_pressure`   | float | bar          | Inlet pressure. Default = 0.0.           |
| `current_temperature`| float | °C           | Fluid temperature. Default = 20.0.       |
| `pipeline_resistance`| float | dimensionless| Pipeline resistance coefficient. Default = 1.0. |
| `pump_efficiency`    | float | 0–1          | Mechanical efficiency. Default = 0.85.   |

All inputs are validated by Pydantic. Invalid values (NaN, Inf, negative RPM,
valve > 100 %, etc.) raise a `ValidationError` before any simulation runs.

---

## 4. Outputs

| Parameter              | Type  | Unit  | Description                                       |
|------------------------|-------|-------|---------------------------------------------------|
| `predicted_flow`       | float | L/min | Estimated volumetric flow rate                    |
| `predicted_pressure`   | float | bar   | Estimated pipeline outlet pressure                |
| `predicted_temperature`| float | °C    | Estimated fluid temperature                       |
| `system_stress`        | float | MPa   | Estimated pipeline hoop stress                    |
| `risk_score`           | float | 0–100 | Normalized severity (physics-derived, not random) |
| `safety_state`         | enum  | —     | SAFE / WARNING / CRITICAL / CATASTROPHIC          |
| `violations`           | list  | —     | Per-parameter violation details                   |
| `explanation`          | str   | —     | Human-readable summary for dashboard display      |
| `simulation_time_ms`   | float | ms    | Wall-clock time taken for the calculation         |

---

## 5. Equations

All equations are in `physics/equations.py`. They are pure functions with no
side effects.

### 5.1 Flow Rate

```
valve_factor   = valve_position / 100
normalized_rpm = pump_rpm / reference_rpm

flow = base_flow × normalized_rpm × valve_factor × pump_efficiency
```

**Assumption:** Centrifugal pump with linear RPM–flow relationship at a fixed
system curve. In reality, pump curves are parabolic, but linear is sufficient
for prototype demonstration.

### 5.2 Pressure

```
pressure_rise = pressure_gain_coefficient × flow² × pipeline_resistance
pressure_loss = pressure_loss_coefficient × flow  × pipeline_resistance

predicted_pressure = current_pressure + pressure_rise - pressure_loss
```

**Assumption:** Simplified Darcy–Weisbach / Bernoulli head model. The
quadratic term dominates at high flow, which causes the pressure to escalate
rapidly when RPM is very high — correctly triggering CATASTROPHIC detection.

### 5.3 Temperature

```
predicted_temperature = current_temperature + thermal_gain_coefficient × flow
```

**Assumption:** Linear temperature rise with flow rate due to fluid friction
and heat generation.

### 5.4 Pipeline Hoop Stress

```
system_stress = predicted_pressure × stress_per_bar
```

**Assumption:** Thin-walled pressure vessel (Lamé equation simplified).
`stress_per_bar` encapsulates the pipe geometry (radius / wall thickness).

---

## 6. Safety Limits

Safety limits are loaded from `config/config.yaml` via `backend/core/config.py`.
They are **never hardcoded** in the physics engine.

| Parameter         | Default Value | Unit  |
|-------------------|---------------|-------|
| `max_pressure`    | 150.0         | bar   |
| `max_rpm`         | 3600          | RPM   |
| `max_temperature` | 120.0         | °C    |
| `max_flow`        | 500.0         | L/min |
| `max_stress`      | 250.0         | MPa   |

To change a limit: edit `config/config.yaml` and restart the service.

---

## 7. Risk Scoring

Risk score is computed from the **ratio** of each physical value to its limit:

```
ratio_i = value_i / limit_i
```

Each ratio is mapped to a score using a clamped quadratic scale:

```
score_i = min(ratio_i, 1.5)² / 1.5² × 100
```

The final risk score is the **maximum** score across all five parameters:

```
risk_score = max(score_pressure, score_rpm, score_flow, score_temp, score_stress)
```

This ensures the worst physical condition drives the overall risk rating.

| Ratio  | Score (approx) | Meaning                  |
|--------|----------------|--------------------------|
| 0.00   | 0              | No load                  |
| 0.70   | 22             | WARNING boundary          |
| 0.90   | 36             | CRITICAL boundary         |
| 1.00   | 44             | At limit                 |
| 1.22   | 66             | 22% over limit            |
| 1.50   | 100            | Maximum (saturated)       |

---

## 8. Safety States

| State         | Condition                              | Action                     |
|---------------|----------------------------------------|----------------------------|
| `SAFE`        | All ratios < 70% of their limits       | No action required          |
| `WARNING`     | Any ratio ≥ 70% (but < 90%)           | Alert operator              |
| `CRITICAL`    | Any ratio ≥ 90% (but < 100%)          | Prepare controlled shutdown |
| `CATASTROPHIC`| Any ratio ≥ 100% (limit exceeded)     | Block command, emergency stop|

The overall state is always the **most severe** state across all parameters.

---

## 9. Example — Normal Command

**Input:**
```json
{
  "pump_rpm": 1500,
  "valve_position": 70,
  "current_pressure": 10.0,
  "current_temperature": 40.0
}
```

**Expected output (approximate):**
```
Predicted Flow     :   105.0  L/min
Predicted Pressure :    27.1  bar
Predicted Temp     :    44.2  °C
System Stress      :    42.0  MPa
Risk Score         :    11.4
Safety State       :    SAFE
```

All values well within limits. System is operating normally.

---

## 10. Example — Attack Command

**Input:**
```json
{
  "pump_rpm": 50000,
  "valve_position": 100,
  "current_pressure": 10.0,
  "current_temperature": 40.0
}
```

**Expected output (approximate):**
```
Predicted Flow     :  4250.0  L/min
Predicted Pressure :  2797.8  bar   (limit: 150.0)
Risk Score         :   100.0
Safety State       :   CATASTROPHIC
Explanation        :   CRITICAL ALERT: Multiple physical safety constraints violated ...
```

The 50,000 RPM command produces a flow ~14× the safe maximum. The quadratic
pressure model responds by generating pressure ~18× the safety limit. All five
physical parameters exceed their limits. The engine classifies this as
CATASTROPHIC and the system should block the command.

---

## 11. Known Limitations

1. **Linear flow model:** Real centrifugal pumps have parabolic RPM–flow curves.
   This prototype uses a simplified linear relationship.

2. **Quasi-steady-state:** The engine computes a single equilibrium point per
   call. It does not model transient dynamics (pressure waves, water hammer).

3. **No heat transfer model:** Temperature rise is a fixed linear function of
   flow. Real systems depend on pipe material, insulation, and ambient conditions.

4. **Single pipeline segment:** The model does not simulate branching networks,
   multiple pumps, or parallel valve configurations.

5. **Uncalibrated coefficients:** The pressure gain, loss, thermal, and stress
   coefficients are chosen to produce meaningful prototype behaviour. They are
   NOT derived from real equipment measurements.

6. **No material fatigue:** Cyclic stress and fatigue accumulation are not
   modelled.

**This engine is intended for prototype demonstration and security research
only. It must not be used to make decisions about real industrial equipment.**

---

## File Structure

```
physics/
├── __init__.py          Public API: simulate(), simulate_timeseries()
├── models.py            Pydantic input/output models, SafetyState enum
├── equations.py         Pure math: flow, pressure, temperature, stress
├── safety.py            Classification, risk scoring, explanations
├── simulator.py         Orchestration: config → equations → safety → result
├── exceptions.py        PhysicsValidationError, PhysicsSimulationError
└── tests/
    ├── test_simulator.py  End-to-end scenario tests
    ├── test_safety.py     Isolated safety module tests
    └── test_boundaries.py Input validation / boundary tests
```

---

## Running the Engine

```bash
# Demo (no server needed)
python scripts/test_physics_demo.py

# Unit tests
pytest physics/tests/ -v

# All tests (Phase 1 + Phase 2)
pytest tests/ physics/tests/ -v
```
