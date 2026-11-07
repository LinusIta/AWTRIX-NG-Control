"""Real radio station dropdown from the device."""
import json
from homeassistant.components.select import SelectEntity
from homeassistant.components import mqtt
from homeassistant.core import callback
from .const import DOMAIN, CONF_NAME, CONF_PREFIX

async def async_setup_entry(hass, entry, async_add_entities):
    device = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AwtrixRadioSelect(hass, entry, device), AwtrixAppSelect(hass, entry, device)])
    from .notification_controls import NotificationScroll
    async_add_entities([NotificationScroll(entry, device)])
    from .extra_controls import ClockFace, WeatherOverlay, AppTransition
    async_add_entities([ClockFace(entry, hass.data[DOMAIN][entry.entry_id]), WeatherOverlay(entry, hass.data[DOMAIN][entry.entry_id]), AppTransition(entry, hass.data[DOMAIN][entry.entry_id])])

class AwtrixRadioSelect(SelectEntity):
    _attr_has_entity_name = True
    _attr_translation_key = 'radio_station'
    _attr_icon = 'mdi:radio'
    def __init__(self,hass,entry,device):
        self.hass,self.entry,self.device = hass,entry,device
        self._attr_unique_id = f'{entry.entry_id}_radio_station'
        self._attr_device_info = {'identifiers':{(DOMAIN,entry.entry_id)},'name':entry.data[CONF_NAME],'manufacturer':'Ulanzi / AWTRIX NG'}
    @property
    def available(self):
        http = self.device.get('http')
        return bool(http and (http.endpoint_ok.get('stations') or http.station_names))
    @property
    def options(self):
        http = self.device.get('http')
        return ['— Arresta radio —'] + (http.station_names if http else [])
    @property
    def current_option(self):
        http = self.device.get('http')
        if not http: return None
        radio = http.audio.get('radio', {}) if isinstance(http.audio,dict) else {}
        if isinstance(radio,dict) and radio.get('playing'):
            name = radio.get('station') or radio.get('name')
            return name if isinstance(name,str) and name in self.options else None
        return '— Arresta radio —'
    async def async_select_option(self, option):
        if option not in self.options: raise ValueError('Unknown station')
        path, body = ('audio/stop', {'group':'radio'}) if option == '— Arresta radio —' else ('audio/play', {'station':option})
        http = self.device.get('http')
        if http:
            await http.request('POST', '/api/v1/' + path, body)
            await http.refresh()
        else:
            await mqtt.async_publish(self.hass,f'{self.entry.data[CONF_PREFIX]}/cmd/{path}',json.dumps(body,ensure_ascii=False),qos=0,retain=False)
    async def async_added_to_hass(self):
        self.device['listeners'].add(self._update)
        self.async_on_remove(lambda: self.device['listeners'].discard(self._update))
    @callback
    def _update(self): self.async_write_ha_state()

class AwtrixAppSelect(SelectEntity):
    _attr_has_entity_name = True
    _attr_translation_key = 'show_app'
    _attr_icon = 'mdi:apps'

    def __init__(self, hass, entry, device):
        self.hass, self.entry, self.device = hass, entry, device
        self._attr_unique_id = f'{entry.entry_id}_app_select'
        self._attr_device_info = {'identifiers': {(DOMAIN, entry.entry_id)}, 'name': entry.data[CONF_NAME], 'manufacturer': 'Ulanzi / AWTRIX NG'}

    @property
    def available(self):
        http = self.device.get('http')
        return bool(http and (http.endpoint_ok.get('apps', False) or http.app_names))

    @property
    def options(self):
        http = self.device.get('http')
        return list(http.app_names) if http and http.app_names else ['Time']

    @property
    def current_option(self):
        active = self.device['state'].get('apps/active')
        if isinstance(active, str) and active in self.options:
            return active
        state = self.device['state'].get('device', {})
        if isinstance(state, dict):
            active = state.get('currentApp') or state.get('app')
            if isinstance(active, str) and active in self.options:
                return active
        return None

    async def async_select_option(self, option):
        if option not in self.options:
            raise ValueError('Unknown app')
        http = self.device.get('http')
        if http:
            await http.request('PUT', '/api/v1/apps/active', {'name': option, 'fast': True})
        else:
            await mqtt.async_publish(self.hass, f'{self.entry.data[CONF_PREFIX]}/cmd/apps/switch', option, qos=0, retain=False)
        self.device['state']['apps/active'] = option
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        self.device['listeners'].add(self._update)
        self.async_on_remove(lambda: self.device['listeners'].discard(self._update))

    @callback
    def _update(self):
        self.async_write_ha_state()
