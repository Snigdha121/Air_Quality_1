IoTSC InfluxDB Docker Setup

 * InfluxDB URL: eclipse.usc.edu:10002
 * Current Version: 1.3.6
 * UN: iotsc
 * PW: anrguscinfluxdb

To start the server with the config file included in this repo, run the
following command in the directory where the custom influxdb.conf lives:

	docker run -d --restart="always" --name iotsc-influxdb -p 10002:8086 -v /home/iotsc/chariot-influxdb-data:/var/lib/influxdb -v $PWD/influxdb.conf:/etc/influxdb/influxdb.conf:ro influxdb:1.3.6

The `:ro` means read only. Authentication enabled in influxdb.conf, and 
only one user has been created (`iotsc`) with admin rights in the 
current instance. Here's an example of how to use the HTTP API:

	curl -G http://eclipse.usc.edu:10002/query -u iotsc:anrguscinfluxdb --data-urlencode "q=SHOW USERS"

