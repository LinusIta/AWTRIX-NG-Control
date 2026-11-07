"""Additional optional entities; the existing app/radio selectors are untouched."""
from __future__ import annotations
from homeassistant.components.select import SelectEntity
from homeassistant.components.switch import SwitchEntity
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from .const import DOMAIN, CONF_NAME


def _device_info(entry):
    return {"identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.data[CONF_NAME], "manufacturer": "Ulanzi / AWTRIX NG"}

class _HttpEntity:
    def __init__(self, entry, device):
        self.device = device
        self._attr_device_info = _device_info(entry)

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self.device['listeners'].add(self._changed)
        self.async_on_remove(lambda: self.device['listeners'].discard(self._changed))

    @callback
    def _changed(self):
        self.async_write_ha_state()

class DisplayPower(_HttpEntity, SwitchEntity):
    _attr_has_entity_name = True
    _attr_translation_key = 'display_power'
    _attr_icon = 'mdi:monitor'

    def __init__(self, entry, device):
        super().__init__(entry, device)
        self._attr_unique_id = f'{entry.entry_id}_display_power'

    @property
    def available(self):
        http = self.device.get('http')
        return bool(http and isinstance(http.display_info.get('power'), bool))

    @property
    def is_on(self):
        http = self.device.get('http')
        return http.display_info.get('power') if http else None

    async def _set(self, value):
        http = self.device.get('http')
        if not http: raise HomeAssistantError('HTTP not configured')
        await http.request('PATCH', '/api/v1/display', {'power': value})
        http.display_info['power'] = value
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs):
        await self._set(True)

    async def async_turn_off(self, **kwargs):
        await self._set(False)

class ClockFace(_HttpEntity, SelectEntity):
    _attr_has_entity_name = True
    _attr_translation_key = 'clock_face'
    _attr_icon = 'mdi:clock-digital'

    def __init__(self, entry, device):
        super().__init__(entry, device)
        self._attr_unique_id = f'{entry.entry_id}_clock_face'

    @property
    def options(self):
        http = self.device.get('http')
        if not http: return []
        faces = http.capabilities.get('clockFaces', []) if isinstance(http.capabilities, dict) else []
        if isinstance(faces, dict): faces = list(faces.keys())
        if not isinstance(faces, list): return []
        return [x for x in faces if isinstance(x, str)]

    @property
    def available(self):
        http = self.device.get('http')
        return bool(http and self.options and isinstance(http.display_settings, dict)
                    and isinstance(http.display_settings.get('clockFace'), str))

    @property
    def current_option(self):
        http = self.device.get('http')
        value = http.display_settings.get('clockFace') if http else None
        return value if value in self.options else None

    async def async_select_option(self, option):
        if option not in self.options:
            raise HomeAssistantError('Quadrante non supportato')
        http = self.device.get('http')
        if not http: raise HomeAssistantError('HTTP not configured')
        await http.request('PATCH', '/api/v1/settings', {'clockFace': option})
        http.display_settings['clockFace'] = option
        self.async_write_ha_state()

class WeatherOverlay(_HttpEntity, SelectEntity):
    _attr_has_entity_name = True
    _attr_translation_key = 'weather_overlay'
    _attr_icon = 'mdi:weather-partly-cloudy'

    def __init__(self, entry, device):
        super().__init__(entry, device)
        self._attr_unique_id = f'{entry.entry_id}_weather_overlay'

    @property
    def options(self):
        http = self.device.get('http')
        if not http or not isinstance(http.capabilities, dict): return []
        overlays = http.capabilities.get('overlays', [])
        if not isinstance(overlays, list): return []
        return ['Nessuno'] + [x for x in overlays if isinstance(x, str)]

    @property
    def available(self):
        http = self.device.get('http')
        return bool(http and self.options and isinstance(http.display_info, dict)
                    and 'overlay' in http.display_info)

    @property
    def current_option(self):
        http = self.device.get('http')
        if not http: return None
        active = http.display_info.get('overlay')
        return active if active in self.options else 'Nessuno'

    async def async_select_option(self, option):
        if option not in self.options: raise HomeAssistantError('Animazione meteo non supportata')
        http = self.device.get('http')
        if not http: raise HomeAssistantError('HTTP not configured')
        new = None if option == 'Nessuno' else option
        await http.request('PATCH', '/api/v1/display', {'overlay': new})
        http.display_info['overlay'] = new
        self.async_write_ha_state()


class AppTransition(_HttpEntity, SelectEntity):
    _attr_has_entity_name = True
    _attr_translation_key = 'app_transition'
    _attr_icon = 'mdi:transition'

    def __init__(self, entry, device):
        super().__init__(entry, device)
        self._attr_unique_id = f'{entry.entry_id}_app_transition_effect'

    @property
    def options(self):
        http = self.device.get('http')
        values = http.capabilities.get('transitions', []) if http and isinstance(http.capabilities, dict) else []
        return [v for v in values if isinstance(v, str)] if isinstance(values, list) else []

    @property
    def available(self):
        return bool(self.options)

    @property
    def current_option(self):
        http = self.device.get('http')
        value = http.display_settings.get('transitionEffect') if http and isinstance(http.display_settings, dict) else None
        return value if value in self.options else None

    async def async_select_option(self, option):
        if option not in self.options: raise HomeAssistantError('Transizione non supportata')
        http = self.device.get('http')
        if not http: raise HomeAssistantError('HTTP non disponibile')
        await http.request('PATCH', '/api/v1/settings', {'transitionEffect': option})
        http.display_settings['transitionEffect'] = option
        self.async_write_ha_state()
