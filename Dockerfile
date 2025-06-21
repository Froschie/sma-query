# first build Alpine Base Image with Init
FROM alpine:3.12
ARG TARGETPLATFORM
RUN apk add --no-cache bash curl tzdata
COPY ./s6download.sh /s6download.sh
RUN chmod +x /s6download.sh && bash /s6download.sh && tar xfz /tmp/s6overlay.tar.gz -C / && rm /tmp/s6overlay.tar.gz && rm /s6download.sh
ENTRYPOINT ["/init"]

# Image Description
LABEL version="4.0" description="Script to Query data from SMA Device and store it to InfluxDB"

# Install Python and Python Modules
RUN apk add --no-cache python3 py-pip && pip install influxdb && apk del py-pip && apk add py3-requests py3-msgpack

# Define Environment Variables needed for Script
ENV sma_ip="192.168.1.2" sma_pw="pw" sma_mode="https" influx_ip="192.168.1.3" influx_port="8086" influx_user="user" influx_pw="pw" influx_db="SMA" interval="30" influx_bat_ip="192.168.1.3"  influx_bat_port="8086" influx_bat_db="db" influx_bat_user="user" influx_bat_pw="pw" bat_measurement="meas" bat_dev_name="name" bat_value_power="power" bat_total_consumption="consumption" bat_total_feed="feed" log="INFO"

# Startup Script to Container
RUN mkdir -p /etc/services.d/pv-query
COPY ./run.sh /etc/services.d/pv-query/run

# Copy Scriptis to Container
ADD ./sma.py ./config_measurements.json ./config_queries.json /
