import logging

from homeassistant.components.switch import SwitchDevice

from custom_components.ajax_hub import AjaxDevice

DOMAIN = 'ajax_hub'
_LOGGER = logging.getLogger(__name__)

# Load power in watts (W)
ATTR_LOAD_POWER = 'load_power'

# Total (lifetime) power consumption in watts
ATTR_POWER_CONSUMED = 'power_consumed'
ATTR_IN_USE = 'in_use'

LOAD_POWER = 'load_power'
POWER_CONSUMED = 'power_consumed'
IN_USE = 'inuse'
VOLTAGE = 'voltage'

def setup_platform(hass, config, add_entities, discovery_info=None):
    devices = []
    for (_,hub) in hass.data[DOMAIN].hubs.items():
        for entry in hub.init_data["objects"]:
            objectType = entry["objectType"]
            if objectType == 31:
                devices.append(AjaxSwitch(entry,  hub))
           
    add_entities(devices)


class AjaxSwitch(SwitchDevice, AjaxDevice):

    def __init__(self, device,  
                 ajax_hub):
        AjaxDevice.__init__(self, device,ajax_hub )     
        self._in_use = device["active"]
        self._load_power = device["current"]
        self._power_consumed = device["powerConsumed"]
        self._voltage = device["voltage"]

    @property
    def unique_id(self):
        return "switch_"+str(self._id)

    @property
    def name(self):
        return self._name

    @property
    def icon(self):
        return 'mdi:power-plug'

    @property
    def is_on(self):
        return self._in_use

    @property
    def current_power_w(self):
        """Return the current power usage in W."""
        return self._load_power*self._voltage

    @property
    def today_energy_kwh(self):
        """Return the today total energy usage in kWh."""
        return self._power_consumed/1000

    @property
    def device_state_attributes(self):
        attrs = {ATTR_IN_USE: self._in_use,
                ATTR_LOAD_POWER: self._load_power,
                ATTR_POWER_CONSUMED: self._power_consumed,
                VOLTAGE: self._voltage
                }

        return attrs

    @property
    def available(self):
        return self._online

    def turn_on(self, **kwargs):
        _LOGGER.error("turn_on " )
        self.hub.systems.set_switch_state(self.hub, self, True)

    def turn_off(self, **kwargs):
        _LOGGER.error("turn_off " )
        self.hub.systems.set_switch_state(self.hub, self, False)

    def parse_data(self, device, raw_data):
        AjaxDevice.parse_data(self,device,raw_data)
        self._in_use = device["active"]
        self._load_power = device["current"]
        self._power_consumed = device["powerConsumed"]
        self._voltage = device["voltage"]
        self.async_schedule_update_ha_state()