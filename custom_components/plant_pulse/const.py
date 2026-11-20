"""Constants for the PlantPulse integration."""
from __future__ import annotations

DOMAIN = "plant_pulse"
SERVICE_FORCE_UPDATE = "force_update"

CONF_DEVICES = "devices"

# Описание типов датчиков. Ключи должны совпадать с ключами,
# возвращаемыми decode_payload() в coordinator.py.
SENSOR_TYPES: dict[str, dict[str, str]] = {
    "temperature": {
        "name": "Температура",
        "unit": "°C",
        "device_class": "temperature",
        "state_class": "measurement",
    },
    "humidity": {
        "name": "Влажность почвы",
        "unit": "%",
        "device_class": "humidity",
        "state_class": "measurement",
    },
    "illuminance": {
        "name": "Освещённость",
        "unit": "lx",
        "device_class": "illuminance",
        "state_class": "measurement",
    },
    "battery": {
        "name": "Батарея",
        "unit": "%",
        "device_class": "battery",
        "state_class": "measurement",
    },
}
