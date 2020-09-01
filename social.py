#! /usr/bin/python3

import logging 
import logging.handlers
import ssl
import random
import serial
import time
# import package numpy
import numpy as np
# import paho.mqtt.client
import paho.mqtt.client as mqtt
# import json package
import json
import ast
from pymongo import MongoClient

time.sleep(10)

broker = "strides.vacustech.in"
port = 1883
topic = "tvstracking"

db_broker = "difence.digitalblanket.io"
db_port = 8883
db_broker_username = "db2user"
db_broker_password = "db2user"
db_alert_topic = "/test/Alert/Vacus"
db_health_topic = "/test/Health/Vacus" 

byteBuffer = np.zeros(2 ** 11, dtype='uint8')
byteBufferLength = 0


def fetchGatewayMac():
    with open("/home/pi/Desktop/configuration/macid.conf","r+") as fd:
        lines = fd.read().splitlines()
    macid = lines[0] 
    return macid
gatewayMac = fetchGatewayMac()

def systemcon(logger):
    st = 0
    try:
        st = client.connect(broker, port, keepalive=60)  # establishing connection
        st = dbClient.connect(db_broker, db_port, keepalive=60)
    
    except Exception as err:
        st = 1;

    finally:
        if (st != 0):
            logger.info("not able to connect to broker...trying to connect again")
            time.sleep(5)
            systemcon(logger);
        else:
            logger.info("Connected to the broker")

def serial_config():
    """
    function to configure the pi or computer
    receive data and returns the serial port
    """
    # Open the serial ports for the configuration and the data ports

    # Raspberry pi
    data_port = serial.Serial('/dev/ttyUSB0', 9600)

    if data_port.isOpen():
        try:
            # throwing all the data stored at port coming from sensor
            data_port.flushInput()
        # if error is been thrown print it
        except Exception as err:
            print("Error " + str(err))
            data_port.close()
            exit()

    else:
        try:
            data_port.open()
        except Exception as err:
            print("Error " + str(err))
            data_port.close()
            exit()

    return data_port


def processData(data_port,logger):
    '''
    processes the serial data
    :return: none
    '''
    data = 0
    global byteBuffer, byteBufferLength
    max_buffer_size = 2048
    frame_size = 700
    last_byte = 127
    # if data available in serial port
    if data_port.in_waiting:
        read_buffer = data_port.read(data_port.in_waiting)
        #print(read_buffer)

        byte_vec = np.frombuffer(read_buffer, dtype='uint8')
        byte_count = len(byte_vec)

        # Check that the buffer is not full, and then add the data to the buffer
        if (byteBufferLength + byte_count) < max_buffer_size:
            # byteBuffer[byteBufferLength:byteBufferLength + byte_count] = byte_vec
            byteBuffer = np.insert(byteBuffer, byteBufferLength + 1, byte_vec)
            byteBufferLength = byteBufferLength + byte_count

            # Check that the buffer has some data
            if byteBufferLength > frame_size:
                # check for all possible locations for 127
                possible_locs = np.where(byteBuffer == last_byte)[0]

                for loc in possible_locs:
                    if loc > (frame_size - 1):
                        data_frame = byteBuffer[(loc - frame_size):loc]
                        processDataFrame(data_frame)
                        # print("byteBuffer", byteBuffer[:loc])
                        # Remove the data from buffer
                        # byteBuffer[:loc] = byteBuffer[loc:byteBufferLength]
                        # byteBuffer[byteBufferLength - loc:] = np.zeros(
                        #    len(byteBuffer[byteBufferLength - loc:]),
                        #    dtype='uint8')
                        np.pad(byteBuffer, (1, 0), mode='constant')[loc + 2:]
                        byteBufferLength = byteBufferLength - loc
                        break


def processDataFrame(data_array):
    '''
    function to process data array
    :param data_array:
    :return: none
    '''
    global client, gatewayMac, dbClient
    
    macBytes = gatewayMac.split("-")
    area = "5a-c2-15-d3" + "-" + str(macBytes[4]) + "-" + str(macBytes[5])
    
    payload = []
    db_alert_payload = []
    db_health_payload = []

    db_health_payload.append({
        "id": gatewayMac,
        "on_off": 1,
        "type": 3,
        "timestamp": int(round(time.time()*1000))
    })
    

    split_data_array = np.split(data_array, 100)
    #print("SPLIT ARRAY IS - ")
    #print(split_data_array)

    for pair in split_data_array:
        if pair[1]:
            payload.append({
                "Tag1": "{0:0{1}x}".format(pair[0], 2) + "-" + "{0:0{1}x}".format(pair[1], 2),
                "Tag2": "{0:0{1}x}".format(pair[2], 2) + "-" + "{0:0{1}x}".format(pair[3], 2),
                "Battery": int(pair[4]),
                "RSSI": int(pair[5]),
                "Alert": int(pair[6]),
                "Gateway": gatewayMac,
                "TimeStamp": int(round(time.time()))
            })

            db_health_payload.append({
                "id": "5a-c2-15-a0" + "-" + "{0:0{1}x}".format(pair[0], 2) + "-" + "{0:0{1}x}".format(pair[1], 2),
                "bt": int(pair[4]),
                "type": 1,
                "timestamp": int(round(time.time()*1000))
            })

            if (pair[6]!=0):
                db_alert_payload.append({
                "id": "5a-c2-15-a0" + "-" + "{0:0{1}x}".format(pair[0], 2) + "-" + "{0:0{1}x}".format(pair[1], 2),
                "type": int(pair[6]),
                "gateway": gatewayMac,
                "timestamp": int(round(time.time()*1000))
                })    

            if (pair[2]==0) and (pair[3]==0):    
                pass        
            else:
                db_alert_payload.append({
                    "id1": "5a-c2-15-a0" + "-" + "{0:0{1}x}".format(pair[0], 2) + "-" + "{0:0{1}x}".format(pair[1], 2),
                    "id2": "5a-c2-15-a0" + "-" + "{0:0{1}x}".format(pair[2], 2) + "-" + "{0:0{1}x}".format(pair[3], 2),
                    "dist": round(random.uniform(0.5, 1), 1),
                    "area": area,
                    "type": 2,
                    "gateway": gatewayMac,
                    "timestamp": int(round(time.time()*1000))
                })

    if len(payload):
        print("Payload for Vacus broker is -")
        print(payload)

        json_payload = json.dumps(payload)
        try:
            ret = client.publish(topic, payload=json_payload, qos=0)
        except Exception as err:
            logger.info("Failed to post the data - " + str(err))
        else:
            if ret[0] != 0:
                logger.innfo("Disconnected from vacus broker..trying to reconnect")
                systemcon(logger)
            else:
                logger.info("Posted the data to vacus broker successfully")

    if len(db_alert_payload):
        print("Alert Payload for flamenco broker is -")
        print(db_alert_payload)

        json_db_alert_payload = json.dumps(db_alert_payload)
        try:
            ret = dbClient.publish(db_alert_topic, payload=json_db_alert_payload, qos=0)
        except Exception as err:
            logger.info("Failed to post the data - " + str(err))
        else:
            if ret[0] != 0:
                logger.innfo("Disconnected from flamenco broker..trying to reconnect")
                systemcon(logger)
            else:
                logger.info("Posted the alert data to flamenco broker successfully")

    if len(db_health_payload):
        print("Health Payload for flamenco broker is -")
        print(db_health_payload)
        
        json_db_health_payload = json.dumps(db_health_payload)
        try:
            ret = dbClient.publish(db_health_topic, payload=json_db_health_payload, qos=0)
        except Exception as err:
            logger.info("Failed to post the health data to flamenco broker - " + str(err))
        else:
            if ret[0] != 0:
                logger.innfo("Disconnected from flamenco broker..trying to reconnect")
                systemcon(logger)
            else:
                logger.info("Posted the health data to flamenco broker successfully")

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, user_data, flags, rc):
    print("Connected with result code " + str(rc))

# Create the logger for the application and bind the output to /sys/log/ #
logger = logging.getLogger('data-posting-service')
logger.setLevel(logging.INFO)
logHandler = logging.handlers.SysLogHandler(address='/dev/log')
logHandler.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)s - %(message)s')
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)

Data_port = serial_config()
client = mqtt.Client()
dbClient = mqtt.Client()
client.on_connect = on_connect
dbClient.on_connect = on_connect
dbClient.username_pw_set(db_broker_username, db_broker_password)
dbClient.tls_set(ca_certs="/home/pi/Desktop/ssl/server-ca.crt", tls_version=ssl.PROTOCOL_TLSv1_2)
systemcon(logger)
client.loop_start()
dbClient.loop_start()

while True:
    try:
        # process serial data
        processData(Data_port,logger)
    except KeyboardInterrupt:
        Data_port.close()
        client.loop_stop()
        dbClient.loop_stop()
        break
