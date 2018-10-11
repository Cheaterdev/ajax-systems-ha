import asyncio
import logging
import json
import voluptuous as vol
import sseclient
import requests
import time
from collections import defaultdict
from requests_toolbelt.utils import dump
from homeassistant.core import callback
import voluptuous as vol

from homeassistant.components.device_tracker import ATTR_SOURCE_TYPE
from homeassistant.const import (ATTR_FRIENDLY_NAME, CONF_ENTITIES,
                                 EVENT_HOMEASSISTANT_START)
from homeassistant.exceptions import TemplateError
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity, async_generate_entity_id
from homeassistant.helpers.event import async_track_state_change
from homeassistant.helpers.restore_state import async_get_last_state
from homeassistant.helpers import template as template_helper
from threading import Thread
from homeassistant.helpers import discovery
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD

_LOGGER = logging.getLogger(__name__)


DOMAIN = 'ajax_hub'
PLATFORM = 'ajax_platform'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string
    }),
}, extra=vol.ALLOW_EXTRA)


ATTR_BATTERY = 'battery'

def setup(hass, config):
    hass.data[DOMAIN] = AjaxSystems(hass, config[DOMAIN])
   
    return True

class AjaxSystems(Entity):
    
    def __init__(self, hass, config):
        self.hass = hass
        self.s = requests.Session() 
        self._threads = []
        self.callbacks = defaultdict(list)
        self._config = config

        self.authorize()

        response = self.s.post('https://app.ajax.systems/SecurConfig/api/account/getUserData')
        _LOGGER.debug("AjaxSystems result "  + response.content.decode('utf-8'))
        
        response = self.s.post('https://app.ajax.systems/SecurConfig/api/dashboard/getHubsData')
        d = json.loads(response.content)
        _LOGGER.debug("AjaxSystems result "  + response.content.decode('utf-8'))
        
        self.hubs = {}
        
        for device in d["data"]:
            self.hubs[device] =  AjaxHub(self, device, d["data"][device])
            self._any_hub_id = self.hubs[device]._hid

        _LOGGER.debug("AjaxSystems result "  +response.content.decode('utf-8'))       

        for component in ['switch' ,'binary_sensor']:
            discovery.load_platform(hass, component, DOMAIN, {}, {})

        thread = Thread(target=self._listen_to_msg, args=())
        self._threads.append(thread)
        thread.daemon = True
        thread.start()


        thread2 = Thread(target=self._read_logs, args=())
        self._threads.append(thread2)
        thread2.daemon = True
        thread2.start()

    def authorize(self):
        payload = {'j_username': self._config[CONF_USERNAME], 'j_password':self._config[CONF_PASSWORD]}
		
        response = self.s.post('https://app.ajax.systems/api/account/do_login', data=payload)
        _LOGGER.debug("AjaxSystems "  + response.content.decode('utf-8'))
		
        response = self.s.post('https://app.ajax.systems/SecurConfig/api/account/getCsaConnection')
        _LOGGER.debug("AjaxSystems result "  + response.content.decode('utf-8'))



    def set_switch_state(self, hub, device, state):
        payload = {'hubID': hub._hid, 'objectType':'31', 'deviceID':device._hid, 'command':6 if state == True else 7}
        response = self.s.post('https://app.ajax.systems/SecurConfig/api/dashboard/sendCommand', data=payload)
        _LOGGER.debug("set_switch_state result "  +str(hub._hid) + " " +str(device._id) + " " +response.content.decode('utf-8'))
        
    def _listen_to_msg(self):
        while True:
            client = sseclient.SSEClient(self.s.get('https://app.ajax.systems/SecurConfig/api/dashboard/sse', stream=True))
            for event in client.events():        
                jdata = json.loads(event.data)
                if 'objectId' in jdata['data']:
                    sid = int(jdata['data']['objectId'])
                    found = False
                    for func in self.callbacks[sid]:
                        func(jdata['data'], event.data)
                        found = True
                    if found == False:
                        _LOGGER.debug("Unknown: "  + event.data)
                else:
                    _LOGGER.debug("_listen_to_msg: "  + event.data)
            _LOGGER.error("_listen_to_msg ENDED")
            self.authorize()
            
    def _read_logs(self):
        while True:
            payload = {'hubId': self._any_hub_id, 'count':1, 'offset':0}
            response = self.s.post('https://app.ajax.systems/SecurConfig/api/dashboard/getLogs', data=payload )
            _LOGGER.debug("_read_logs result "  +response.content.decode('utf-8'))
            time.sleep(60)
        
class AjaxDevice:
    def __init__(self, device, ajax_hub):
        self._id = int(device["objectId"])
        self._hid = device["hexObjectId"]
        self._name = device["deviceName"]
        self.hub = ajax_hub
        self._online = device.get('online', None)
        self._battery = device.get('batteryCharge', None)       
        ajax_hub.systems.callbacks[self._id].append(self.parse_data)

    def parse_data(self, device, raw_data):
        self._name = device["deviceName"]
        self._online = device.get('online', None)
        self._battery = device.get('batteryCharge', None)
        
    def get_attributes(self):
        return {ATTR_BATTERY: self._battery}

class AjaxHub(AjaxDevice):
    def __init__(self, systems, device_id, data):
        self.init_data = data
        self.systems = systems

        _LOGGER.error("AjaxHub init "  + device_id)
        for entry in data["objects"]:
            objectType = entry["objectType"]
            if objectType == 33:
                AjaxDevice.__init__(self, entry, self)