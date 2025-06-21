# encoding: utf-8
import json
import time
from datetime import datetime, timedelta
import requests
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
from influxdb import InfluxDBClient
import argparse
import sys
import signal
import os
import logging

parser=argparse.ArgumentParser(
    description='''Script for Query SMA Values.''')
parser.add_argument('--sma_ip', type=str, required=True, default="", help='IP of the SMA Device.')
parser.add_argument('--sma_pw', type=str, required=True, default="", help='Password of the SMA Device.')
parser.add_argument('--sma_mode', type=str, required=False, default="https", choices=["http", "https"], help='HTTP Mode for accessing the WebConnect Interface.')
parser.add_argument('--influx_ip', type=str, required=True, default="", help='IP of the Influx DB Server.')
parser.add_argument('--influx_port', type=str, required=True, default="", help='Port of the Influx DB Server.')
parser.add_argument('--influx_user', type=str, required=True, default="", help='User of the Influx DB Server.')
parser.add_argument('--influx_pw', type=str, required=True, default="", help='Password of the Influx DB Server.')
parser.add_argument('--influx_db', type=str, required=True, default="", help='DB name of the Influx DB Server.')
parser.add_argument('--influx_bat_ip', type=str, required=False, default="", help='IP of the Influx DB Server for Battery.')
parser.add_argument('--influx_bat_port', type=str, required=False, default="", help='Port of the Influx DB Server for Battery.')
parser.add_argument('--influx_bat_user', type=str, required=False, default="", help='User of the Influx DB Server for Battery.')
parser.add_argument('--influx_bat_pw', type=str, required=False, default="", help='Password of the Influx DB Server for Battery.')
parser.add_argument('--influx_bat_db', type=str, required=False, default="", help='DB name of the Influx DB Server for Battery.')
parser.add_argument('--bat_measurement', type=str, required=False, default="", help='Name of the Influx DB Measurement for Battery.')
parser.add_argument('--bat_dev_name', type=str, required=False, default="", help='Name of the Device Name for Battery.')
parser.add_argument('--bat_value_power', type=str, required=False, default="", help='Name of the Value name for Discharging/Charging Power of Battery.')
parser.add_argument('--bat_total_consumption', type=str, required=False, default="", help='Name of the Value name total Consumption for Battery.')
parser.add_argument('--bat_total_feed', type=str, required=False, default="", help='Name of the Value name total Feed for Battery.')
parser.add_argument('--interval', type=float, required=False, default="30.0", help='Interval in Seconds to query and save the data.')
parser.add_argument('--write', type=int, required=False, default=1, choices=[0, 1], help='Specify if Data should be written to InfluxDB or not.')
parser.add_argument('--log', type=str, required=False, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help='Specify Log output.')
args=parser.parse_args()

ip = args.sma_ip
pw = args.sma_pw
mode = args.sma_mode

# Log Output configuration
logging.basicConfig(level=getattr(logging, args.log), format='%(asctime)s.%(msecs)05d %(levelname)07s:\t%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
log = logging.getLogger(__name__)

# Load Measurement Configuration
# Definition of SMA Measurements
try:
    for filename in ["config_measurements.json", "/config_measurements.json"]:
        if os.path.isfile(filename):
            with open(filename) as json_data_file:
                measurements = json.load(json_data_file)
                break
    measurement_list = {}
    for measurement in measurements:
        if measurements[measurement]['active'] == True:
            measurement_list[measurement] = measurements[measurement]
except Exception as e:
    log.error("config_measurements.json file could not be opened or is not valid JSON file!")
    log.error(e)
    time.sleep(60)    
    sys.exit(1)

# Load Constant Queries Configuration
# definition of continous queries for faster statistics
try:
    for filename in ["config_queries.json", "/config_queries.json"]:
        if os.path.isfile(filename):
            with open(filename) as json_data_file:
                continuous_queries = json.load(json_data_file)
                break
    for query in continuous_queries:
        continuous_queries[query] = continuous_queries[query].replace("+influx_db+", args.influx_db)
except:
    log.error("config_queries.json file could not be opened or is not valid JSON file!")
    time.sleep(60)    
    sys.exit(1)

measurement_groups = {}
for measurement in measurement_list:
    if measurement_list[measurement]['group'] is not None:
        measurement_groups[measurement_list[measurement]['group']] = {}
        measurement_groups[measurement_list[measurement]['group']]['measurement'] = measurement_list[measurement]['group']

# Download of SMA Language File
url = mode + "://" + ip + "/data/l10n/en-US.json"
response = requests.request("GET", url, verify=False, timeout=(3, 10))
descriptions = response.json()

# Catch Stopping the Docker Container
def handler_stop_signals(signum, frame):
    global sid
    global ip
    if logout(ip, sid, mode):
        log.info("SMA Device Logout Successfull.")
    else:
        log.error("SMA Device Logout Failed.")
    log.warning("Container Stopping...")
    sys.exit(0)
signal.signal(signal.SIGINT, handler_stop_signals)
signal.signal(signal.SIGTERM, handler_stop_signals)

# Login Function
def login(ip, pw, mode):
    url = mode + "://" + ip + "/dyn/login.json"
    payload = "{\"right\":\"usr\",\"pass\":\"" + pw + "\"}"
    try:
        response = requests.request("POST", url, data = payload, verify=False, timeout=(3, 10))
        log.debug(response.json())
        log.debug(response.status_code)
        if response.status_code == 200:
            if "result" in response.json():
                return response.json()['result']['sid']
        return None
    except:
        return None

# Logout Function
def logout(ip, sid, mode):
    url = mode + "://" + ip + "/dyn/logout.json?sid=" + sid
    response = requests.request("POST", url, data = "{}", verify=False, timeout=(3, 10))
    if response.status_code == 200:
        return True
    else:
        return False

# SMA Value Query
def query_values(ip, mode):
    # check Battery Charging or Discharging
    if args.influx_bat_ip:
        client_bat = InfluxDBClient(host=args.influx_bat_ip, port=args.influx_bat_port, username=args.influx_bat_user, password=args.influx_bat_pw)
        client_bat.switch_database(args.influx_bat_db)

        points = client_bat.query(f'SELECT last({args.bat_value_power}) FROM {args.bat_measurement} WHERE device=\'{args.bat_dev_name}\'').get_points()
        for point in points:
            if point["last"] >= 0:
                battery_charging = int(point["last"])
                battery_discharging = 0
            else:
                battery_charging = 0
                battery_discharging = int(point["last"] * -1)

        points = client_bat.query(f'SELECT last({args.bat_total_consumption}) FROM {args.bat_measurement} WHERE device=\'{args.bat_dev_name}\'').get_points()
        for point in points:
            battery_total_consumption = int(float(point["last"]) * 1000)
        points = client_bat.query(f'SELECT last({args.bat_total_feed}) FROM {args.bat_measurement} WHERE device=\'{args.bat_dev_name}\'').get_points()
        for point in points:
            battery_total_feed = int(float(point["last"]) * 1000)
        client_bat.close()
    else:
        battery_charging = 0
        battery_discharging = 0
        battery_total_consumption = 0
        battery_total_feed = 0
    global sid
    global pw
    global descriptions
    url = mode + "://" + ip + "/dyn/getValues.json?sid=" + sid
    payload = {"destDev": [], "keys ": [] }
    measurements = []
    for measurement in measurement_list:
        if measurement_list[measurement]['key'] not in measurements and measurement_list[measurement]['key'] is not None:
            measurements.append(measurement_list[measurement]['key'])
    payload = json.dumps({"destDev": [], "keys": measurements})
    try:
        response = requests.request("POST", url, data = payload, verify=False, timeout=(3, 10))
        log.debug(response.json())
        log.debug(response.status_code)
        if "err" in response.json():
            if response.json()['err'] == 401:
                # Login on SMA Device
                sid = login(ip, pw, mode)
                while not sid:
                    log.error("Login on SMA Device (" + ip + ") failed.")
                    time.sleep(60)
                    sid = login(ip, pw, mode)
                log.info("Login on SMA Device successfull.")
        else:
            for id in response.json()['result']:
                sma_data = response.json()['result'][id]
    except:
        log.error("Query Failed...")

    values = {}
    for measurement in measurement_list:
        if measurement_list[measurement]['key'] is not None:
            key = measurement_list[measurement]['key']
            typ = measurement_list[measurement]['type']
            val = measurement_list[measurement]['val']
            if typ == "int":
                try:
                    for id in sma_data[key]:
                        values[measurement] = int(sma_data[key][id][val]['val'])
                except:
                    values[measurement] = 0
            elif typ == "calc":
                values[measurement] = 0
            elif typ == "tag":
                try:
                    for id in sma_data[key]:
                        values[measurement] = descriptions[str(sma_data[key][id][val]['val'][0]['tag'])]
                except:
                    values[measurement] = str("-")
            else:
                try:
                    for id in sma_data[key]:
                        values[measurement] = str(sma_data[key][id][val]['val'])
                except:
                    values[measurement] = str("-")
    for measurement in measurement_list:
        typ = measurement_list[measurement]['type']
        if typ == "calc":
            try:
                values[measurement] = values[measurement_list[measurement]['field1']]-values[measurement_list[measurement]['field2']]+values[measurement_list[measurement]['field3']]
                if "battery" in measurement_list[measurement]:
                    if measurement_list[measurement]['group'] == "actuals" or measurement_list[measurement]['group'] == "phases":
                        values[measurement] = values[measurement] + battery_discharging - battery_charging
                    elif measurement_list[measurement]['group'] == "totals":
                        values[measurement] = values[measurement] + battery_total_feed - battery_total_consumption
            except:
                pass
        if typ == "battery":
            try:
                values[measurement] = locals()[measurement_list[measurement]['field1']]
            except:
                pass
    return values

# Session Check Function
def session_check(ip, mode):
    url = mode + "://" + ip + "/dyn/sessionCheck.json"
    try:
        response = requests.request("POST", url, data = "{}", verify=False, timeout=(3, 10))
    except:
        return (False, "No response from SMA Device (" + ip + ")!")
    #log.debug(response.json())
    if response.status_code == 200:
        if "result" in response.json():
            if "cntFreeSess" in response.json()['result']:
                if response.json()['result']['cntFreeSess'] > 0:
                    return (True, "Sessions OK: " + str(response.json()['result']['cntFreeSess']))
                else:
                    return (False, "No free Session on SMA Device (" + ip + ")!")
    return (False, "Error in Response from SMA Device (" + ip + ")!")

# Time Rounding Function
def ceil_time(ct, delta):
    return ct + (datetime.min - ct) % delta

# Check for Free Session on SMA Device
session_status = session_check(ip, mode)
while not session_status[0]:
    log.error(session_status[1])
    time.sleep(10)
    session_status = session_check(ip, mode)
log.info(session_status[1])

now = datetime.now()
new_time = ceil_time(now, timedelta(seconds=int(args.interval)))

log.info("Actual Time: " + str(now) + " waiting for: " + str(new_time))

# Wait for Full Minute / Half Minute
while now < new_time:
    time.sleep(0.5)
    now = datetime.now()

client = InfluxDBClient(host=args.influx_ip, port=args.influx_port, username=args.influx_user, password=args.influx_pw)

# Login on SMA Device
sid = login(ip, pw, mode)
while not sid:
    log.error("Login on SMA Device (" + ip + ") failed.")
    time.sleep(60)
    sid = login(ip, pw, mode)
log.info("Login on SMA Device successfull.")

# Execute Query every Xs
solar_values_last = {}
try:
    while True:
        solar_values = query_values(ip, mode)
        log.debug("SMA Device Values: " + str(solar_values))
        # Connect to InfluxDB and save Solar Values
        try:
            client = InfluxDBClient(host=args.influx_ip, port=args.influx_port, username=args.influx_user, password=args.influx_pw)
            #log.debug(client.get_list_database())
            if not {'name': args.influx_db} in client.get_list_database():
                client.create_database(args.influx_db)
                log.info("InfluxDB (" + str(args.influx_db) + ") created.")
            client.switch_database(args.influx_db)
            # check for correct continous query configuration
            queries = client.get_list_continuous_queries()
            for db in queries:
                if list(db.keys())[0] == args.influx_db:
                    for query in db[args.influx_db]:
                        if query['name'] in continuous_queries:
                            if query['query'] == continuous_queries[query['name']]:
                                continuous_queries.pop(query['name'])
                            else:
                                client.drop_continuous_query(query['name'], database=args.influx_db)
                                log.info("Incorrect Continuous Query dropped: " + str(query['name']))
            for query in continuous_queries:
                influx_query = client.query(continuous_queries[query])
                log.info("Added Continuous Query: " + str(query) + " Result: " + str(influx_query))
                sel_start = continuous_queries[query].find("SELECT")
                sel_end = continuous_queries[query].find("END")
                sel_query = continuous_queries[query][sel_start:sel_end]
                influx_query = client.query(sel_query)
                log.info("Filled Statistical Tables for: " + str(query) + " Result: " + str(influx_query))

            # Write Solar data to InfluxDB 
            try:
                # Workaround for missing / wrong (lower) total values after SMA restart
                if "solar_total" in measurement_list:
                    points = client.query('SELECT last(solar_total) FROM totals').get_points()
                    for point in points:
                        solar_values_last['solar_total'] = point['last']
                    if 'solar_total' in solar_values_last:
                        if solar_values['solar_total'] < solar_values_last['solar_total']:
                            solar_values['solar_total'] = solar_values_last['solar_total']
                            solar_values['consumption_total'] = solar_values['solar_total']-solar_values['einspeisung_total']+solar_values['bezug_total']
                    points = client.query('SELECT last(bezug_total) FROM totals').get_points()
                    for point in points:
                        solar_values_last['bezug_total'] = point['last']
                    if 'bezug_total' in solar_values_last:
                        if solar_values['bezug_total'] < solar_values_last['bezug_total']:
                            solar_values['bezug_total'] = solar_values_last['bezug_total']
                            solar_values['consumption_total'] = solar_values['solar_total']-solar_values['einspeisung_total']+solar_values['bezug_total']
                    points = client.query('SELECT last(einspeisung_total) FROM totals').get_points()
                    for point in points:
                        solar_values_last['einspeisung_total'] = point['last']
                    if 'einspeisung_total' in solar_values_last:
                        if solar_values['einspeisung_total'] < solar_values_last['einspeisung_total']:
                            solar_values['einspeisung_total'] = solar_values_last['einspeisung_total']
                            solar_values['consumption_total'] = solar_values['solar_total']-solar_values['einspeisung_total']+solar_values['bezug_total']
                # Generating the JSON for writing the Influx DB data
                json_body = []
                for group in measurement_groups:
                    temp_body = {
                        "measurement": str(group),
                        "tags": {
                            "serial": str(solar_values['sma_sn']),
                            "device": str(solar_values['sma_type'])
                        },
                        "time": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                        "fields": {}
                    }
                    for measurement in measurement_list:
                        if measurement_list[measurement]['group'] == group:
                            if solar_values[measurement] is not None:
                                temp_body['fields'][measurement] = solar_values[measurement]
                    if str(solar_values['sma_sn']) != "unknown" and str(solar_values['sma_sn']) != "-" and str(solar_values['sma_type']) != "unknown" and str(solar_values['sma_type']) != "-":
                        json_body.append(temp_body)
                    else:
                        log.error("Incorrect Serial Number / Device Type, skipping data, SN: " + str(solar_values['sma_sn']) + ", Device: " + str(solar_values['sma_type']))
                log.debug("InfluxDB write data DEBUG:" + str(json_body))
                if args.write == 1:
                    influx_result = client.write_points(json_body)
                    if influx_result:
                        log.debug("InfluxDB write data successfull:" + str(json_body))
                    else:
                        log.error("InfluxDB write data FAILED:" + str(json_body))
                        log.error(influx_result)
                #solar_values_last = solar_values
            except Exception as e:
                log.error("InfluxDB error writing the Solar Values")
                log.error(e)
            finally:
                client.close()
        except Exception as e:
            log.error("InfluxDB connection failed (%s@%s)." % (args.influx_ip, args.influx_port))

        time.sleep(args.interval - ((time.time() - new_time.timestamp()) % args.interval))
except KeyboardInterrupt:
    log.warning("Script aborted...")
finally:
    if logout(ip, sid, mode):
        log.info("SMA Device Logout Successfull.")
    else:
        log.error("SMA Device Logout Failed.")
