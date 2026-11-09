# PlantPulse

Custom Home Assistant integration for BLE plant sensors (MCLH-09 compatible).

## Features
- Multi-device support
- Temperature, humidity, soil moisture, illuminance, battery
- Retry with exponential backoff
- Force update service
- Configurable BLE UUIDs
- Options flow for live reconfiguration

## Installation via HACS
1. Add this repo as a custom repository in HACS (type: Integration).
2. Install "PlantPulse".
3. Restart Home Assistant.
4. Go to Settings → Devices & Services → Add Integration → PlantPulse.

## Configuration
Enter devices one per line:
AA:BB:CC:DD:EE:FF; Living Room Plant

Adjust polling interval, retries, raw soil mode and BLE UUIDs as needed.

## Service
`plant_pulse.force_update` — force immediate poll.
