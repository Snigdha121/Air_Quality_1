from grove import grovepi
from grove import grove_i2c_digital_light_sensor as grove_light_sensor
import time, signal, sys
sys.path.append('/home/pi/iotsc/dashboard/Adafruit_ADS1x15')

from Adafruit_ADS1x15 import ADS1x15

import paho.mqtt.client as mqtt
import time
import math
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
import json
import logging
import configparser
import argparse
import csv
import base64
import sys
from influxdb import InfluxDBClient
import os




global IFclient, objects
json_body = []
contents={}

contents["measurement"]="Air_Quality4"
contents["tags"]={}
contents["tags"]["PI_ID"]=9027
contents["fields"]={}



IFclient=InfluxDBClient('eclipse.usc.edu',10002,'loracciuser','lora4cci','loracci')



####I2c ADC MUX Configuration##########
ADS1115 = 0x01	# 16-bit ADC

# Select the gain
gain = 4096  # +/- 4.096V

# Select the sample rate
sps = 8    # 8 samples per second

###########################################




# Parse the arguments
parser = argparse.ArgumentParser()
parser.add_argument("output_file", help="Output file for log/debug")
parser.add_argument("input_file", help="Input file with configurations")

args = parser.parse_args()

# Logging setup
logging.basicConfig(filename=args.output_file, level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filemode='w')

# Configuration file
settings = configparser.ConfigParser()
settings.read(args.input_file)

# Device Identifier
iotsc_id = str(settings.get('id', 'myid'))

#I3 Broker configurations
i3_broker = str(settings.get('IMSCBroker', 'i3_url'))
i3_port = str(settings.get('IMSCBroker', 'i3_port'))
i3_topic = str(settings.get('IMSCBroker', 'i3_topic'))
i3_user_name = str(settings.get('IMSCBroker', 'i3_user_name'))
i3_password = str(settings.get('IMSCBroker', 'i3_password'))

#Eclipse Broker
eclipse_broker="eclipse.usc.edu"


#Bluetooth Broker
bluetooth_broker="localhost"


# Sensors dictionary
sensors = {}
bluetooth_payload = {}

# Set up the sensors settings (from config file)
for section in settings.sections():
    if section.startswith('sensor'):
        l = [str(settings.get(section, 'telemetry')),
             str(settings.get(section, 'type')),
             str(settings.get(section, 'bus')),
             int(settings.get(section, 'port')),
             int(settings.get(section, 'sampling'))]
        sensors[str(settings.get(section, 'id'))] = l

# Setting up the direction of pins and initialize modules
k = sensors.keys()
# Gas sensors are all connected with an extra board with MCP3008 chip
if 'gas_mq2' in k or 'gas_mq3' in k or 'gas_mq5' in k or 'gas_mq9' in k:
    gas_sensors = ADS1x15(ic=ADS1115)
    adc = gas_sensors

last_attributes = {}
last_telemetry = {}
next_sample = {}

# MQTT callback function after connection
def on_connect(client, userdata, flags, rc):
    ##Commenting the below line to minimise log overhead	
    ##logging.info('Connected flags ' + str(flags) + ' Result code ' + str(rc) + ' Client_id  ' + str(client))
    return

# MQTT callback function when a message is received
def on_message(client, userdata, msg):
    ##Commenting the below line to minimise log overhead	
    ##logging.info("Message received  " + msg.topic + " " + msg.payload)
    return


i3_client = mqtt.Client(i3_user_name)
i3_client.on_connect = on_connect
i3_client.on_message = on_message
i3_client.username_pw_set(i3_user_name, i3_password)




connected_i3 = False
while connected_i3 == False:
    try:    
        logging.info('Connecting to i3 broker...')
        i3_client.connect(i3_broker, i3_port, 60)
        i3_client.loop_start()
        connected_i3 = True
    except Exception as e:
        logging.critical('Exception' + str(e))
        time.sleep(1)



# Initialize the dictionary of next sample timestamp
cur_time_ms = int(time.time() * 1000)
for k,v in sensors.items():
    next_sample[k] = cur_time_ms + v[4]*30

next_i3_publish = int(time.time())



while True:
    time.sleep(30)
    for k,v in sensors.items():
        sensor_type = v[1]
        if sensor_type == 'sensor':
            topic = v[0]
            port = v[3]
            interval = v[4]
            data = None

            cur_time_ms = int(time.time() * 1000)
            cur_time = int(time.time())

            try:
		#time.sleep(300)
		# Gas MQ2
                if k == 'gas_mq2' and cur_time_ms > next_sample[k]:
		    data = adc.readRaw(0, gain, sps)
		    logging.debug("Reading Gas MQ2 " + str(data))
                    next_sample[k] = cur_time_ms + interval
                # Gas MQ3
                elif k == 'gas_mq3' and cur_time_ms > next_sample[k]:
		    	data = adc.readRaw(1, gain, sps) 
                    	logging.debug("Reading Gas MQ3 " + str(data))
                    	next_sample[k] = cur_time_ms + interval
                # Gas MQ5
                elif k == 'gas_mq5' and cur_time_ms > next_sample[k]:
		    	data = adc.readRaw(2, gain, sps) 
                    	logging.debug("Reading Gas MQ5 " + str(data))
                    	next_sample[k] = cur_time_ms + interval
                # Gas MQ9
                elif k == 'gas_mq9' and cur_time_ms > next_sample[k]:
		    	data = adc.readRaw(3, gain, sps) 
                    	logging.debug("Reading Gas MQ9 " + str(data))
                    	next_sample[k] = cur_time_ms + interval
     
                

            except Exception as ex:
                pass
            
            else:
                # Publish the data (if valid)
                if data is not None:
                    last_telemetry[topic] = data
		    last_telemetry["ID"]=iotsc_id

                    if cur_time > next_i3_publish :
                        next_i3_publish = cur_time + 30
			print("***********************************************************")
			print(last_telemetry)
			print("***********************************************************")
                        i3_client.publish(i3_topic, json.dumps(last_telemetry), 1)
			for i in last_telemetry:
				if i == "gas_mq2":
					#print("##########################################################")	
					#print(last_telemetry[i])
					contents["fields"]["gas_mq2"]=int(last_telemetry[i])
				if i == "gas_mq3":
					print(last_telemetry[i])
					contents["fields"]["gas_mq3"]=int(last_telemetry[i])
				if i == "gas_mq5":
					contents["fields"]["gas_mq5"]=int(last_telemetry[i])
				if i== "gas_mq9":
					contents["fields"]["gas_mq9"]=int(last_telemetry[i])
			
			if (len(contents["fields"])==4):
				json_body.append(contents)
				#print(json.dumps(contents))
				print ("write_points: {0}".format(json_body))
				IFclient.write_points(json_body)
				 	

        else:	
            continue

