"""DataUpdateCoordinator for the KlikAanKlikUit (ICS-2000) integration.

The ics2000_python library exposes Hub.get_device_status(entity_id), which
polls trustsmartcloud2.com for the last known status of a device (as reported
by the Trust app, Zigbee devices, or commands sent through the hub itself).

Note this is NOT live feedback from the physical device: classic KlikAanKlikUit
433MHz devices are one-way RF, so a remote that talks directly to a receiver
(bypassing the ICS2000 hub) will never show up here. Only state changes the
ICS2000 cloud actually knows about are visible through this polling.
"""
from __future__ import annotations

import logging
from datetime import timedelta

from ics2000_python.Core import CoreException, Hub
from ics2000_python.Cryptographer import decrypt

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def fetch_device_types(hub: Hub) -> dict[int, int]:
    """Return {device_id: device_type} by re-reading the sync endpoint.

    The library discards device_type for devices it can't classify, so we
    re-fetch it ourselves. Blocking (HTTP + decrypt) - call via the executor.
    Accesses a few library internals that have no public accessor; degrades to
    an empty dict on any error so classification just falls back to defaults.
    """
    import json

    import requests

    result: dict[int, int] = {}
    try:
        url = f"{Hub.base_url}/gateway.php"
        params = {
            "action": "sync",
            "email": hub._email,  # noqa: SLF001
            "mac": hub.mac.replace(":", ""),
            "password_hash": hub._password,  # noqa: SLF001
            "home_id": hub._homeId,  # noqa: SLF001
        }
        resp = requests.get(url, params=params, timeout=15)
        for device in resp.json():
            try:
                data = json.loads(decrypt(device["data"], hub.aes))
                module = data.get("module", {})
                if "id" in module and "device" in module:
                    result[module["id"]] = module["device"]
            except Exception:  # noqa: BLE001
                continue
    except Exception as err:  # noqa: BLE001
        _LOGGER.warning("Could not fetch device types, using fallbacks: %s", err)
    return result


class Ics2000Coordinator(DataUpdateCoordinator[dict[int, list]]):
    """Polls the ICS2000 cloud for the status of every known device."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        hub: Hub,
        scan_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=max(scan_interval, 5)),
        )
        self.hub = hub
        self.entry = entry

    async def _async_update_data(self) -> dict[int, list]:
        try:
            return await self.hass.async_add_executor_job(self._poll_all)
        except CoreException as err:
            raise UpdateFailed(f"Could not reach ICS2000 cloud: {err}") from err

    def _poll_all(self) -> dict[int, list]:
        """Blocking: fetch status for every device. Runs in the executor."""
        statuses: dict[int, list] = {}
        for device in self.hub.devices:
            device_id = device.id
            try:
                statuses[device_id] = self.hub.get_device_status(device_id)
            except Exception as err:  # noqa: BLE001 - one bad device shouldn't kill the poll
                _LOGGER.debug(
                    "Could not fetch status for %s (%s): %s", device.name, device_id, err
                )
                statuses[device_id] = []
        return statuses

    async def async_refresh_device_list(self) -> None:
        """Re-sync the device list from the cloud (new/removed devices).

        Not called automatically - devices added in the Trust app after setup
        won't appear until Home Assistant is restarted or this is triggered,
        since entities are only created once at platform setup.
        """
        await self.hass.async_add_executor_job(self.hub.pull_devices)
