"""Binary sensor platform for KlikAanKlikUit input devices.

Covers the doorbell (device_type 21) and wall-switch transmitter
(device_type 25) - devices that have no on/off in the KAKU app because they
are inputs, not actuators. Their state is read from the cloud poll.

IMPORTANT - this may not do anything useful for the doorbell. Classic KAKU is
one-way 433MHz and the cloud only stores state the hub knows about. Whether a
doorbell press actually shows up here (status flipping 0 -> 1) and stays set
long enough to be caught by a poll is unverified - it depends entirely on the
hardware. If the state never changes when the bell rings, no software can fix
that; the press simply isn't reaching the cloud. Test by ringing the bell and
watching this entity (or re-downloading diagnostics).
"""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import Ics2000Coordinator
from .device_classifier import CATEGORY_INPUT, classify

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: Ics2000Coordinator = data["coordinator"]
    hub_identifier = data["hub_identifier"]
    device_types: dict[int, int] = data["device_types"]

    entities = [
        Ics2000BinarySensor(coordinator, device, hub_identifier)
        for device in coordinator.hub.devices
        if classify(device, device_types.get(device.id)) == CATEGORY_INPUT
    ]
    async_add_entities(entities)


class Ics2000BinarySensor(CoordinatorEntity[Ics2000Coordinator], BinarySensorEntity):
    """A KlikAanKlikUit input (doorbell / wall switch), read from the cloud."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self, coordinator: Ics2000Coordinator, device, hub_identifier: tuple[str, str]
    ) -> None:
        super().__init__(coordinator)
        self._device = device
        self._id = device.id
        self._attr_unique_id = f"klikaanklikuit-{device.id}-input"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(device.id))},
            name=device.name,
            manufacturer=MANUFACTURER,
            model="Input",
            via_device=hub_identifier,
        )

    @property
    def is_on(self) -> bool | None:
        status = self.coordinator.data.get(self._id, [])
        if not status:
            return None
        return status[0] == 1
