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


####I2c ADC MUX Configuration##########
ADS1115 = 0x01	# 16-bit ADC

# Select the gain
# gain = 6144  # +/- 6.144V
gain = 4096  # +/- 4.096V
# gain = 2048  # +/- 2.048V
# gain = 1024  # +/- 1.024V
# gain = 512   # +/- 0.512V
# gain = 256   # +/- 0.256V

# Select the sample rate
# sps = 8    # 8 samples per second
# sps = 16   # 16 samples per second
# sps = 32   # 32 samples per second
# sps = 64   # 64 samples per second
# sps = 128  # 128 samples per second
sps = 250  # 250 samples per second
# sps = 475  # 475 samples per second
# sps = 860  # 860 samples per second

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


# Broker parameters (from config file)
iotsc_broker = str(settings.get('dashboard', 'url'))
iotsc_port = int(settings.get('dashboard', 'iotsc_port'))
iotsc_access_token = str(settings.get('dashboard', 'access_token'))
iotsc_topic_telemetry = str(settings.get('dashboard', 'topic_telemetry'))
iotsc_topic_attributes = str(settings.get('dashboard', 'topic_attributes'))

#I3 Broker configurations
i3_broker = str(settings.get('IMSCBroker', 'i3_url'))
i3_port = str(settings.get('IMSCBroker', 'i3_port'))
i3_topic = str(settings.get('IMSCBroker', 'i3_topic'))
i3_user_name = str(settings.get('IMSCBroker', 'i3_user_name'))
i3_password = str(settings.get('IMSCBroker', 'i3_password'))

#Eclipse Broker
eclipse_broker="eclipse.usc.edu"

# Sensors dictionary
sensors = {}

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
if 'temp_interior' in k:
    grovepi.pinMode(sensors['temp_interior'][3], "INPUT")
if 'temp_exterior' in k:
    grovepi.pinMode(sensors['temp_exterior'][3], "INPUT")
if 'light_digital' in k:
    _POWER_DOWN = 0x00
    TSL2561=grove_light_sensor.Tsl2561()
    TSL2561._init__()
if 'pir' in k:
    grovepi.pinMode(sensors['pir'][3], "INPUT")
if 'water' in k:
    grovepi.pinMode(sensors['water'][3], "INPUT")
if 'vibration' in k:
    grovepi.pinMode(sensors['vibration'][3], "INPUT")
if 'sound' in k:
    grovepi.pinMode(sensors['sound'][3], "INPUT")
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

# Connecting to IoTSc broker
iotsc_client = mqtt.Client()
iotsc_client.on_connect = on_connect
iotsc_client.on_message = on_message
iotsc_client.username_pw_set(iotsc_access_token)

i3_client = mqtt.Client(i3_user_name)
i3_client.on_connect = on_connect
i3_client.on_message = on_message
i3_client.username_pw_set(i3_user_name, i3_password)

#Eclipse connection
eclipse_client = mqtt.Client("eclipse")
eclipse_client.on_connect = on_connect
eclipse_client.on_message = on_message


connected = False
while connected == False:
    try:    
        logging.info('Connecting to broker...')
        iotsc_client.connect(iotsc_broker, iotsc_port, 60)
        iotsc_client.loop_start()
        connected = True
    except Exception as e:
        logging.critical('Exception' + str(e))
        time.sleep(1)

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

connected_eclipse = False
while connected_eclipse == False:
    try:    
        logging.info('Connecting to eclipsebroker...')
	eclipse_client.connect(eclipse_broker)
        eclipse_client.loop_start()
        connected_eclipse = True
    except Exception as e:
        logging.critical('Exception' + str(e))
        time.sleep(1)

# Initialize the dictionary of next sample timestamp
cur_time_ms = int(time.time() * 1000)
for k,v in sensors.items():
    next_sample[k] = cur_time_ms + v[4]

next_i3_publish = int(time.time())

while True:
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
                # DHT Temp
                if k == 'dht_temp' and cur_time_ms > next_sample[k]:
                    [temp, hum] = grovepi.dht(port, 1)
                    temp = sorted([-40, temp, 50])[1]
                    if not math.isnan(temp):
                        data = float("{0:.2f}".format(temp))
                        logging.debug("Reading DHT temp " + str(data))
                        next_sample[k] = cur_time_ms + interval
                # DHT Hum
                elif k == 'dht_hum' and cur_time_ms > next_sample[k]:
                    [temp, hum] = grovepi.dht(port, 1)
                    hum = sorted([5, hum, 99])[1]
                    if not math.isnan(hum):
                        data = hum
                        logging.debug("Reading DHT hum " + str(data))
                        next_sample[k] = cur_time_ms + interval
                # Temperature interior
                elif k == 'temp_interior' and cur_time_ms > next_sample[k]:
                    data = float("{0:.2}".format(grovepi.temp(port, '1.2')))
                    logging.debug("Reading Temperature Interior " + str(data))
                    next_sample[k] = cur_time_ms + interval
                # Temperature exterior
                elif k == 'temp_exterior' and cur_time_ms > next_sample[k]:
                    data = float("{0:.2}".format(grovepi.temp(port, '1.2')))
                    logging.debug("Reading Temperature Exterior " + str(data))
                    next_sample[k] = cur_time_ms + interval
                # Light Digital
                elif k == 'light_digital' and cur_time_ms > next_sample[k]:
                    gain = 0
                    val = TSL2561.readLux(gain)
                    data = val[4]
                    data = float("{0:.2f}".format(data))
                    logging.debug("Reading Light Digital " + str(data))
                    next_sample[k] = cur_time_ms + interval
                # PIR
                elif k == 'pir' and cur_time_ms > next_sample[k]:
                    motion = grovepi.digitalRead(port)
                    if motion == 0 or motion == 1:
                        data = motion
                        logging.debug("Reading PIR " + str(data))
                        next_sample[k] = cur_time_ms + interval
                # Water
                elif k == 'water' and cur_time_ms > next_sample[k]:
                    water = grovepi.digitalRead(port)
                    if water == 0 or water == 1:
                        data = 1 - water
                        logging.debug("Reading Water " + str(data))
                        next_sample[k] = cur_time_ms + interval
                # Vibration
                elif k == 'vibration' and cur_time_ms > next_sample[k]:
                    vibration = grovepi.analogRead(port)
                    if vibration == 1023:
                        data = 1
                    else:
                        data = 0
                    logging.debug("Reading Vibration " + str(data))
                    next_sample[k] = cur_time_ms + interval
                # Sound
                elif k == 'sound' and cur_time_ms > next_sample[k]:
                    data = grovepi.analogRead(port)
                    logging.debug("Reading Sound " + str(data))
                    next_sample[k] = cur_time_ms + interval
                # Gas MQ2
                elif k == 'gas_mq2' and cur_time_ms > next_sample[k]:
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
                else:
                    continue

            except Exception as ex:
                pass
            
            else:
                # Publish the data (if valid)
                if data is not None:
                    last_telemetry[topic] = data
		    last_telemetry["ID"]=iotsc_id
                    iotsc_client.publish(iotsc_topic_telemetry, json.dumps(last_telemetry), 1)
                    if cur_time > next_i3_publish :
                        next_i3_publish = cur_time + 15
			print last_telemetry
                        i3_client.publish(i3_topic, json.dumps(last_telemetry), 1)
                        eclipse_client.publish(i3_topic, json.dumps(last_telemetry), 1)


        else:
            continue

    # Update status of sensor
    iotsc_client.publish(iotsc_topic_attributes, json.dumps(last_attributes), 1)
    eclipse_client.publish(i3_topic, json.dumps(last_telemetry), 1)

