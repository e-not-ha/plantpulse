"""Data coordinator for PlantPulse."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from bleak import BleakClient
from bleak.exc import BleakError

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import CONF_DEVICES, DOMAIN

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(minutes=5)

# UUID характеристики, из которой читается payload.
# Уточните под ваш реальный MCLH-09.
CHARACTERISTIC_UUID = "0000fff4-0000-1000-8000-00805f9b34fb"

# Если устройство падает N раз подряд — пропускаем его на время
MAX_CONSECUTIVE_ERRORS = 5
FAILURE_COOLDOWN_SEC = 300


def decode_payload(payload: bytes) -> dict[str, float]:
    """Decode raw BLE payload.

    ВНИМАНИЕ: смещения и масштабы подобраны по аналогии с типичными
    MCLH-09. Проверьте их на реальном устройстве.
    """
    if len(payload) < 7:
        raise ValueError(f"Payload too short: {len(payload)} bytes")

    temperature = int.from_bytes(payload[0:2], "little", signed=True) / 10.0
    humidity = int.from_bytes(payload[2:4], "little", signed=False) / 10.0
    illuminance = int.from_bytes(payload[4:6], "little", signed=False)
    battery = payload[6]

    return {
        "temperature": temperature,
        "humidity": humidity,
        "illuminance": illuminance,
        "battery": battery,
    }


class PlantPulseCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Coordinator that polls all configured BLE devices in parallel."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="plant_pulse",
            update_interval=UPDATE_INTERVAL,
        )
        self._devices: list[dict[str, str]] = entry.data.get(CONF_DEVICES, [])
        self._consecutive_errors: dict[str, int] = {d["mac"]: 0 for d in self._devices}
        self._cooldown_until: dict[str, float] = {d["mac"]: 0.0 for d in self._devices}

    async def _read_device(self, mac: str) -> dict[str, float]:
        """Read one device and decode payload."""
        async with BleakClient(mac, timeout=20.0) as client:
            payload = await client.read_gatt_char(CHARACTERISTIC_UUID)
            return decode_payload(bytes(payload))

    def _should_skip(self, mac: str) -> bool:
        loop_time = self.hass.loop.time()
        return loop_time < self._cooldown_until.get(mac, 0.0)

    def _mark_failure(self, mac: str) -> None:
        self._consecutive_errors[mac] = self._consecutive_errors.get(mac, 0) + 1
        if self._consecutive_errors[mac] >= MAX_CONSECUTIVE_ERRORS:
            self._cooldown_until[mac] = self.hass.loop.time() + FAILURE_COOLDOWN_SEC
            _LOGGER.warning(
                "Device %s disabled for %s s after %s errors",
                mac,
                FAILURE_COOLDOWN_SEC,
                self._consecutive_errors[mac],
            )

    def _mark_success(self, mac: str) -> None:
        self._consecutive_errors[mac] = 0
        self._cooldown_until[mac] = 0.0

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        if not self._devices:
            return {}

        active = [d for d in self._devices if not self._should_skip(d["mac"])]
        tasks = [self._read_device(d["mac"]) for d in active]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        data: dict[str, dict[str, Any]] = {}
        errors: list[str] = []

        # Сохраняем последние успешные значения для пропущенных устройств.
        for d in self._devices:
            mac = d["mac"]
            if self._should_skip(mac) and self.data and mac in self.data:
                data[mac] = self.data[mac]

        for device, result in zip(active, results):
            mac = device["mac"]
            if isinstance(result, (Exception, BleakError)):
                self._mark_failure(mac)
                errors.append(f"{mac}: {result}")
                if self.data and mac in self.data:
                    data[mac] = self.data[mac]
                continue
            self._mark_success(mac)
            data[mac] = result

        if not data and errors:
            raise UpdateFailed(f"All devices failed: {errors}")

        return data
