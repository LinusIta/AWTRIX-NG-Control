"""Native Home Assistant notify entities for AWTRIX NG."""
from __future__ import annotations

import json
from homeassistant.components import mqtt
from homeassistant.components.notify import NotifyEntity, NotifyEntityFeature
from .const import DOMAIN, CONF_PREFIX, CONF_NAME
from .notification_payload import title_message_layout


async def async_setup_entry(hass, entry, async_add_entities):
    device = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AwtrixNotify(entry, device)])


class AwtrixNotify(NotifyEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "notifications"
    _attr_supported_features = NotifyEntityFeature.TITLE

    def __init__(self, entry, device):
        self._entry = entry
        self._device = device
        self._attr_unique_id = f"{entry.entry_id}_native_notify"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.data[CONF_NAME],
            "manufacturer": "Ulanzi / AWTRIX NG",
        }

    @property
    def available(self):
        return self._device["available"]

    async def async_send_message(self, message: str, title: str | None = None) -> None:
        payload = ({"layout": title_message_layout(title, message)} if title else {"text": message})
        topic = f"{self._entry.data[CONF_PREFIX]}/cmd/notify"
        await mqtt.async_publish(self.hass, topic, json.dumps(payload, ensure_ascii=False), qos=0, retain=False)
