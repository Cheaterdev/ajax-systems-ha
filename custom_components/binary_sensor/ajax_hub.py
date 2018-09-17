import logging

from homeassistant.components.binary_sensor import BinarySensorDevice

from custom_components.ajax_hub import AjaxDevice

DOMAIN = 'ajax_hub'
_LOGGER = logging.getLogger(__name__)


SMOKE_ALARM = 'smoke_alarm'
TEMPERATURE_ALARM = 'temperature_alarm'


def setup_platform(hass, config, add_entities, discovery_info=None):
    devices = []
    for (_,hub) in hass.data[DOMAIN].hubs.items():
        for entry in hub.init_data["objects"]:
            objectType = entry["objectType"]
            if objectType == 5:
                devices.append(AjaxLeakSensor(entry, hub))
            elif objectType == 1:
                devices.append(AjaxDoorSensor(entry, hub))
            elif objectType == 2:
                devices.append(AjaxMotionSensor(entry, hub))
            elif objectType == 3: 
                devices.append(AjaxFireSensor(entry, hub))
                devices.append(AjaxSmokeSensor(entry, hub))
    add_entities(devices)


class AjaxBinarySensor(BinarySensorDevice, AjaxDevice):
    def __init__(self, device,  
                 ajax_hub, device_class):
        AjaxDevice.__init__(self, device, ajax_hub )     
        self._device_class = device_class

    @property
    def device_class(self):
        return self._device_class

    @property
    def unique_id(self):
        return self._device_class + "_" + str(self._id)

    @property
    def name(self):
        return self._name
    
    @property
    def available(self):
        return self._online

    @property
    def device_state_attributes(self):
        return AjaxDevice.get_attributes(self)

class AjaxLeakSensor(AjaxBinarySensor):
    def __init__(self, device,  
                 ajax_hub):
        AjaxBinarySensor.__init__(self, device,ajax_hub,"leak" )     
        self._leak = device["leakDetected"]


    @property
    def is_on(self):
        return self._leak

    def parse_data(self, device, raw_data):
        AjaxDevice.parse_data(self,device,raw_data)
        self._leak = device["leakDetected"]
        self.async_schedule_update_ha_state()


class AjaxDoorSensor(AjaxBinarySensor):
    def __init__(self, device,  
                 ajax_hub):
        AjaxBinarySensor.__init__(self, device,ajax_hub, "door" )     
        self._closed = device["reedClosed"]

    @property
    def is_on(self):
        return self._closed == 0

    def parse_data(self, device, raw_data):
        AjaxDevice.parse_data(self,device,raw_data)
        self._closed = device["reedClosed"]
        self.async_schedule_update_ha_state()

        
class AjaxMotionSensor(AjaxBinarySensor):
    def __init__(self, device,  
                 ajax_hub):
        AjaxBinarySensor.__init__(self, device,ajax_hub,"motion" )     
        self._motion = device["motionPresent"]

    @property
    def is_on(self):
        return self._motion == 1

    def parse_data(self, device, raw_data):
        AjaxDevice.parse_data(self,device,raw_data)
        self._motion = device["motionPresent"]
        self.async_schedule_update_ha_state()

        
class AjaxSmokeSensor(AjaxBinarySensor):
    def __init__(self, device,  
                 ajax_hub):
        AjaxBinarySensor.__init__(self, device,ajax_hub,"smoke" )     
        self._smoke_alarm = device["smokeAlarm"]
 
    @property
    def is_on(self):
        return self._smoke_alarm == 1 

    def parse_data(self, device, raw_data):
        AjaxDevice.parse_data(self,device,raw_data)
        self._smoke_alarm = device["smokeAlarm"]

        self.async_schedule_update_ha_state()

class AjaxFireSensor(AjaxBinarySensor):

    def __init__(self, device,  
                 ajax_hub):
        AjaxBinarySensor.__init__(self, device,ajax_hub,"heat" )     
        self._temperature_alarm = device["temperatureAlarm"]
 
    @property
    def is_on(self):
        return self._temperature_alarm == 1 

    def parse_data(self, device, raw_data):
        AjaxBinarySensor.parse_data(self,device,raw_data)
        self._temperature_alarm = device["temperatureAlarm"]
        self.async_schedule_update_ha_state()
