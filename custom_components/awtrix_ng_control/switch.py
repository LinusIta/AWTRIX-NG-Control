"""Auto brightness and rotation controls."""
import json
from homeassistant.components.switch import SwitchEntity
from homeassistant.components import mqtt
from homeassistant.core import callback
from .const import DOMAIN, CONF_PREFIX, CONF_NAME
FIELDS = [
    ("1 · Luminosità automatica", "autoBrightness", "mdi:brightness-auto"),
    ("2 · Rotazione automatica app", "autoTransition", "mdi:autorenew"),
]
TRANSLATION_KEYS = {"autoBrightness": "auto_brightness", "autoTransition": "auto_transition"}
async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([SettingSwitch(hass, entry, hass.data[DOMAIN][entry.entry_id], *p) for p in FIELDS])
    from .extra_controls import DisplayPower
    async_add_entities([DisplayPower(entry, hass.data[DOMAIN][entry.entry_id])])
class SettingSwitch(SwitchEntity):
    _attr_has_entity_name = True
    def __init__(self, hass, entry, device, name, key, icon):
        self.hass, self.entry, self.device, self.key = hass, entry, device, key
        self._attr_translation_key, self._attr_icon = TRANSLATION_KEYS[key], icon
        self._attr_unique_id = f"{entry.entry_id}_auto_brightness" if key == "autoBrightness" else f"{entry.entry_id}_{key}"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}, "name": entry.data[CONF_NAME], "manufacturer": "Ulanzi / AWTRIX NG"}
    @property
    def available(self): return True
    @property
    def is_on(self):
        settings = self.device["state"].get("settings", {})
        return settings.get(self.key) if isinstance(settings, dict) else None
    async def async_turn_on(self, **kwargs): await self._set(True)
    async def async_turn_off(self, **kwargs): await self._set(False)
    async def _set(self, value):
        await mqtt.async_publish(self.hass, f"{self.entry.data[CONF_PREFIX]}/cmd/settings", json.dumps({self.key: value}), qos=0, retain=False)
    async def async_added_to_hass(self):
        self.device["listeners"].add(self._update)
        self.async_on_remove(lambda: self.device["listeners"].discard(self._update))
    @callback
    def _update(self): self.async_write_ha_state()
