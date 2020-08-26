# sma-query
Python Script to query SMA Inverter Data via WebConnect and save the data to InfluxDB.

The script has been tested using a SMA Inverter SUNNY TRIPOWER 5.0 and SMA Enegry Meter.

It uses the WebConnect Login to query data via JSON API at configurable time interval (default 15s) and save the data into an InfluxDB.

Following data will be queried (but can be extended easily):

* Current Generated Power in W
* Current Power to Grid in W
* Current Power from Grid in W
* Current Power Consumption in W (calulated)
* Total Generated Power in Wh
* Total Power to Grid in Wh
* Total Power from Grid in Wh
* Total Power Consumption in Wh (calulated)
* Current DC Power in W of String A
* Current DC Power in V of String A
* Current DC Power in A of String A
* Current AC Power in W
* Current AC Frequency in Hz
* Current AC Power in A of Phase 1-3
* Current AC Power in V of Phase 1-3
* Current AC Power Generation in W of Phase 1-3
* Current AC Power Supply in W of Phase 1-3
* Current AC Power Acquisition in W of Phase 1-3
* Current AC Power Consumption in W of Phase 1-3 (calculated)

The script can be run directly using Python3 or placed into a Docker container. 

The wrapper script start.sh is needed to correctly perform logout from the SMA Inverter as without it the Sessions will remain forever blocking all of only 4 possible connections.


## Start Script without Container
```
python sma.py --influx_ip=192.168.1.3 --influx_port="8086" --influx_user="user" --influx_pw="pw" --sma_ip=192.168.1.2--sma_pw="pw" --influx_db="SMA" --interval=15 --write=0
```
Example Output:
```
2020-08-26 17:01:29.648563 Sessions OK: 2
2020-08-26 17:01:29.648563 Actual Time: 2020-08-26 17:01:29.648563 waiting for: 2020-08-26 17:01:30
2020-08-26 17:01:31.039033 Login on SMA Device successfull.
2020-08-26 17:01:31.664865 SMA Device Values:  {'sma_sn': '1234567890', 'solar_act': 500, 'einspeisung_act': 0, 'bezug_act': 50, 'solar_total': 100000, 'einspeisung_total': 50000, 'bezug_total': 50000, 'power_a': 500, 'voltage_a': 50000, 'current_a': 1000, 'power': 500, 'freq': 5000, 'current_1': 333, 'current_2': 333, 'current_3': 333, 'voltage_1': 23000, 'voltage_2': 23000, 'voltage_3': 23000, 'power_1': 166, 'power_2': 166, 'power_3': 167, 'supply_1': 0, 'supply_2': 0, 'supply_3': 0, 'acquisition_1': 50, 'acquisition_2': 0, 'acquisition_3': 0, 'consumption_act': 550, 'consumption_total': 50000, 'consumption_1': 200, 'consumption_2': 200, 'consumption_3': 150}
2020-08-26 17:01:46.651006 SMA Device Logout Successfull.
```


## Create Docker Container

```
mkdir sma-query
cd sma-query/
curl -O https://raw.githubusercontent.com/Froschie/sma-query/master/Dockerfile
curl -O https://raw.githubusercontent.com/Froschie/sma-query/master/start.sh
curl -O https://raw.githubusercontent.com/Froschie/sma-query/master/sma.py
docker build --tag sma-query .
```

## Start Docker Container via CMD Line
```
docker run -d --name sma-query --restart unless-stopped -e influx_ip=192.168.1.3 -e influx_port=8086 -e influx_user=user -e influx_pw=pw -e sma_ip=192.168.1.2 -e sma_pw=pw -e interval=15 sma-query
```


## Start Docker Container via Docker-Compose File
```
version: '3'

services:
  sma-query:
    image: sma-query:latest
    container_name: sma-query
    environment:
      - influx_ip=192.168.1.3
      - influx_por=8086
      - influx_user=user
      - influx_pw=pw
      - sma_ip=192.168.1.2
      - sma_pw=pw
      - interval=15
    restart: unless-stopped
```


PS: sorry for some mix of German and English names. That happened during translation and I was simply too lazy to adapt my already present InflusDB data.
