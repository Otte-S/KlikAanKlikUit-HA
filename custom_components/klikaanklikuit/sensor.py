"""Sensor platform for KlikAanKlikUit: temperature/humidity sensors.

Devices the library can't classify (unrecognised device_type, e.g. a doorbell
receiver, gong or garage switch) are handled in light.py as switchable lights,
not here. Their raw cloud status is still available via the Diagnostics
download for debugging.
"""
from __future__ import annotations

import logging

from ics2000_python.Devices import TemperatureHumiditySensor

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import Ics2000Coordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator: Ics2000Coordinator = data["coordinator"]
    hub_identifier = data["hub_identifier"]

    entities: list[SensorEntity] = []
    for device in coordinator.hub.devices:
        if isinstance(device, TemperatureHumiditySensor):
            entities.append(Ics2000TemperatureSensor(coordinator, device, hub_identifier))
            entities.append(Ics2000HumiditySensor(coordinator, device, hub_identifier))
        # Unknown-type devices are handled by light.py as switchable lights.
        # Their raw cloud status is still available via the Diagnostics
        # download (Settings > Devices & Services > ... > Download diagnostics)
        # for debugging things like a doorbell's function indices.

    async_add_entities(entities)


class Ics2000SensorBase(CoordinatorEntity[Ics2000Coordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: Ics2000Coordinator, device, hub_identifier: tuple[str, str]
    ) -> None:
        super().__init__(coordinator)
        self._device = device
        self._id = device.id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(device.id))},
            name=device.name,
            manufacturer=MANUFACTURER,
            via_device=hub_identifier,
        )

    @property
    def _status(self) -> list:
        return self.coordinator.data.get(self._id, [])


class Ics2000TemperatureSensor(Ics2000SensorBase):
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(
        self, coordinator: Ics2000Coordinator, device, hub_identifier: tuple[str, str]
    ) -> None:
        super().__init__(coordinator, device, hub_identifier)
        self._attr_unique_id = f"klikaanklikuit-{device.id}-temperature"
        self._attr_name = "Temperature"

    @property
    def native_value(self) -> float | None:
        status = self._status
        if len(status) < 5:
            return None
        return round(status[4] / 100.0, 2)


class Ics2000HumiditySensor(Ics2000SensorBase):
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(
        self, coordinator: Ics2000Coordinator, device, hub_identifier: tuple[str, str]
    ) -> None:
        super().__init__(coordinator, device, hub_identifier)
        self._attr_unique_id = f"klikaanklikuit-{device.id}-humidity"
        self._attr_name = "Humidity"

    @property
    def native_value(self) -> float | None:
        status = self._status
        if len(status) < 12:
            return None
        return round(status[11] / 100.0, 2)
