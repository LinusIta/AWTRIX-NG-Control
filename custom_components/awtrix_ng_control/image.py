"""Real framebuffer preview via device HTTP API."""
from __future__ import annotations
from io import BytesIO
from PIL import Image
from homeassistant.components.image import ImageEntity
from .const import DOMAIN, CONF_NAME

async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([AwtrixScreen(hass,entry,hass.data[DOMAIN][entry.entry_id])])

class AwtrixScreen(ImageEntity):
    _attr_has_entity_name = True
    _attr_translation_key = 'screen'
    _attr_content_type = 'image/png'
    def __init__(self,hass,entry,device):
        super().__init__(hass)
        self.hass,self.entry,self.device=hass,entry,device
        self._attr_unique_id=f'{entry.entry_id}_screen'
        self._attr_device_info={'identifiers':{(DOMAIN,entry.entry_id)},'name':entry.data[CONF_NAME],'manufacturer':'Ulanzi / AWTRIX NG'}
    @property
    def available(self): return bool(self.device.get('http') and self.device['http'].connected)
    async def async_image(self):
        client=self.device.get('http')
        if not client: return None
        data=await client.request('GET','/api/v1/display/screen')
        if not isinstance(data,dict): return None
        w,h=data.get('width'),data.get('height')
        pixels=data.get('pixels',[])
        if not isinstance(w,int) or not isinstance(h,int) or w*h>4096 or not isinstance(pixels,list) or len(pixels)!=w*h:return None
        def render():
            im=Image.new('RGB',(w,h))
            im.putdata([((int(c)>>16)&255,(int(c)>>8)&255,int(c)&255) for c in pixels])
            im=im.resize((w*8,h*8),resample=Image.Resampling.NEAREST)
            out=BytesIO(); im.save(out,'PNG'); return out.getvalue()
        return await self.hass.async_add_executor_job(render)
