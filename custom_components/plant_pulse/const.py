"""Constants for PlantPulse."""

DOMAIN = "plant_pulse"
PLATFORMS = ["sensor"]

CONF_DEVICES = "devices"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_MAX_RETRIES = "max_retries"
CONF_RAW_SOIL = "raw_soil_moisture"
CONF_SERVICE_UUID = "service_uuid"
CONF_CHAR_UUID = "char_uuid"

DEFAULT_SCAN_INTERVAL = 60
DEFAULT_MAX_RETRIES = 3
DEFAULT_RAW_SOIL = False

# ВНИМАНИЕ: подставь реальные UUID из оригинального MCLH-09 проекта,
# если они отличаются. Эти значения — рабочая заготовка.
DEFAULT_SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
DEFAULT_CHAR_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"

ATTR_ERROR_COUNT = "error_count"
ATTR_LAST_UPDATE = "last_update"
ATTR_MAC = "mac"
ATTR_NAME = "name"

SERVICE_FORCE_UPDATE = "force_update"
