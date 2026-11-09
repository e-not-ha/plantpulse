"""Sensor platform for PlantPulse."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.unit import UnitOfTemperature

from .const import (
    ATTR_ERROR_COUNT,
    ATTR_LAST_UPDATE,
    ATTR_MAC,
    ATTR_NAME,
    CONF_DEVICES,
    DOMAIN,
)
from .coordinator import PlantPulseCoordinator

SENSOR_TYPES = {
    "temperature": {
        "name": "Temperature",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.CELSIUS,
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "humidity": {
        "name": "Humidity",
        "device_class": SensorDeviceClass.HUMIDITY,
        "unit": "%",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "soil_moisture": {
        "name": "Soil Moisture",
        "device_class": SensorDeviceClass.MOISTURE,
        "unit": "%",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "light": {
        "name": "Illuminance",
        "device_class": SensorDeviceClass.ILLUMINANCE,
        "unit": "lx",
        "state_class": SensorStateClass.MEASUREMENT,
    },
    "battery": {
        "name": "Battery",
        "device_class": SensorDeviceClass.BATTERY,
        "unit": "%",
        "state_class": SensorStateClass.MEASUREMENT,
    },
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up PlantPulse sensors."""
    coordinator: PlantPulseCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for device in entry.data.get(CONF_DEVICES, []):
        for key, meta in SENSOR_TYPES.items():
            entities.append(
                PlantPulseSensor(coordinator, entry, device, key, meta)
            )
    async_add_entities(entities)


class PlantPulseSensor(CoordinatorEntity, SensorEntity):
    """Representation of a PlantPulse sensor."""

    def __init__(
        self,
        coordinator: PlantPulseCoordinator,
        entry: ConfigEntry,
        device: dict,
        key: str,
        meta: dict,
    ) -> None:
        super().__init__(coordinator)
        self._mac = device["mac"]
        self._name = device.get("name", self._mac)
        self._key = key
        self._meta = meta
        self._attr_unique_id = f"plantpulse_{self._mac}_{key}"
        self._attr_name = f"{self._name} {meta['name']}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._mac)},
            "name": self._name,
            "manufacturer": "Life Control",
            "model": "MCLH-09",
        }

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data.get(self._mac, {})
        if not data.get("available", False):
            return None
        return data.get(self._key)

    @property
    def native_unit_of_measurement(self) -> str | None:
        return self._meta.get("unit")

    @property
    def device_class(self) -> SensorDeviceClass | None:
        return self._meta.get("device_class")

    @property
    def state_class(self) -> SensorStateClass | None:
        return self._meta.get("state_class")

    @property
    def available(self) -> bool:
        data = self.coordinator.data.get(self._mac, {})
        return bool(data.get("available", False))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data.get(self._mac, {})
        return {
            ATTR_MAC: self._mac,
            ATTR_ERROR_COUNT: data.get(ATTR_ERROR_COUNT, 0),
            ATTR_LAST_UPDATE: data.get(ATTR_LAST_UPDATE),
        }
