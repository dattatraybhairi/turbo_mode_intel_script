#!/bin/bash

echo running setup2

apt install net-tools

wget https://www.realvnc.com/download/file/vnc.files/VNC-Server-6.7.2-Linux-x86.deb

sudo apt install ./VNC-Server-6.7.2-Linux-x86.deb -y

sudo systemctl start vncserver-x11-serviced.service

sudo systemctl restart wificonfig.service

sudo systemctl status wificonfig.service

echo test wificonfig.service 

sudo -H -u vacus bash -c 'firefox http://localhost:8001/'

sed -i 's/test/DIGVK/g' social.py

sudo systemctl restart broker

sudo systemctl status broker

sudo systemctl status gateway

sudo systemctl status counter

sudo systemctl status socialParamsConfig.service 

cat /sys/class/net/*/address


