"""Editable controls: notification, app, icon and colors."""
import json
from homeassistant.components.text import TextEntity, TextMode
from homeassistant.components import mqtt
from homeassistant.core import callback
from .const import DOMAIN, CONF_PREFIX, CONF_NAME

FIELDS = [
    ("notification", "3 · Testo notifica", "mdi:message-text", 255),
    ("icon", "3 · Icona notifica", "mdi:image", 80),
    ("color", "3 · Colore notifica", "mdi:palette", 7),
]

async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([ControlText(hass, entry, hass.data[DOMAIN][entry.entry_id], *item) for item in FIELDS])
    from .notification_controls import NotificationSound
    async_add_entities([NotificationSound(entry, hass.data[DOMAIN][entry.entry_id])])

class ControlText(TextEntity):
    _attr_has_entity_name = True
    _attr_native_min = 0
    _attr_mode = TextMode.TEXT
    def __init__(self, hass, entry, device, key, name, icon, max_length):
        self.hass, self.entry, self.device, self.key = hass, entry, device, key
        self._attr_translation_key, self._attr_icon = f"notification_{key}" if key != "notification" else "notification_text", icon
        self._attr_native_max = max_length
        self._attr_unique_id = f"{entry.entry_id}_text_{key}" if key != "notification" else f"{entry.entry_id}_notification_text"
        self._value = ""
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}, "name": entry.data[CONF_NAME], "manufacturer": "Ulanzi / AWTRIX NG"}
    @property
    def available(self):
        return True
    @property
    def native_value(self):
        if self.key == "icon":
            return self.device.get("notification_icon", "")
        if self.key == "color":
            return self.device.get("notification_color", "#FFFFFF")
        if self.key == "app":
            # Keep the manual text control synchronized with the current app.
            # Previously it always showed an empty value until the user typed.
            active = self.device["state"].get("apps/active")
            if isinstance(active, str) and active.strip():
                return active
            info = self.device["state"].get("device", {})
            if isinstance(info, dict):
                active = info.get("currentApp") or info.get("app")
                if isinstance(active, str) and active.strip():
                    return active
        return self._value
    async def async_set_value(self, value):
        prefix = self.entry.data[CONF_PREFIX]
        if self.key == "notification":
            # Il campo di testo salva soltanto il messaggio.
            # L'invio avviene esclusivamente premendo "Invia notifica ora".
            self.device["notification_text"] = value
        elif self.key == "app":
            if not value.strip():
                return
            http = self.device.get('http')
            if http and http.endpoint_ok['apps']:
                await http.request('PUT', '/api/v1/apps/active', {'name': value.strip(), 'fast': True})
            else:
                await mqtt.async_publish(self.hass, f'{prefix}/cmd/apps/switch', value.strip(), qos=0, retain=False)
            self.device['state']['apps/active'] = value.strip()
        elif self.key == "icon":
            self.device["notification_icon"] = value.strip()
        else:
            if len(value) != 7 or not value.startswith("#") or any(c not in "0123456789ABCDEFabcdef" for c in value[1:]):
                raise ValueError("Il colore deve essere in formato #RRGGBB")
            self.device["notification_color"] = value
        self._value = value
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        if self.key == "app":
            self.device["listeners"].add(self._update)
            self.async_on_remove(lambda: self.device["listeners"].discard(self._update))

    @callback
    def _update(self):
        self.async_write_ha_state()
