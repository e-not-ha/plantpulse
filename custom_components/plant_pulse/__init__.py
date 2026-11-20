"""The PlantPulse integration."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, SERVICE_FORCE_UPDATE
from .coordinator import PlantPulseCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

SERVICE_FORCE_UPDATE_SCHEMA = vol.Schema(
    {
        vol.Optional("entry_id"): cv.string,
    }
)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Register the force_update service once, at integration setup."""
    hass.data.setdefault(DOMAIN, {})

    async def async_force_update(call: ServiceCall) -> None:
        entry_id = call.data.get("entry_id")
        if entry_id:
            coordinator = hass.data[DOMAIN].get(entry_id)
            if coordinator is None:
                _LOGGER.warning("Entry %s not found for force_update", entry_id)
                return
            await coordinator.async_refresh()
        else:
            for coordinator in hass.data[DOMAIN].values():
                await coordinator.async_refresh()

    hass.services.async_register(
        DOMAIN,
        SERVICE_FORCE_UPDATE,
        async_force_update,
        schema=SERVICE_FORCE_UPDATE_SCHEMA,
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PlantPulse from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = PlantPulseCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload integration when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
