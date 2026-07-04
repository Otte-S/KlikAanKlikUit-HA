"""Button platform for KlikAanKlikUit gongs / chimes (device_type 13).

Gongs have no on/off in the KAKU app - you trigger them. Pressing the button
sends an on command, which is what makes the gong sound. Commands go over
local UDP when the hub IP is known, otherwise the cloud.
"""
from __future__ import annotations

import logging
import time

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MANUFACTURER
from .coordinator import Ics2000Coordinator
from .device_classifier import CATEGORY_GONG, classify

_LOGGER = logging.getLogger(__name__)


def _send_with_retries(tries: int, sleep: int, func, *args) -> None:
    for i in range(tries):
        func(*args)
        if i != tries - 1:
            time.sleep(sleep)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: Ics2000Coordinator = data["coordinator"]
    hub_identifier = data["hub_identifier"]
    device_types: dict[int, int] = data["device_types"]
    tries: int = data["tries"]
    sleep: int = data["sleep"]

    entities = [
        Ics2000GongButton(coordinator, device, tries, sleep, hub_identifier)
        for device in coordinator.hub.devices
        if classify(device, device_types.get(device.id)) == CATEGORY_GONG
    ]
    async_add_entities(entities)


class Ics2000GongButton(ButtonEntity):
    """A KlikAanKlikUit gong - press to sound it."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self,
        coordinator: Ics2000Coordinator,
        device,
        tries: int,
        sleep: int,
        hub_identifier: tuple[str, str],
    ) -> None:
        self._hub = device.hub
        self._id = device.id
        self.tries = tries
        self.sleep = sleep
        self._attr_unique_id = f"klikaanklikuit-{device.id}-gong"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(device.id))},
            name=device.name,
            manufacturer=MANUFACTURER,
            model="Gong",
            via_device=hub_identifier,
        )

    async def async_press(self) -> None:
        await self.hass.async_add_executor_job(
            _send_with_retries, self.tries, self.sleep, self._hub.turn_on, self._id
        )
