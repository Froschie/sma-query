FROM python:slim

# Image Description
LABEL version="1.0" description="Script to Query data from SMA Device and store it to InfluxDB"

# Install required Python Modules
RUN pip install influxdb requests

# Install pgrep for stopping the Python Script in case needed
RUN apt-get update && apt-get install -y procps htop dos2unix

# Define Environment Variables needed for Script
ENV sma_ip="192.168.1.2" sma_pw="pw" influx_ip="192.168.1.3" influx_port="8086" influx_user="user" influx_pw="pw" influx_db="SMA" interval="30"

# Set correct Timezone
RUN ln -sf /usr/share/zoneinfo/Europe/Berlin /etc/localtime

# Copy Scriptis to Container
ADD ./sma.py /sma.py
ADD ./start.sh /start.sh
RUN chmod +x /start.sh && dos2unix /start.sh
RUN mkdir /logs

# Default Command for starting the Container
CMD ["/start.sh"]
