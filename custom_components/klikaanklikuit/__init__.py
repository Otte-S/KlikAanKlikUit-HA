"""The KlikAanKlikUit (ICS-2000) integration."""
from __future__ import annotations

import logging

from ics2000_python.Core import CoreException, Hub

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_MAC, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.typing import ConfigType

from datetime import timedelta

from .const import (
    CONF_LOCAL_IP,
    CONF_SCAN_INTERVAL,
    CONF_SLEEP,
    CONF_TRIES,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MANUFACTURER,
    MODEL_HUB,
)
from .coordinator import Ics2000Coordinator, fetch_device_types
from .discovery import discover_hubs

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.LIGHT,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
]

# How often to broadcast for hubs on the network. Kept infrequent so it never
# spams the LAN; the whole point is a one-off "found it" prompt, not polling.
DISCOVERY_INTERVAL = timedelta(minutes=30)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Start periodic local discovery for ICS-2000 hubs."""

    async def _scan(_now=None) -> None:
        hubs = await hass.async_add_executor_job(discover_hubs)
        for hub in hubs:
            hass.async_create_task(
                hass.config_entries.flow.async_init(
                    DOMAIN,
                    context={"source": "integration_discovery"},
                    data={"ip": hub["ip"], "mac": hub.get("mac", "")},
                )
            )

    # One scan shortly after start, then on an interval.
    await _scan()
    async_track_time_interval(hass, _scan, DISCOVERY_INTERVAL)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ICS2000 from a config entry."""

    def _create_hub() -> Hub:
        # Hub.__init__ logs in, pulls the device list AND does a 10s-max UDP
        # broadcast to find the hub's local IP. All blocking - must run here,
        # in the executor, never on the event loop.
        return Hub(
            entry.data[CONF_MAC],
            entry.data[CONF_EMAIL],
            entry.data[CONF_PASSWORD],
        )

    try:
        hub = await hass.async_add_executor_job(_create_hub)
    except CoreException as err:
        raise ConfigEntryNotReady(f"Could not connect to ICS2000 hub: {err}") from err

    if not hub.connected:
        raise ConfigEntryNotReady("ICS2000 hub reported not connected")

    # If the user pinned a local IP, use it - the auto broadcast in Hub.__init__
    # can fail across VLANs/subnets. With an IP set, the library sends commands
    # over local UDP instead of the cloud.
    local_ip = entry.options.get(CONF_LOCAL_IP) or entry.data.get(CONF_LOCAL_IP)
    if local_ip:
        hub.ip_address = local_ip

    if hub.ip_address:
        _LOGGER.info(
            "KlikAanKlikUit hub found locally at %s - commands go over local UDP",
            hub.ip_address,
        )
    else:
        _LOGGER.warning(
            "KlikAanKlikUit hub not found on the local network - commands will "
            "fall back to the cloud. Set a local IP in the integration options "
            "to force local control."
        )

    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    coordinator = Ics2000Coordinator(hass, entry, hub, scan_interval)
    await coordinator.async_config_entry_first_refresh()

    # Recover each device's real device_type so platforms can classify
    # switches/dimmers/gongs/doorbells that the library couldn't.
    device_types = await hass.async_add_executor_job(fetch_device_types, hub)

    # Register the hub itself as a device so every KAKU device can hang under
    # it (via_device) in the device tree, instead of floating loose.
    hub_identifier = (DOMAIN, entry.entry_id)
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={hub_identifier},
        manufacturer=MANUFACTURER,
        model=MODEL_HUB,
        name=f"KlikAanKlikUit hub ({entry.data[CONF_MAC]})",
    )

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "hub": hub,
        "coordinator": coordinator,
        "tries": entry.options.get(CONF_TRIES, 1),
        "sleep": entry.options.get(CONF_SLEEP, 3),
        "hub_identifier": hub_identifier,
        "device_types": device_types,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_update_options))
    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when options (tries/sleep/scan interval) change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
