"""Brightness and app rotation interval controls."""
import json
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.core import callback
from homeassistant.components import mqtt
from .const import DOMAIN, CONF_PREFIX, CONF_NAME
FIELDS=[("1 · Luminosità", "brightness", 0, 255, 1, "mdi:brightness-6"), ("2 · Durata rotazione (s)", "appDurationMs", 1, 60, 1, "mdi:timer-outline"), ("4 · Volume generale", "volume", 0, 100, 1, "mdi:volume-high"), ("4 · Volume radio", "radioVolume", 0, 100, 1, "mdi:radio"), ("4 · Volume avvisi", "alertVolume", 0, 100, 1, "mdi:bell-ring"), ("4 · Volume app", "appVolume", 0, 100, 1, "mdi:apps")]
TRANSLATION_KEYS = {"brightness": "brightness", "appDurationMs": "app_duration", "volume": "volume", "radioVolume": "radio_volume", "alertVolume": "alert_volume", "appVolume": "app_volume"}
async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([SettingNumber(hass, entry, hass.data[DOMAIN][entry.entry_id], *f) for f in FIELDS])
    from .notification_controls import NotificationDuration
    async_add_entities([NotificationDuration(entry, hass.data[DOMAIN][entry.entry_id])])
class SettingNumber(NumberEntity):
    _attr_has_entity_name = True
    _attr_mode = NumberMode.SLIDER
    def __init__(self, hass, entry, device, label, key, mini, maxi, step, icon):
        self.hass, self.entry, self.device, self.key = hass, entry, device, key
        self._attr_translation_key, self._attr_icon = TRANSLATION_KEYS[key], icon
        self._attr_native_min_value, self._attr_native_max_value, self._attr_native_step = mini, maxi, step
        self._attr_unique_id = f"{entry.entry_id}_brightness_control" if key == "brightness" else f"{entry.entry_id}_{key}"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}, "name": entry.data[CONF_NAME], "manufacturer": "Ulanzi / AWTRIX NG"}
    @property
    def available(self): return True
    @property
    def native_value(self):
        settings = self.device["state"].get("settings", {})
        if not isinstance(settings, dict): return None
        value = settings.get(self.key)
        return value / 1000 if self.key == "appDurationMs" and isinstance(value, (int, float)) else value
    async def async_set_native_value(self, value):
        payload = {self.key: int(value * 1000) if self.key == "appDurationMs" else int(value)}
        if self.key == "brightness": payload["autoBrightness"] = False
        await mqtt.async_publish(self.hass, f"{self.entry.data[CONF_PREFIX]}/cmd/settings", json.dumps(payload), qos=0, retain=False)
    async def async_added_to_hass(self):
        self.device["listeners"].add(self._update)
        self.async_on_remove(lambda: self.device["listeners"].discard(self._update))
    @callback
    def _update(self): self.async_write_ha_state()
