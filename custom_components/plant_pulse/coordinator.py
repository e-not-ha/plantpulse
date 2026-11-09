"""Data update coordinator for PlantPulse."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from bleak import BleakClient
from bleak_retry_connector import establish_connection

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_ERROR_COUNT,
    ATTR_LAST_UPDATE,
    CONF_CHAR_UUID,
    CONF_DEVICES,
    CONF_MAX_RETRIES,
    CONF_RAW_SOIL,
    CONF_SCAN_INTERVAL,
    CONF_SERVICE_UUID,
    DEFAULT_MAX_RETRIES,
    DEFAULT_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


def decode_payload(
    data: bytes, raw_soil: bool = False
) -> dict[str, float | int]:
    """Decode raw BLE payload into sensor values.

    Формат предполагается little-endian, 16-bit поля.
    При необходимости скорректируй offsets/scale под реальный MCLH-09.
    """
    if len(data) < 10:
        raise ValueError("Payload too short")

    temperature = int.from_bytes(data[0:2], "little") / 10.0
    humidity = int.from_bytes(data[2:4], "little") / 10.0
    soil_raw = int.from_bytes(data[4:6], "little")
    light = int.from_bytes(data[6:8], "little")
    battery = int.from_bytes(data[8:10], "little")

    soil = soil_raw if raw_soil else max(0.0, min(100.0, soil_raw / 10.0))

    return {
        "temperature": temperature,
        "humidity": humidity,
        "soil_moisture": soil,
        "light": light,
        "battery": battery,
    }


class PlantPulseCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that polls BLE plant sensors."""

    def __init__(self, hass: HomeAssistant, entry) -> None:
        self._entry = entry
        self._devices = entry.data.get(CONF_DEVICES, [])
        self._scan_interval = timedelta(
            seconds=entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        )
        self._max_retries = entry.data.get(CONF_MAX_RETRIES, DEFAULT_MAX_RETRIES)
        self._raw_soil = entry.data.get(CONF_RAW_SOIL, False)
        self._service_uuid = entry.data.get(CONF_SERVICE_UUID)
        self._char_uuid = entry.data.get(CONF_CHAR_UUID)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN := "plant_pulse",
            update_interval=self._scan_interval,
        )

        self._error_counts: dict[str, int] = {}
        self._last_update: dict[str, Any] = {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from all devices."""
        result: dict[str, Any] = {}
        for device in self._devices:
            mac = device["mac"]
            try:
                data = await self._read_device(mac)
                values = decode_payload(data, self._raw_soil)
                self._error_counts[mac] = 0
                self._last_update[mac] = dt_util.utcnow()
                result[mac] = {
                    **values,
                    ATTR_ERROR_COUNT: 0,
                    ATTR_LAST_UPDATE: self._last_update[mac],
                    "available": True,
                }
            except Exception as err:
                count = self._error_counts.get(mac, 0) + 1
                self._error_counts[mac] = count
                _LOGGER.warning(
                    "BLE read failed for %s (attempt %s/%s): %s",
                    mac, count, self._max_retries, err
                )
                available = count < self._max_retries
                result[mac] = {
                    ATTR_ERROR_COUNT: count,
                    ATTR_LAST_UPDATE: self._last_update.get(mac),
                    "available": available,
                }
        return result

    async def _read_device(self, mac: str) -> bytes:
        """Read characteristic with retry/backoff."""
        delay = 1
        last_err = None
        for attempt in range(1, self._max_retries + 1):
            try:
                client = await establish_connection(
                    BleakClient,
                    self.hass.bluetooth,
                    mac,
                    used_discovery=None,
                )
                try:
                    return await client.read_gatt_char(self._char_uuid)
                finally:
                    await client.disconnect()
            except Exception as err:
                last_err = err
                _LOGGER.debug(
                    "Attempt %s for %s failed: %s", attempt, mac, err
                )
                await asyncio.sleep(delay)
                delay *= 2
        raise last_err
