"""Maps ICS2000 device_type numbers to a handling category.

The ics2000_python library only recognises a handful of device types and
collapses everything else to a bare Device object, discarding the type. We
re-fetch the real device_type (see coordinator.fetch_device_types) and classify
here, so switches/dimmers/gongs/inputs each become the right kind of entity.

Type numbers below were derived from a real hub's diagnostics, matched against
the status array shape. They are best-effort, not from official docs:
  1  LAMP            on/off            status [on]
  2  DIMMER          dim               status [on, level]
  3  OPEN_CLOSE      on/off
  12 ZIGBEE          on/off
  13 GONG            trigger           status [x]        -> button
  21 DOORBELL        input             status [x]        -> binary_sensor
  24 DIMMABLE_LAMP   dim
  25 WALL_SWITCH     input             status [x]        -> binary_sensor
  28 (garage switch) on/off           status [on]
  34 (dimmable lamp) dim              status [on, level, ...]
  41 KAKUSCHAKELAAR  on/off
  46 TEMP_HUMIDITY   sensor
  53 (IR panel)      on/off           status [on, ...]
"""
from __future__ import annotations

from ics2000_python.Devices import Dimmer, Light, TemperatureHumiditySensor

CATEGORY_LIGHT = "light"
CATEGORY_DIMMER = "dimmer"
CATEGORY_TEMP_HUMIDITY = "temp_humidity"
CATEGORY_GONG = "gong"
CATEGORY_INPUT = "input"

LIGHT_TYPES = {1, 3, 12, 28, 41, 53}
DIMMER_TYPES = {2, 24, 34}
TEMP_HUMIDITY_TYPES = {46}
GONG_TYPES = {13}
INPUT_TYPES = {21, 25}


def classify(device, device_type: int | None) -> str:
    """Return the handling category for a device.

    Prefers the numeric device_type (accurate, covers unknown-to-library
    devices); falls back to the library's Python class when the type is
    missing. Anything still unrecognised defaults to an on/off light so it
    stays controllable rather than disappearing.
    """
    if device_type in DIMMER_TYPES or isinstance(device, Dimmer):
        return CATEGORY_DIMMER
    if device_type in TEMP_HUMIDITY_TYPES or isinstance(device, TemperatureHumiditySensor):
        return CATEGORY_TEMP_HUMIDITY
    if device_type in GONG_TYPES:
        return CATEGORY_GONG
    if device_type in INPUT_TYPES:
        return CATEGORY_INPUT
    if device_type in LIGHT_TYPES or isinstance(device, Light):
        return CATEGORY_LIGHT
    return CATEGORY_LIGHT
