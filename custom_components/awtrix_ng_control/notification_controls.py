"""Persistent notification composition controls (local integration state)."""
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.components.select import SelectEntity
from homeassistant.components.text import TextEntity, TextMode
from .const import DOMAIN, CONF_NAME


def _device_info(entry):
    return {"identifiers": {(DOMAIN, entry.entry_id)}, "name": entry.data[CONF_NAME], "manufacturer": "Ulanzi / AWTRIX NG"}


class NotificationDuration(NumberEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "notification_duration"
    _attr_icon = "mdi:timer-outline"
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 1
    _attr_native_max_value = 600
    _attr_native_step = 1

    def __init__(self, entry, device):
        self.device = device
        self._attr_unique_id = f"{entry.entry_id}_notification_duration"
        self._attr_device_info = _device_info(entry)

    @property
    def native_value(self):
        return self.device.get("notification_duration", 10)

    async def async_set_native_value(self, value):
        self.device["notification_duration"] = int(value)
        self.async_write_ha_state()


class NotificationScroll(SelectEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "notification_scroll"
    _attr_icon = "mdi:format-text-wrapping-wrap"
    _attr_options = ["Predefinito", "static", "wrap", "loop", "bounce"]

    def __init__(self, entry, device):
        self.device = device
        self._attr_unique_id = f"{entry.entry_id}_notification_scroll"
        self._attr_device_info = _device_info(entry)

    @property
    def current_option(self):
        return self.device.get("notification_scroll", "Predefinito")

    async def async_select_option(self, option):
        if option not in self.options:
            raise ValueError("Modalità di scorrimento non valida")
        self.device["notification_scroll"] = option
        self.async_write_ha_state()


class NotificationSound(TextEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "notification_sound"
    _attr_icon = "mdi:music-note"
    _attr_native_min = 0
    _attr_native_max = 80
    _attr_mode = TextMode.TEXT

    def __init__(self, entry, device):
        self.device = device
        self._attr_unique_id = f"{entry.entry_id}_notification_sound"
        self._attr_device_info = _device_info(entry)

    @property
    def native_value(self):
        return self.device.get("notification_sound", "")

    async def async_set_value(self, value):
        self.device["notification_sound"] = value.strip()
        self.async_write_ha_state()
