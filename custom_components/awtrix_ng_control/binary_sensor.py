"""MQTT availability and physical button states."""
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import callback
from .const import DOMAIN, CONF_NAME

async def async_setup_entry(hass, entry, async_add_entities):
    device = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AwtrixBinary(entry, device, key) for key in ("availability", "left", "select", "right")])

class AwtrixBinary(BinarySensorEntity):
    _attr_has_entity_name = True
    def __init__(self, entry, device, key):
        self._device, self._key = device, key
        self._attr_translation_key = "online" if key == "availability" else f"button_{key}"
        self._attr_unique_id = f"{entry.entry_id}_binary_{key}"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}, "name": entry.data[CONF_NAME], "manufacturer": "Ulanzi / AWTRIX NG"}
    @property
    def is_on(self):
        if self._key == "availability":
            return self._device["available"]
        return str(self._device["state"].get(f"buttons/{self._key}", "0")) in ("1", "True", "true")
    @property
    def available(self):
        return True if self._key == "availability" else self._device["available"]
    async def async_added_to_hass(self):
        self._device["listeners"].add(self._update)
        self.async_on_remove(lambda: self._device["listeners"].discard(self._update))
    @callback
    def _update(self):
        self.async_write_ha_state()
