# VISION-X Green FinTech

> **Secure Renewable Energy Verification Node** - A blockchain-inspired system that rewards users for generating verifiable green energy while detecting and preventing fraud through ML-powered anomaly detection.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.54.0-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Installation](#installation)
- [Usage](#usage)
- [Hardware Requirements](#hardware-requirements)
- [Fraud Detection](#fraud-detection)
- [API Reference](#api-reference)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

VISION-X Green FinTech is a professional-grade terminal application that bridges renewable energy hardware with fintech rewards. The system:

1. **Monitors** real-time energy production from solar panels via serial connection
2. **Verifies** authenticity using physics-based rules and machine learning
3. **Rewards** users with tokens for verified green energy generation
4. **Detects** fraud attempts (grid power injection, battery spoofing) in real-time

The application features a cyberpunk-inspired black terminal UI with live metrics, real-time graphing, and comprehensive audit logging.

---

## Features

### Core Capabilities

- **Real-Time Monitoring**: Live voltage, current, and power metrics with 100ms refresh rate
- **ML-Powered Anomaly Detection**: Isolation Forest algorithm identifies suspicious patterns
- **Physics-Based Verification**: Enforces solar cell physics constraints (Voc ~0.6-1.0V)
- **User Authentication**: Secure user registration and session management
- **Token Rewards System**: Automatic coin accrual based on verified power output
- **Audit Trail**: Complete SQLite-backed logging of all energy readings
- **Configurable Thresholds**: Adjustable noise filtering and voltage cutoffs
- **Simulation Mode**: Grid attack simulation for testing fraud detection

### Technical Highlights

- **60-second rolling buffer** for ML model training and trend analysis
- **Hardware physics validation** prevents voltage spoofing attacks
- **Noise filtering** eliminates sensor artifacts below configurable thresholds
- **Non-blocking UI** maintains responsive interface during continuous data streaming

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    VISION-X TERMINAL UI                         │
│                      (Streamlit Frontend)                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     APPLICATION LAYER                           │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────────┐ │
│  │   Session   │  │    Serial    │  │   Calibration Config    │ │
│  │   State     │  │   Handler    │  │   (Noise/Voltage)       │ │
│  └─────────────┘  └──────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    VERIFICATION ENGINE                          │
│  ┌─────────────────────────┐  ┌─────────────────────────────┐  │
│  │   Physics Check         │  │   ML Anomaly Detection      │  │
│  │   - Voltage > 2.0V = ✗  │  │   - Isolation Forest        │  │
│  │   - Valid range check   │  │   - Statistical outliers    │  │
│  └─────────────────────────┘  └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATA PERSISTENCE                           │
│                    (SQLite Database)                            │
│  - users: id, name, phone, coins                                │
│  - readings: user_id, timestamp, V/C/P, anomaly_flag, coins     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Serial port (for hardware connection) or simulation mode

### Setup Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/VISION-X-Green-FinTech.git
   cd VISION-X-GREEN-FINTECH
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify installation**
   ```bash
   python serial_test.py
   ```

4. **Run the application**
   ```bash
   streamlit run main.py
   ```

---

## Usage

### First-Time Setup

1. Launch the application - the terminal UI will open in your browser
2. Register a new user by entering name and phone number
3. Note your assigned User ID for future sessions

### Connecting Hardware

1. Connect your solar panel sensor to a serial port (default: COM7)
2. Enter the correct port in the PORT field
3. Click **START** to begin monitoring

### Calibration

Access the sidebar to adjust:

| Parameter | Description | Default |
|-----------|-------------|---------|
| Min Current (A) | Noise floor filter | 0.05 A |
| Min Voltage (V) | Voltage cutoff threshold | 0.5 V |

### Simulation Mode

Enable **SIMULATE GRID ATTACK** to test fraud detection:
- Injects 5.0V / 2.5A fake signal
- Triggers immediate fraud alert
- Validates physics-based detection

---

## Hardware Requirements

### Supported Sensors

- Any Arduino-based voltage/current sensor with serial output
- Output format: `voltage,current,power` (CSV, 115200 baud)
- Single-cell solar panels (0.5-1.0V Voc recommended)

### Wiring Diagram

```
Solar Panel → Voltage Sensor → Arduino → USB → Computer
                │
            Current Sensor
```

### Serial Protocol

```
# Expected format (newline-terminated)
0.75,0.32,0.24
```

---

## Fraud Detection

### Detection Layers

#### Layer 1: Physics Validation
```python
if voltage > 2.0:
    return -1  # Anomaly - Single cell cannot exceed ~1.0V
```

#### Layer 2: Behavioral Analysis
- Isolation Forest identifies statistical outliers
- Trains on 20-sample rolling window
- 5% contamination threshold for anomaly sensitivity

#### Layer 3: Noise Analysis
- Real signals contain natural variance
- Perfect/stable injected values are flagged
- Configurable noise floor filtering

### Response Actions

| Status | Action |
|--------|--------|
| ✓ SECURED | Tokens awarded (power × 0.0001) |
| ✗ FRAUD DETECTED | No reward, incident logged |
| ⏸ IDLE | Monitoring, no action |

---

## API Reference

### Database Functions (`database.py`)

| Function | Parameters | Returns | Description |
|----------|------------|---------|-------------|
| `init_db()` | None | None | Initialize SQLite schema |
| `create_user(name, phone)` | name: str, phone: str | int | Create user, return ID |
| `get_user(user_id)` | user_id: int | tuple | Fetch user record |
| `update_coins(user_id, coins)` | user_id: int, coins: float | None | Update token balance |
| `log_reading(...)` | Multiple | None | Log energy reading |
| `get_history(user_id, limit)` | user_id: int, limit: int | list | Fetch recent readings |

### ML Model (`ml_model.py`)

```python
from ml_model import SolarAnomalyModel

model = SolarAnomalyModel()
model.train(data)  # data: list of [voltage, current, power]
prediction = model.predict([0.75, 0.32, 0.24])  # Returns: 1 (normal) or -1 (anomaly)
```

---

## Project Structure

```
VISION-X-GREEN-FINTECH/
├── main.py              # Streamlit application (entry point)
├── ml_model.py          # SolarAnomalyModel class (Isolation Forest)
├── database.py          # SQLite database operations
├── requirements.txt     # Python dependencies
├── serial_test.py       # Serial connection test utility
├── users.db             # SQLite database (auto-generated)
└── README.md            # This file
```

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Maintain physics-first validation approach
- Preserve terminal UI aesthetic consistency
- All database operations must use parameterized queries
- ML model changes require validation against simulation mode

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Support

For issues, questions, or contributions:
- **Repository**: [GitHub Issues](https://github.com/your-org/VISION-X-Green-FinTech/issues)
- **Documentation**: This README and inline code comments

---

*VISION-X Green FinTech - Securing Renewable Energy, One Token at a Time.*
