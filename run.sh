#!/usr/bin/with-contenv bash

python3 -u /sma.py --sma_ip $sma_ip --sma_pw $sma_pw --sma_mode $sma_mode --influx_ip $influx_ip --influx_port $influx_port --influx_user $influx_user --influx_pw $influx_pw --influx_db $influx_db --interval $interval --write $write
