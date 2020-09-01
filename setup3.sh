#!/bin/bash

echo running setup2

apt install lm-sensors

echo $(sensors)

sudo systemctl status wificonfig.service

echo test wificonfig.service 

sudo -H -u vacus bash -c 'firefox http://localhost:8001/'

sed -i 's/test/DIGVK/g' social.py

sudo systemctl status broker

sudo systemctl status gateway

sudo systemctl status counter

sudo systemctl status socialParamsConfig.service 



