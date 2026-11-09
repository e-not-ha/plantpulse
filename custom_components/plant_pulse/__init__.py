"""PlantPulse integration for BLE plant sensors."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_CHAR_UUID,
    CONF_DEVICES,
    CONF_MAX_RETRIES,
    CONF_RAW_SOIL,
    CONF_SCAN_INTERVAL,
    CONF_SERVICE_UUID,
    DEFAULT_CHAR_UUID,
    DEFAULT_MAX_RETRIES,
    DEFAULT_RAW_SOIL,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SERVICE_UUID,
    DOMAIN,
    PLATFORMS,
    SERVICE_FORCE_UPDATE,
)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up PlantPulse."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PlantPulse from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = PlantPulseCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def async_force_update(call):
        await coordinator.async_refresh()

    hass.services.async_register(
        DOMAIN, SERVICE_FORCE_UPDATE, async_force_update
    )

    entry.async_on_unload(
        entry.add_update_listener(async_reload_entry)
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
