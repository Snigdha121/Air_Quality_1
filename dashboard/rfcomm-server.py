# file: rfcomm-server.py
# auth: Albert Huang <albert@csail.mit.edu>
# desc: simple demonstration of a server application that uses RFCOMM sockets
#
# $Id: rfcomm-server.py 518 2007-08-10 07:20:07Z albert $

from bluetooth import *
import sys
sys.path.insert(0,"/usr/local/lib/python2.7/dist-packages/paho-mqtt")

import paho.mqtt.client as mqttClient
import time
import json
import math
import os
import logging

sensor_data={}
sensor_data["temp"]=0
sensor_data["hum"]=0
sensor_data["light"]=0
sensor_data["gas_MQ2"]=0
sensor_data["gas_MQ3"]=0
sensor_data["gas_MQ5"]=0
sensor_data["gas_MQ9"]=0
sensor_data["sound"]=0


<<<<<<< HEAD
################Message Queue#####################
Transporter_Queue={} #Dictionary storing messages at the intermediate nodes (used while the phone drops the messages
Transporter_Queue["Blue"]={}
#Transporter_Queue["Blue"]["Latency"]=0
Transporter_Queue["Red"]=0
Transporter_Queue["Green"]=0

=======
>>>>>>> 8bf21a84e3009ab4372a05be7b6fa06233d3b8cf

time.sleep(5)

os.system('sudo hciconfig hci0 piscan')

##MQTT connection handler##################### 
def on_connect(client, userdata, flags, rc):
 
    if rc == 0:
 
        logging.info("Connected to broker")
 
        global Connected                #Use global variable
        Connected = True                #Signal connection 
 
    else:
 
        logging.critical("Connection failed")
 

Connected = False   #global variable for the state of the connection


#logging setup
logging.basicConfig(filename="/home/pi/iotsc/dashboard/bth.log", level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filemode='w')


####MQTT broker configuration############################################ 
broker_address= "localhost"  #Broker address
#port = 1883                         #Broker port
#user = "yourUser"                    #Connection username
#password = "yourPassword"            #Connection password


def on_message(client, userdata, message):
    global sensor_data
    #print "##################################"
    #print "Message topic: " + message.topic
    #print "Message topic: " + message.payload
    input=json.loads(message.payload)
    if "temperature_interior" in input:
	sensor_data["temp"]=input["temperature_interior"]
    if "light" in input:
	sensor_data["light"]=input["light"]
    if "humidity" in input:
	sensor_data["hum"]=input["humidity"]
    if "Sound" in input:
	sensor_data["sound"]=input["Sound"]
    if "gas_mq2" in input:
	sensor_data["gas_MQ2"]=input["gas_mq2"]
    if "gas_mq3" in input:
	sensor_data["gas_MQ3"]=input["gas_mq3"]
    if "gas_mq5" in input:
	sensor_data["gas_MQ5"]=input["gas_mq5"]
    if "gas_mq9" in input:
	sensor_data["gas_MQ9"]=input["gas_mq9"]
    #print sensor_data
    return
 

########Init MQTT############################
client = mqttClient.Client("Python")               #create new instance
#client.username_pw_set(user, password=password)    #set username and password
client.on_connect= on_connect                      #attach function to callback
client.on_message= on_message                      #attach function to callback

######Connecting to broker###################### 
client.connect(broker_address)          #connect to broker
 
client.loop_start()        #start the loop
 
while Connected != True:    #Wait for connection
    time.sleep(0.1)
 
client.subscribe("USC/#")
 

server_sock=BluetoothSocket( RFCOMM )
server_sock.bind(("",PORT_ANY))
server_sock.listen(1)

port = server_sock.getsockname()[1]

uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"

advertise_service( server_sock, "SampleServer",
                   service_id = uuid,
                   service_classes = [ uuid, SERIAL_PORT_CLASS ],
                   profiles = [ SERIAL_PORT_PROFILE ], 
#                   protocols = [ OBEX_UUID ] 
                    )
                   
logging.info("Waiting for connection on RFCOMM channel")

#client_sock, client_info = server_sock.accept()
#print "Accepted connection from ", client_info

while True:
	try:
		client_sock, client_info = server_sock.accept()
		#print "Accepted connection from ", client_info
		logging.info("Accepted connection from %s",str(client_info))
		data = client_sock.recv(1024)
		logging.info("Message Received is %s",str(data))
		while data != "disconnect":
			if len(data) == 0: break
			if data == "data":
				#print json.dumps(sensor_data)
<<<<<<< HEAD
				sensor_data["timestamp"]=str(int(round(time.time() * 1000)))
				logging.info("Timestamp is %s",str(sensor_data["timestamp"]))
				client_sock.send(json.dumps(sensor_data))
			if data == "reboot":
				os.system('sudo shutdown -r now')
			if data == "survey":
				data = client_sock.recv(1024)
				logging.info("Message Received is %s",str(data))
				payload={'total_credit': 7.89, 'mid': 1, 'credit_earned': 0.65}
				client_sock.send(json.dumps(payload))
				break
			if data == "packet":
				data = client_sock.recv(1024)
				logging.info("Message Received is %s",str(data))
				payload={'packet_present':0}
				logging.info("Queue lenght is %s",str(Transporter_Queue[str(data)]))
				if len(Transporter_Queue[str(data)]) != 0:
					payload={'packet_present':len(Transporter_Queue[str(data)])}
				client_sock.send(json.dumps(payload))
			if data == "get_packet":
				data = client_sock.recv(1024)
				logging.info("Message Received is %s",str(data))
				if len(Transporter_Queue[str(data)]) != 0:
					client_sock.send(json.dumps(Transporter_Queue[str(data)]))
				break
			if data == "drop":
				data = client_sock.recv(1024)
				logging.info("Message Received is %s",str(data))
				data=json.loads(data)

				if "team" in data:
					logging.info("Team is %s",data['team'])
					print data['team']
					if str(data['team']) == "blue":
						Transporter_Queue["Blue"]=data
						Transporter_Queue["Blue"]["Latency"]=0
						Transporter_Queue["Blue"]["Latency"]=(int(round(time.time()*1000)))-int(data["timestamp"])
						logging.info("Latency is %s",str(Transporter_Queue["Blue"]["Latency"]))
						logging.info("Blue Queue contains %s",str(Transporter_Queue["Blue"]))
						
				payload={'Latency': str(Transporter_Queue["Blue"]["Latency"])}
				client_sock.send(json.dumps(payload))
				break		
			if str(data) == "disconnect": #this if statement is not becoming true
				logging.info("Exiting the loop")
				#client_sock.close()
				break
			data = client_sock.recv(1024)
			logging.info("Message Received is %s",str(data))
		logging.info("Outside the while loop")
		#client_sock.close()
=======
				client_sock.send(json.dumps(sensor_data))
			if data == "reboot":
				os.system('sudo shutdown -r now')
			if data == "disconnect":
				logging.info("Exiting the loop")
				client_sock.close()
				break
			data = client_sock.recv(1024)
			logging.info("Message Received is %s",str(data))
		client_sock.close()
>>>>>>> 8bf21a84e3009ab4372a05be7b6fa06233d3b8cf
	except IOError:
    		pass
		client_sock.close()

logging.info("disconnected")
server_sock.close()
logging.info("all done")