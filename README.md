# sma-query
Python Script to query SMA Inverter via WebConnect


## Create Docker Container

```
mkdir sma-query && cd sma-query/
curl -O https://raw.githubusercontent.com/Froschie/sma-query/master/Dockerfile
curl -O https://raw.githubusercontent.com/Froschie/sma-query/master/start.sh
curl -O https://raw.githubusercontent.com/Froschie/sma-query/master/sma.py
docker build --tag sma-query .
```

## Start Docker Container via CMD Line
```
docker run -d --name sma-query --restart unless-stopped -e influx_ip=192.168.1.3 -e influx_port="8086" -e influx_user="user" -e influx_pw="pw" -e sma_ip=192.168.1.2 -e sma_pw="pw" -e interval=15 sma-query
```

## Start Docker Container via Docker-Compose File
```
version: '3'

services:
  sma-query:
    image: sma-query:latest
    container_name: sma-query
    environment:
      - influx_ip="192.168.1.3"
      - influx_port="8086"
      - influx_user="user"
      - influx_pw="pw"
      - sma_ip="192.168.1.2"
      - sma_pw="pw"
      - interval="15"
    restart: unless-stopped
```
