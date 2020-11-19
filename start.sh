#!/bin/bash
python -u /sma.py --sma_ip $sma_ip --sma_pw $sma_pw --sma_mode $sma_mode --influx_ip $influx_ip --influx_port $influx_port --influx_user $influx_user --influx_pw $influx_pw --influx_db $influx_db --interval $interval &
child=$(pgrep -P $$)
echo "Python Script started as process: " $child

cleanup() {
    echo "Stopping Python Script" $child
    kill -TERM $child
    sleep 10s
    exit
}

trap cleanup INT TERM

while :; do
    sleep 1s
done
