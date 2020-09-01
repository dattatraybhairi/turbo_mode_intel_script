#!/bin/bash 

echo $(pwd)

sudo apt-get install git -y

sudo git clone https://VacusTechnology:Vacus%23321@github.com/VacusTechnology/socialDistancingGw

sudo git clone https://VacusTechnology:Vacus%23321@github.com/VacusTechnology/wifiConfigurationGw

cd socialDistancingGw/

sudo git checkout mallapur

cd deb/

sudo apt-get install ./gateway-mallapur_1.0.0_amd64.deb -y

cd ../wifiDeb

sudo apt-get install ./wificonfig_1.0.0_amd64.deb -y

echo setup finished 
