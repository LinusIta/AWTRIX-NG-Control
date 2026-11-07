"""Three native Home Assistant lights for AWTRIX NG indicator LEDs."""
from __future__ import annotations
from homeassistant.components.light import LightEntity, ColorMode
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from .const import DOMAIN, CONF_NAME

async def async_setup_entry(hass, entry, async_add_entities):
    device = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([IndicatorLight(entry, device, index) for index in (1, 2, 3)])

class IndicatorLight(LightEntity):
    _attr_has_entity_name = True
    _attr_supported_color_modes = {ColorMode.RGB}
    _attr_color_mode = ColorMode.RGB

    def __init__(self, entry, device, index):
        self.device, self.index = device, index
        self._attr_unique_id = f"{entry.entry_id}_indicator_{index}"
        self._attr_translation_key = "indicator"
        self._attr_translation_placeholders = {"index": str(index)}
        self._attr_icon = "mdi:led-on"
        self._attr_device_info = {
            'identifiers': {(DOMAIN, entry.entry_id)},
            'name': entry.data[CONF_NAME],
            'manufacturer': 'Ulanzi / AWTRIX NG',
        }
        self._last_color = (255, 255, 255)
        self._last_on = False

    def _indicator_state(self):
        current = self.device['state'].get('device', {})
        if not isinstance(current, dict): return None
        indicators = current.get('indicators')
        if isinstance(indicators, list) and len(indicators) >= self.index:
            value = indicators[self.index-1]
            if isinstance(value, dict): return value
        return None

    @property
    def available(self):
        # HTTP is already proven live by the other controls. An indicator has
        # no dedicated GET endpoint: its state is reported in /state/device.
        return self.device.get('http') is not None

    @property
    def is_on(self):
        current = self._indicator_state()
        return bool(current['on']) if current and 'on' in current else self._last_on

    @property
    def rgb_color(self):
        current = self._indicator_state()
        value = current.get('color') if current else None
        if isinstance(value, str) and len(value) == 7 and value.startswith('#'):
            try: return tuple(bytes.fromhex(value[1:]))
            except ValueError: pass
        return self._last_color

    async def async_turn_on(self, **kwargs):
        rgb = kwargs.get('rgb_color') or self.rgb_color or (255,255,255)
        color = '#' + ''.join(f'{max(0,min(255,int(n))):02X}' for n in rgb)
        http = self.device.get('http')
        if http is None: raise HomeAssistantError('AWTRIX HTTP non disponibile')
        await http.request('PUT', f'/api/v1/indicators/{self.index}', {'color':color})
        self._last_on, self._last_color = True, tuple(rgb)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        http = self.device.get('http')
        if http is None: raise HomeAssistantError('AWTRIX HTTP non disponibile')
        # Use null color rather than DELETE, retaining the selected color.
        await http.request('PUT', f'/api/v1/indicators/{self.index}', {'color':None})
        self._last_on = False
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        await super().async_added_to_hass()
        self.device['listeners'].add(self._refresh)
        self.async_on_remove(lambda:self.device['listeners'].discard(self._refresh))

    @callback
    def _refresh(self):
        self.async_write_ha_state()
