"""Operational command buttons."""
import json
from homeassistant.exceptions import HomeAssistantError
from homeassistant.components.button import ButtonEntity
from homeassistant.components import mqtt
from .const import DOMAIN, CONF_PREFIX, CONF_NAME

BUTTONS = [
    ("3 · Cancella notifica", "notify/dismiss", "", "mdi:bell-cancel"),
    ("3 · Invia ora", "send_saved_notification", "", "mdi:send"),
    ("2 · App successiva", "apps/next", "", "mdi:skip-next"),
    ("2 · App precedente", "apps/previous", "", "mdi:skip-previous"),
    ("1 · Mostra orologio", "apps/switch", "Time", "mdi:clock-outline"),
    ("5 · Aggiorna schermata MQTT", "screen/get", "", "mdi:monitor-screenshot"),
    ("4 · Ferma radio", "audio/stop", '{"group":"radio"}', "mdi:radio-off"),

]
TRANSLATION_KEYS = {"notify/dismiss": "dismiss_notification", "send_saved_notification": "send_notification", "apps/next": "next_app", "apps/previous": "previous_app", "apps/switch": "show_clock", "screen/get": "refresh_screen", "audio/stop": "stop_radio"}
async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([AwtrixButton(hass, entry, hass.data[DOMAIN][entry.entry_id], *spec) for spec in BUTTONS])
class AwtrixButton(ButtonEntity):
    _attr_has_entity_name = True
    def __init__(self, hass, entry, device, name, command, payload, icon):
        self.hass, self.entry, self.device = hass, entry, device
        self.command, self.payload = command, payload
        self._attr_translation_key, self._attr_icon = TRANSLATION_KEYS[command], icon
        self._attr_unique_id = f"{entry.entry_id}_button_{command.replace('/', '_')}"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}, "name": entry.data[CONF_NAME], "manufacturer": "Ulanzi / AWTRIX NG"}
    @property
    def available(self):
        return True
    async def async_press(self):
        if self.command == "send_saved_notification":
            message = self.device.get("notification_text", "").strip()
            if not message:
                raise HomeAssistantError("Scrivi prima il messaggio nel campo Invia notifica")
            duration = self.device.get("notification_duration", 10)
            payload = {"text": message, "durationMs": int(duration) * 1000}
            sound = self.device.get("notification_sound", "").strip()
            scroll = self.device.get("notification_scroll", "Predefinito")
            if sound:
                payload["sound"] = sound
            if scroll != "Predefinito":
                payload["scroll"] = scroll
            icon = self.device.get("notification_icon", "").strip()
            color = self.device.get("notification_color", "#FFFFFF")
            if icon:
                payload["icon"] = icon
            if color:
                payload["textColor"] = color
            await mqtt.async_publish(
                self.hass,
                f"{self.entry.data[CONF_PREFIX]}/cmd/notify",
                json.dumps(payload, ensure_ascii=False),
                qos=0,
                retain=False,
            )
            return
        http = self.device.get("http")
        if http:
            if self.command == "screen/get":
                await http.request("GET", "/api/v1/display/screen")
                return
            if self.command in ("apps/next", "apps/previous"):
                await http.request("POST", "/api/v1/" + self.command)
                return
            if self.command == "apps/switch":
                await http.request("PUT", "/api/v1/apps/active", {"name": self.payload, "fast": True})
                return
            if self.command == "audio/stop":
                await http.request("POST", "/api/v1/audio/stop", {"group": "radio"})
                return
        await mqtt.async_publish(self.hass, f"{self.entry.data[CONF_PREFIX]}/cmd/{self.command}", self.payload, qos=0, retain=False)
