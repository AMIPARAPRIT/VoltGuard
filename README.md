# VoltGuard

VoltGuard is a Physics-Aware ICS/SCADA Intrusion Detection & Prevention System.
It acts as a physics firewall, evaluating whether industrial commands are physically safe for the industrial process, regardless of whether they are syntactically valid Modbus/DNP3 packets.

## Supported Modes
- **Offline / Air-Gapped Mode**: Fully self-contained operation with local physics prediction and policy evaluation.
- **Online / Connected Mode**: Connects to corporate SOCs for telemetry sync and intelligence.
- **Hybrid Mode**: Operates autonomously but provides remote dashboards and alerts.

## Project Structure (Phase 1)
```
VoltGuard-1/
├── backend/            # FastAPI backend foundation
├── config/             # Centralized configuration (YAML)
├── core/               # C++ Modbus parser and canonical schemas
├── dashboard/          # React frontend (Future)
├── data/               # SQLite database storage
├── decision_engine/    # Rust decision engine (Future)
├── docs/               # Architecture documentation
├── parser/             # C++ parser module (Future integration)
├── physics/            # Physics simulation engine (Future)
├── simulator/          # Python mock traffic generator
└── tests/              # Pytest test suite
```

## Technology Stack
- **Backend**: Python 3.11+, FastAPI, SQLAlchemy, SQLite, Uvicorn, Pydantic
- **Traffic Generator**: Python, Scapy, PyModbus
- **Parser (Future)**: C++20
- **Physics (Future)**: Python, NumPy, SciPy
- **Decision Engine (Future)**: Rust
- **Dashboard (Future)**: React, TypeScript

## Installation & Setup

### Prerequisites
- Python 3.11+
- CMake (for building the C++ parser)

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Start the Backend
```bash
# On Windows
.\run.ps1

# Or manually:
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### Run Tests
```bash
pytest tests/ -v
```

### Run Mock Traffic Generator
```bash
python simulator/traffic/traffic_generator.py --count 5
```