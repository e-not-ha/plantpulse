"""Sensor platform for PlantPulse."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DEVICES, DOMAIN, SENSOR_TYPES
from .coordinator import PlantPulseCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: PlantPulseCoordinator = hass.data[DOMAIN][entry.entry_id]
    devices = entry.data.get(CONF_DEVICES, [])

    entities: list[PlantPulseSensor] = []
    for device in devices:
        for key, meta in SENSOR_TYPES.items():
            entities.append(PlantPulseSensor(coordinator, device, key, meta))

    async_add_entities(entities)


class PlantPulseSensor(CoordinatorEntity[PlantPulseCoordinator], SensorEntity):
    """One PlantPulse sensor value."""

    def __init__(
        self,
        coordinator: PlantPulseCoordinator,
        device: dict[str, str],
        sensor_key: str,
        meta: dict[str, str],
    ) -> None:
        super().__init__(coordinator)
        self._mac = device["mac"]
        self._device_name = device["name"]
        self._sensor_key = sensor_key
        self._meta = meta
        self._attr_unique_id = f"{self._mac}_{sensor_key}"
        self._attr_name = f"{self._device_name} {meta['name']}"
        self._attr_native_unit_of_measurement = meta["unit"]
        if meta.get("device_class"):
            self._attr_device_class = meta["device_class"]
        if meta.get("state_class"):
            self._attr_state_class = meta["state_class"]

    @property
    def native_value(self):
        if not self.coordinator.data:
            return None
        device_data = self.coordinator.data.get(self._mac)
        if not device_data:
            return None
        return device_data.get(self._sensor_key)
