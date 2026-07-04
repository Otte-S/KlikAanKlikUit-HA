"""Diagnostics support for KlikAanKlikUit.

Download via Settings > Devices & Services > KlikAanKlikUit > ... > Download
diagnostics. Dumps every device with its ICS2000 device_type number and raw
status - the fastest way to identify special devices (doorbell, gong,
wall-switch input) for classification. Email/password/mac are redacted.
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import fetch_device_types

_LOGGER = logging.getLogger(__name__)

REDACTED = "***REDACTED***"
_REDACT_KEYS = {"password", "email", "mac"}


def _redact(data: dict) -> dict:
    return {k: (REDACTED if k in _REDACT_KEYS else v) for k, v in data.items()}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]

    raw_types = data.get("device_types") or await hass.async_add_executor_job(
        fetch_device_types, coordinator.hub
    )

    return {
        "entry_data": _redact(dict(entry.data)),
        "entry_options": dict(entry.options),
        "devices": [
            {
                "id": device.id,
                "name": device.name,
                "python_class": type(device).__name__,
                "device_type": raw_types.get(device.id),
                "status": coordinator.data.get(device.id, []),
            }
            for device in coordinator.hub.devices
        ],
    }
