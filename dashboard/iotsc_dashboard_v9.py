from grove import grovepi
from grove import grove_light_sensor
import paho.mqtt.client as mqtt
import time
import math
import Adafruit_GPIO.SPI as SPI
import Adafruit_MCP3008
import json
import logging
import configparser
import argparse

# Parse the arguments
parser = argparse.ArgumentParser()
parser.add_argument("output_file", help="Output file for log/debug")
parser.add_argument("input_file", help="Input file with configurations")
args = parser.parse_args()

# Logging setup
logging.basicConfig(filename=args.output_file, level=logging.DEBUG, 
                    format='%(asctime)s %(levelname)s %(message)s',
                    filemode='w')

# Configuration file
settings = configparser.ConfigParser()
settings.read(args.input_file)

# Broker parameters (from config file)
iotsc_broker = str(settings.get('dashboard', 'url'))
iotsc_access_token = str(settings.get('dashboard', 'access_token'))
iotsc_topic_telemetry = str(settings.get('dashboard', 'topic_telemetry'))
iotsc_topic_attributes = str(settings.get('dashboard', 'topic_attributes'))

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
    grove_light_sensor.init()
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
    gas_sensors = Adafruit_MCP3008.MCP3008(spi=SPI.SpiDev(0, 1))

# Attributes and Telemetry dictionaries
last_attributes = {}
last_telemetry = {}
next_sample = {}

# MQTT callback function after connection
def on_connect(client, userdata, flags, rc):
    logging.info('Connected flags ' + str(flags) + ' Result code ' + str(rc) + ' Client_id  ' + str(client))

# MQTT callback function when a message is received
def on_message(client, userdata, msg):
    logging.info("Message received  " + msg.topic + " " + msg.payload)

# Connecting to IoTSc broker
iotsc_client = mqtt.Client()
iotsc_client.on_connect = on_connect
iotsc_client.on_message = on_message
iotsc_client.username_pw_set(iotsc_access_token)

try:    
    logging.info('Connecting to broker')
    iotsc_client.connect(iotsc_broker, 2883, 60)
    iotsc_client.loop_start()
except Exception as e:
    logging.critical('Exception' + str(e))

# Initialize the dictionary of next sample timestamp
cur_time_ms = int(time.time() * 1000)
for k,v in sensors.items():
    next_sample[k] = cur_time_ms + v[4]

while True:
    for k,v in sensors.items():
        sensor_type = v[1]
        if sensor_type == 'sensor':
            topic = v[0]
            port = v[3]
            interval = v[4]
            data = None

            cur_time_ms = int(time.time() * 1000)
            try:
                # DHT Temp
                if k == 'dht_temp' and cur_time_ms > next_sample[k]:
                    [temp, hum] = grovepi.dht(port, 1)
                    if not math.isnan(temp):
                        data = temp
                        logging.debug("Reading DHT temp " + str(data))
                        next_sample[k] = cur_time_ms + interval
                # DHT Hum
                if k == 'dht_hum' and cur_time_ms > next_sample[k]:
                    [temp, hum] = grovepi.dht(port, 1)
                    if not math.isnan(hum):
                        data = hum
                        logging.debug("Reading DHT hum " + str(data))
                        next_sample[k] = cur_time_ms + interval
                # Temperature interior
                elif k == 'temp_interior' and cur_time_ms > next_sample[k]:
                    data = round(float(grovepi.temp(port, '1.2')), 2)
                    logging.debug("Reading Temperature Interior " + str(data))
                    next_sample[k] = cur_time_ms + interval
                # Temperature exterior
                elif k == 'temp_exterior' and cur_time_ms > next_sample[k]:
                    data = round(float(grovepi.temp(port, '1.2')), 2)
                    logging.debug("Reading Temperature Exterior " + str(data))
                    next_sample[k] = cur_time_ms + interval
                # Light Digital
                elif k == 'light_digital' and cur_time_ms > next_sample[k]:
                    data = grove_light_sensor.readVisibleLux()
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
                        data = water
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
                    data = gas_sensors.read_adc(port)
                    logging.debug("Reading Gas MQ2 " + str(data))
                    next_sample[k] = cur_time_ms + interval
                # Gas MQ3
                elif k == 'gas_mq3' and cur_time_ms > next_sample[k]:
                    data = gas_sensors.read_adc(port)
                    logging.debug("Reading Gas MQ3 " + str(data))
                    next_sample[k] = cur_time_ms + interval
                # Gas MQ5
                elif k == 'gas_mq5' and cur_time_ms > next_sample[k]:
                    data = gas_sensors.read_adc(port)
                    logging.debug("Reading Gas MQ5 " + str(data))
                    next_sample[k] = cur_time_ms + interval
                # Gas MQ9
                elif k == 'gas_mq9' and cur_time_ms > next_sample[k]:
                    data = gas_sensors.read_adc(port)
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
                    iotsc_client.publish(iotsc_topic_telemetry, json.dumps(last_telemetry), 1)
        else:
            continue

    # Update status of sensor
    iotsc_client.publish(iotsc_topic_attributes, json.dumps(last_attributes), 1)
