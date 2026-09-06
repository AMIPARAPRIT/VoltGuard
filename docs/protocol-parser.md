# VoltGuard Industrial Protocol Parser & Traffic Generator

This document provides complete technical reference and operational documentation for **Phase 3** of VoltGuard: the **Industrial Protocol Parser & Traffic Generator**.

---

## 1. Architecture Overview

VoltGuard processes raw industrial network payloads (Modbus/TCP and DNP3), translates protocol-specific bytes into a normalized, protocol-agnostic command structure, and evaluates physical state impact using the Physics Engine.

```
RAW INDUSTRIAL TRAFFIC (Modbus/TCP, DNP3)
                ↓
    C++ PROTOCOL PARSER (build/voltguard_parser.exe)
 (Modbus / DNP3 + Configurable Register Mapping)
                ↓
       PYTHON BRIDGE & FALLBACK (parser/wrapper.py)
                ↓
       NORMALIZED COMMAND (JSON / Dict)
  (Timestamp, IPs, Device, Cmd, Val, Unit)
                ↓
     PYTHON PHYSICS ENGINE (physics.simulator)
 (Evaluates physical state & safety limits)
                ↓
      PHYSICS RESULT / SAFETY STATE
  (SAFE, WARNING, CRITICAL, CATASTROPHIC)
```

---

## 2. Protocol Specifications & Decoding

### 2.1 Modbus/TCP Parser
- **Port:** TCP 502
- **MBAP Header (7 Bytes):**
  - Transaction ID (2 bytes, big-endian)
  - Protocol ID (2 bytes, default `0x0000`)
  - Length (2 bytes, big-endian byte count following)
  - Unit ID (1 byte, target slave device)
- **PDU Functions Supported:**
  - **Function Code 03 (`0x03`):** Read Holding Registers
  - **Function Code 06 (`0x06`):** Write Single Register
  - **Function Code 16 (`0x10`):** Write Multiple Registers

### 2.2 Register Mapping Configuration

| Register Address | Command Name | Description | Default Unit | Default Target Device |
| :--- | :--- | :--- | :--- | :--- |
| `40001` | `SET_RPM` | Pump RPM Setpoint | RPM | `Pump-01` |
| `40002` | `SET_VALVE` | Valve Opening Position | % | `Valve-01` |
| `40003` | `SET_PRESSURE` | Pipeline Pressure Setpoint | bar | `Pressure-Sensor-01` |
| `40004` | `SET_TEMPERATURE` | Temperature Setpoint | °C | `Temp-Sensor-01` |

### 2.3 DNP3 Parser Foundation
- **Data Link Header (10 Bytes):**
  - Sync Bytes: `0x05 0x64`
  - Length (1 byte)
  - Control Byte (1 byte)
  - Destination Address (2 bytes, little-endian)
  - Source Address (2 bytes, little-endian)
  - Header CRC (2 bytes)
- **Application Layer:** Normalizes function codes (Read, Write, Select, Operate, Direct Operate) and analog output points into `NormalizedCommand`.

---

## 3. Data Schema & Models

### `NormalizedCommand` C++ Struct / Python Dict
```json
{
  "timestamp": "2026-09-06T05:55:22Z",
  "source_ip": "192.168.1.20",
  "destination_ip": "192.168.1.50",
  "device_id": "Pump-01",
  "protocol": "Modbus/TCP",
  "function_code": 6,
  "register": 40001,
  "command": "SET_RPM",
  "value": 50000.0,
  "unit": "RPM",
  "success": true
}
```

---

## 4. Python Wrapper & Physics Bridge (`parser/wrapper.py`)

The wrapper supports dual execution:
1. **C++ Subprocess Invocation:** Executes compiled `build/voltguard_parser.exe` binary.
2. **Native Python Fallback:** In environments without C++ toolchains, uses `NativePythonParser` to decode hexadecimal frames natively.
3. **Physics Engine Bridge:** `parse_and_simulate()` maps `NormalizedCommand` parameters directly to `PhysicsCommand` and calls `physics.simulator.simulate()`.

---

## 5. Industrial Traffic Generator (`parser/traffic_generator/`)

Generates realistic network payloads for testing and demonstration:

### Device Inventory
- `PLC-01`: `192.168.1.10`
- `Pump-01`: `192.168.1.20`
- `Pump-02`: `192.168.1.21`
- `Valve-01`: `192.168.1.30`
- `Pressure-Sensor-01`: `192.168.1.40`
- `Flow-Sensor-01`: `192.168.1.41`
- `RTU-01`: `192.168.1.50`

### Execution Modes
- **`normal`:** Standard operational telemetry (RPM 1000–2000, Valve 40–80%, Pressure 1–4 bar).
- **`suspicious`:** Boundary setpoints & rapid shifts (RPM 2500–4000, Valve 90–100%, high frequency polls).
- **`attack`:** Dangerous OT malicious setpoint overrides (e.g. `SET_RPM` = 50000, 30000, 10000).
- **`mixed`:** Interleaved mix of normal, suspicious, and attack traffic.

CLI Usage:
```bash
python parser/traffic_generator/generator.py --mode attack --count 10 --output console
```

---

## 6. REST API Endpoints (`backend/api/routes/traffic.py`)

- `POST /api/traffic/parse`: Decodes raw hex payload into `NormalizedCommand`.
- `POST /api/traffic/process`: Decodes raw hex payload AND evaluates physics state.
- `POST /api/traffic/generate`: Generates synthetic traffic payloads for specified mode.

---

## 7. Verification & Attack Demonstration

Run the integration demonstration script:
```bash
python scripts/demo_phase3.py
```

### Verified Sample Output
- **Raw Attack Payload:** `00 01 00 00 00 06 01 06 9C 41 C3 50`
- **Extracted Command:** `SET_RPM` = 50000.0 RPM (Register 40001)
- **Physics Prediction:**
  - Predicted Pressure: `7226.57 bar` (Limit: 80.0 bar)
  - Predicted Flow: `2125.00 L/min` (Limit: 500.0 L/min)
  - Predicted Temp: `130.00 °C` (Limit: 120.0 °C)
  - System Stress: `11201.19 MPa` (Limit: 130.0 MPa)
- **Evaluated Safety State:** `CATASTROPHIC`
- **Risk Score:** `100.0 / 100.0`
