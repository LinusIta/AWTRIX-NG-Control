"""State entities derived from retained AWTRIX NG MQTT state topics."""
import json
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import callback
from .const import DOMAIN, CONF_NAME, CONF_PREFIX

FIELDS = [
    ("Active App", "apps/active"),
    ("Device Info", "device"),
    ("Settings", "settings"),
    ("Ultimo errore", "last_error"),
]

async def async_setup_entry(hass, entry, async_add_entities):
    device = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AwtrixSensor(entry, device, label, path) for label, path in FIELDS] + [AwtrixHttpDiagnostic(entry, device)])

class AwtrixSensor(SensorEntity):
    _attr_has_entity_name = True
    def __init__(self, entry, device, label, path):
        self._entry, self._device, self._path = entry, device, path
        self._attr_translation_key = {"apps/active": "active_app", "device": "device_info"}.get(path, path)
        self._attr_unique_id = f"{entry.entry_id}_{path.replace('/', '_')}"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}, "name": entry.data[CONF_NAME], "manufacturer": "Ulanzi / AWTRIX NG", "model": "AWTRIX NG"}
    @property
    def available(self):
        return self._device["available"]
    @property
    def native_value(self):
        data = self._device["state"].get(self._path)
        if isinstance(data, dict):
            return "Received"
        if data is None:
            return None
        return str(data)[:255]
    @property
    def extra_state_attributes(self):
        data = self._device["state"].get(self._path)
        return data if isinstance(data, dict) else None
    async def async_added_to_hass(self):
        self._device["listeners"].add(self._update)
        self.async_on_remove(lambda: self._device["listeners"].discard(self._update))
    @callback
    def _update(self):
        self.async_write_ha_state()


class AwtrixHttpDiagnostic(SensorEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "http_diagnostic"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["not_configured", "unreachable", "partial", "connected"]
    _attr_icon = "mdi:lan-check"

    def __init__(self, entry, device):
        self._entry, self._device = entry, device
        self._attr_unique_id = f"{entry.entry_id}_http_diagnostic"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}, "name": entry.data[CONF_NAME], "manufacturer": "Ulanzi / AWTRIX NG"}

    @property
    def available(self):
        return True

    @property
    def native_value(self):
        http = self._device.get('http')
        if http is None:
            return 'not_configured'
        if not http.connected:
            return 'unreachable'
        if not http.endpoint_ok.get('apps') or not http.endpoint_ok.get('stations'):
            return 'partial'
        return 'connected'

    @property
    def extra_state_attributes(self):
        http = self._device.get('http')
        if http is None:
            return {'host': self._entry.options.get('host', ''), 'configured': False}
        return {'host': http.host, 'endpoints': dict(http.endpoint_ok), 'errors': dict(http.endpoint_errors), 'applications': list(http.app_names), 'stations': list(http.station_names)}

    async def async_added_to_hass(self):
        self._device['listeners'].add(self._update)
        self.async_on_remove(lambda: self._device['listeners'].discard(self._update))

    @callback
    def _update(self):
        self.async_write_ha_state()
