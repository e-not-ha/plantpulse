"""Config flow for PlantPulse."""

from __future__ import annotations

import re
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

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
)

MAC_RE = re.compile(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")


def parse_devices(raw: str) -> list[dict]:
    """Parse multi-line device input."""
    devices = []
    seen = set()
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split(";")]
        mac = parts[0].upper()
        if not MAC_RE.match(mac):
            raise ValueError(f"Invalid MAC address: {mac}")
        if mac in seen:
            raise ValueError(f"Duplicate MAC: {mac}")
        seen.add(mac)
        name = parts[1] if len(parts) > 1 and parts[1] else mac
        devices.append({"mac": mac, "name": name})
    if not devices:
        raise ValueError("At least one device is required")
    return devices


class PlantPulseConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PlantPulse."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                devices = parse_devices(user_input[CONF_DEVICES])
            except ValueError as err:
                errors[CONF_DEVICES] = str(err)
            else:
                return self.async_create_entry(
                    title="PlantPulse",
                    data={
                        CONF_DEVICES: devices,
                        CONF_SCAN_INTERVAL: user_input.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                        CONF_MAX_RETRIES: user_input.get(
                            CONF_MAX_RETRIES, DEFAULT_MAX_RETRIES
                        ),
                        CONF_RAW_SOIL: user_input.get(
                            CONF_RAW_SOIL, DEFAULT_RAW_SOIL
                        ),
                        CONF_SERVICE_UUID: user_input.get(
                            CONF_SERVICE_UUID, DEFAULT_SERVICE_UUID
                        ),
                        CONF_CHAR_UUID: user_input.get(
                            CONF_CHAR_UUID, DEFAULT_CHAR_UUID
                        ),
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_DEVICES): str,
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): int,
                vol.Optional(
                    CONF_MAX_RETRIES, default=DEFAULT_MAX_RETRIES
                ): int,
                vol.Optional(
                    CONF_RAW_SOIL, default=DEFAULT_RAW_SOIL
                ): bool,
                vol.Optional(
                    CONF_SERVICE_UUID, default=DEFAULT_SERVICE_UUID
                ): str,
                vol.Optional(
                    CONF_CHAR_UUID, default=DEFAULT_CHAR_UUID
                ): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return PlantPulseOptionsFlow(config_entry)


class PlantPulseOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                devices = parse_devices(user_input[CONF_DEVICES])
            except ValueError as err:
                errors[CONF_DEVICES] = str(err)
            else:
                return self.async_create_entry(
                    title="",
                    data={
                        CONF_DEVICES: devices,
                        CONF_SCAN_INTERVAL: user_input.get(
                            CONF_SCAN_INTERVAL,
                            self.config_entry.data.get(
                                CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                            ),
                        ),
                        CONF_MAX_RETRIES: user_input.get(
                            CONF_MAX_RETRIES,
                            self.config_entry.data.get(
                                CONF_MAX_RETRIES, DEFAULT_MAX_RETRIES
                            ),
                        ),
                        CONF_RAW_SOIL: user_input.get(
                            CONF_RAW_SOIL,
                            self.config_entry.data.get(
                                CONF_RAW_SOIL, DEFAULT_RAW_SOIL
                            ),
                        ),
                        CONF_SERVICE_UUID: user_input.get(
                            CONF_SERVICE_UUID,
                            self.config_entry.data.get(
                                CONF_SERVICE_UUID, DEFAULT_SERVICE_UUID
                            ),
                        ),
                        CONF_CHAR_UUID: user_input.get(
                            CONF_CHAR_UUID,
                            self.config_entry.data.get(
                                CONF_CHAR_UUID, DEFAULT_CHAR_UUID
                            ),
                        ),
                    },
                )

        current = self.config_entry.data
        devices_str = "\n".join(
            f"{d['mac']}; {d['name']}" for d in current.get(CONF_DEVICES, [])
        )

        schema = vol.Schema(
            {
                vol.Required(CONF_DEVICES, default=devices_str): str,
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=current.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): int,
                vol.Optional(
                    CONF_MAX_RETRIES,
                    default=current.get(CONF_MAX_RETRIES, DEFAULT_MAX_RETRIES),
                ): int,
                vol.Optional(
                    CONF_RAW_SOIL,
                    default=current.get(CONF_RAW_SOIL, DEFAULT_RAW_SOIL),
                ): bool,
                vol.Optional(
                    CONF_SERVICE_UUID,
                    default=current.get(CONF_SERVICE_UUID, DEFAULT_SERVICE_UUID),
                ): str,
                vol.Optional(
                    CONF_CHAR_UUID,
                    default=current.get(CONF_CHAR_UUID, DEFAULT_CHAR_UUID),
                ): str,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
        )
