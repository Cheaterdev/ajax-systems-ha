# ajax-systems-ha
Ajax Security integration into Home Assistant

## Features
Exposes your Ajax Security devices in Home Assistant:
- Ajax DoorProtect
- Ajax MotionProtect
- Ajax LeaksProtect
- Ajax WallSwitch
- Ajax FireProtect

## Setup
	Place entire contents in */custom_components* folder
	
```yaml
# configuration.yaml

ajax_hub:
  username: !USERNAME!
  password: !PASSWORD!
  
```

Configuration variables:
- **username** (*Required*): Your login username
- **password** (*Required*): Your login password

For security purposes create and use another Ajax Account with user-mode rights.

## Disclaimer
This software is supplied "AS IS" without any warranties and support.