# VoltGuard Architecture

This document outlines the architecture for VoltGuard, a Physics-Aware ICS/SCADA Intrusion Detection & Prevention System.

## High-Level Pipeline

```
Industrial Command
        ↓
Modbus/DNP3 Parser (C++)
        ↓
Physics Simulation (Python)
        ↓
Safety Analysis (Python)
        ↓
Decision Engine (Rust)
        ↓
ALLOW / BLOCK
        ↓
Database (SQLite via FastAPI)
        ↓
Real-Time WebSocket
        ↓
Industrial Security Dashboard (React)
```

## Phase 1 Components

Currently in Phase 1, the following foundational components are implemented:

- **Backend Foundation**: A robust FastAPI application providing the core REST APIs and WebSocket infrastructure.
- **Database**: SQLite database with SQLAlchemy ORM handling `SecurityEvent`, `Telemetry`, and `Alert` records.
- **Mock Traffic Generator**: Python script generating simulated Modbus TCP traffic (normal and malicious).
- **C++ Modbus Parser**: Foundation for the high-performance packet parser.

## Future Phases

- **Phase 2**: Integration of the C++ parser into the Python backend and implementation of the Physics Simulation Engine using NumPy/SciPy.
- **Phase 3**: Development of the high-speed Rust Decision Engine for millisecond-latency policy evaluation.
- **Phase 4**: Real-time React + TypeScript dashboard for SOC monitoring.
