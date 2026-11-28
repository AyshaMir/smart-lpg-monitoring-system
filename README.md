
# Smart LPG Monitoring System

## Project Overview

The Smart LPG Monitoring System is an embedded IoT prototype designed to monitor LPG cylinder levels, detect potential gas leaks, and provide real-time alerts through physical indicators and a web-based dashboard.

The system uses a Raspberry Pi Pico 2 W running MicroPython to collect sensor readings, process alert conditions, and communicate with the dashboard over Wi-Fi.

## Features

- Real-time LPG weight and percentage monitoring.
- Potential gas leak detection using an MQ-5 sensor.
- LED and buzzer alerts.
- Low LPG warnings at 20% remaining capacity.
- Sensor fault detection.
- Web-based monitoring dashboard.
- Historical sensor readings and CSV export.
- Daily consumption and remaining LPG predictions.
- Cooking session tracking.
- LPG consumption and refill cost calculations.
- Demo mode and mock API for testing without hardware.

## Hardware Components

- Raspberry Pi Pico 2 W
- MQ-5 gas sensor
- HX711 load cell amplifier
- 10 kg load cell
- Green, yellow and red LEDs
- Buzzer
- Resistors and connecting wires
- Load cell mounting platform

## Software Architecture

The firmware follows a modular, non-blocking architecture that separates sensor acquisition, alert processing, hardware indicators, network communication and task scheduling.

| File              | Purpose                           |
| ----------------- | --------------------------------- |
| `main.py`       | Main firmware execution           |
| `sensors.py`    | Sensor acquisition and processing |
| `hx711.py`      | Load cell amplifier communication |
| `alerts.py`     | Alert state machine               |
| `indicators.py` | LED and buzzer control            |
| `timebase.py`   | Non-blocking task scheduling      |
| `wifi.py`       | Wi-Fi connectivity                |
| `server.py`     | HTTP API server                   |

## Alert States

| State         | Description                          |
| ------------- | ------------------------------------ |
| NORMAL        | LPG above 20% with no suspected leak |
| LOW_GAS       | LPG at or below 20%                  |
| LEAK_DETECTED | Potential gas leak detected          |
| FAULT         | Required sensor data is unavailable  |

Gas leak alerts receive priority over other alert conditions.

## Dashboard

The dashboard consists of four main sections:

- **Monitor:** Current LPG level, sensor readings, alerts and consumption predictions.
- **History:** Historical sensor graphs and CSV export.
- **Cooking Sessions:** Session duration, LPG consumption and associated costs.
- **Costs:** Remaining LPG value, consumption costs and estimated refill costs.

Demo and live history are stored separately. Mock API readings are identified as simulated and excluded from live history and cooking session records.

## Running the Dashboard

From the project root, start the dashboard server:

```bash
python -m http.server 8080 --directory dashboard
```

Open the following address in a browser:

```text
http://127.0.0.1:8080/indx.html
```

## Testing Without Hardware

Start the mock Pico API in a separate terminal:

```bash
python mockpico.py
```

Select Live Pico API on the dashboard and enter:

```text
http://127.0.0.1:8000/api/status
```

Alternatively, use Demo mode to simulate normal operation, low LPG, potential gas leaks and sensor faults.

## Firmware Regression Testing

Run the following command from the project root:

```bash
python tests/test_logic.py
```

The regression tests verify alert and indicator logic without requiring physical hardware.

## Current Development Status

- [X] Modular firmware architecture
- [X] MQ-5 sensor testing
- [X] LED and buzzer testing
- [X] Alert state machine
- [X] Firmware regression tests
- [X] Dashboard implementation
- [X] Demo mode testing
- [X] Mock API integration
- [ ] Load cell troubleshooting and calibration
- [ ] Complete physical hardware integration
- [ ] Live Pico dashboard verification
- [ ] Final end-to-end testing

## Limitations

- Load cell calibration is required before accurate LPG weight measurements can be obtained.
- The dashboard currently assumes a 3 kg LPG capacity.
- Consumption predictions require sufficient historical weight readings.
- Browser-based historical data is stored locally.
- The system is an educational prototype and is not a certified gas detection or safety device.
