"""Config flow for PlantPulse."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_DEVICES, DOMAIN

_LOGGER = logging.getLogger(__name__)

DEFAULT_DEVICES = "AA:BB:CC:DD:EE:FF;Растение 1"


def parse_devices(raw: str) -> list[dict[str, str]]:
    """Parse `MAC;Name` lines into a list of dicts."""
    devices: list[dict[str, str]] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(";", 1)
        mac = parts[0].strip().upper()
        if not mac:
            continue
        name = parts[1].strip() if len(parts) > 1 and parts[1].strip() else mac
        devices.append({"mac": mac, "name": name})
    return devices


def _unique_id_for(devices: list[dict[str, str]]) -> str:
    return "_".join(sorted(d["mac"] for d in devices))


class PlantPulseConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle initial configuration."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            devices = parse_devices(user_input[CONF_DEVICES])
            if not devices:
                errors["base"] = "no_devices"
            else:
                await self.async_set_unique_id(_unique_id_for(devices))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="PlantPulse",
                    data={CONF_DEVICES: devices},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_DEVICES, default=DEFAULT_DEVICES): str}
            ),
            errors=errors,
        )
