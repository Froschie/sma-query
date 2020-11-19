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

# Definition of SMA Measurements
# Mandatory
measurement_list = {}
# einspeisung = supply
measurement_list['sma_sn'] = {'key': "6800_00A21E00", 'group': None, 'type': str, 'val': 0, 'name': "Serial Number of Inverter"}
measurement_list['solar_act'] = {'key': "6100_40263F00", 'group': "actuals", 'type': int, 'val': 0, 'name': "Current Solar Power in W"}
measurement_list['einspeisung_act'] = {'key': "6100_40463600", 'group': "actuals", 'type': int, 'val': 0, 'name': "Current Supply Power in W "}
measurement_list['bezug_act'] = {'key': "6100_40463700", 'group': "actuals", 'type': int, 'val': 0, 'name': "Current Input Power in W"}
measurement_list['consumption_act'] = {'key': None, 'group': "actuals", 'type': int, 'val': 0, 'name': "Current Consumption Power in W"}
measurement_list['solar_total'] = {'key': "6400_0046C300", 'group': "totals", 'type': int, 'val': 0, 'name': "Total Solar Power in Wh"}
measurement_list['einspeisung_total'] = {'key': "6400_00462400", 'group': "totals", 'type': int, 'val': 0, 'name': "Total Supply Power in Wh"}
measurement_list['bezug_total'] = {'key': "6400_00462500", 'group': "totals", 'type': int, 'val': 0, 'name': "Total Input Power in Wh"}
measurement_list['consumption_total'] = {'key': None, 'group': "totals", 'type': int, 'val': 0, 'name': "Total Consumption Power in Wh"}
# Optional, following measurements can be activated/deactivated or custom ones added:
measurement_list['power_a'] = {'key': "6380_40251E00", 'group': "dc", 'type': int, 'val': 0, 'name': "Current DC Power in W of String A"}
#measurement_list['power_b'] = {'key': "6380_40251E00", 'group': "dc", 'type': int, 'val': 1, 'name': "Current DC Power in W of String B"}
measurement_list['voltage_a'] = {'key': "6380_40451F00", 'group': "dc", 'type': int, 'val': 0, 'name': "Current DC Power in V of String A"}
#measurement_list['voltage_b'] = {'key': "6380_40451F00", 'group': "dc", 'type': int, 'val': 1, 'name': "Current DC Power in V of String A"}
measurement_list['current_a'] = {'key': "6380_40452100", 'group': "dc", 'type': int, 'val': 0, 'name': "Current DC Power in A of String A"}
#measurement_list['current_b'] = {'key': "6380_40452100", 'group': "dc", 'type': int, 'val': 1, 'name': "Current DC Power in A of String A"}
measurement_list['power'] = {'key': "6100_40263F00", 'group': "ac", 'type': int, 'val': 0, 'name': "Current AC Power in W"}
measurement_list['freq'] = {'key': "6100_00465700", 'group': "ac", 'type': int, 'val': 0, 'name': "Current AC Frequency in Hz"}
measurement_list['current_1'] = {'key': "6100_40465300", 'group': "ac", 'type': int, 'val': 0, 'name': "Current AC Power in A of Phase 1"}
measurement_list['current_2'] = {'key': "6100_40465400", 'group': "ac", 'type': int, 'val': 0, 'name': "Current AC Power in A of Phase 2"}
measurement_list['current_3'] = {'key': "6100_40465500", 'group': "ac", 'type': int, 'val': 0, 'name': "Current AC Power in A of Phase 3"}
measurement_list['voltage_1'] = {'key': "6100_00464800", 'group': "ac", 'type': int, 'val': 0, 'name': "Current AC Power in V of Phase 1"}
measurement_list['voltage_2'] = {'key': "6100_00464900", 'group': "ac", 'type': int, 'val': 0, 'name': "Current AC Power in V of Phase 2"}
measurement_list['voltage_3'] = {'key': "6100_00464A00", 'group': "ac", 'type': int, 'val': 0, 'name': "Current AC Power in V of Phase 3"}
measurement_list['power_1'] = {'key': "6100_40464000", 'group': "phases", 'type': int, 'val': 0, 'name': "Current AC Power Generation in W of Phase 1"}
measurement_list['power_2'] = {'key': "6100_40464100", 'group': "phases", 'type': int, 'val': 0, 'name': "Current AC Power Generation in W of Phase 2"}
measurement_list['power_3'] = {'key': "6100_40464200", 'group': "phases", 'type': int, 'val': 0, 'name': "Current AC Power Generation in W of Phase 3"}
measurement_list['supply_1'] = {'key': "6100_0046E800", 'group': "phases", 'type': int, 'val': 0, 'name': "Current AC Power Supply in W of Phase 1"}
measurement_list['supply_2'] = {'key': "6100_0046E900", 'group': "phases", 'type': int, 'val': 0, 'name': "Current AC Power Supply in W of Phase 2"}
measurement_list['supply_3'] = {'key': "6100_0046EA00", 'group': "phases", 'type': int, 'val': 0, 'name': "Current AC Power Supply in W of Phase 3"}
measurement_list['acquisition_1'] = {'key': "6100_0046EB00", 'group': "phases", 'type': int, 'val': 0, 'name': "Current AC Power Acquisition in W of Phase 1"}
measurement_list['acquisition_2'] = {'key': "6100_0046EC00", 'group': "phases", 'type': int, 'val': 0, 'name': "Current AC Power Acquisition in W of Phase 2"}
measurement_list['acquisition_3'] = {'key': "6100_0046ED00", 'group': "phases", 'type': int, 'val': 0, 'name': "Current AC Power Acquisition in W of Phase 3"}
measurement_list['consumption_1'] = {'key': None, 'group': "phases", 'type': int, 'val': 0, 'name': "Current AC Power Consumption in W of Phase 1"}
measurement_list['consumption_2'] = {'key': None, 'group': "phases", 'type': int, 'val': 0, 'name': "Current AC Power Consumption in W of Phase 2"}
measurement_list['consumption_3'] = {'key': None, 'group': "phases", 'type': int, 'val': 0, 'name': "Current AC Power Consumption in W of Phase 3"}

measurement_groups = {}
for measurement in measurement_list:
    if measurement_list[measurement]['group'] is not None:
        measurement_groups[measurement_list[measurement]['group']] = {}
        measurement_groups[measurement_list[measurement]['group']]['measurement'] = measurement_list[measurement]['group']

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
parser.add_argument('--interval', type=float, required=False, default="30.0", help='Interval in Seconds to query and save the data.')
parser.add_argument('--write', type=int, required=False, default=1, choices=[0, 1], help='Specify if Data should be written to InfluxDB or not.')
args=parser.parse_args()

ip = args.sma_ip
pw = args.sma_pw
mode = args.sma_mode

# definition of continous queries for faster statistics
continuous_queries = {
    'actuals_5min': 'CREATE CONTINUOUS QUERY actuals_5min ON ' + args.influx_db + ' BEGIN SELECT mean(solar_act) AS solar_5min, mean(consumption_act) AS consumption_5min, mean(bezug_act) AS bezug_5min, mean(einspeisung_act) AS einspeisung_5min INTO ' + args.influx_db + '.autogen.actuals_5min FROM ' + args.influx_db + '.autogen.actuals GROUP BY time(5m) END',
    'totals_daily': 'CREATE CONTINUOUS QUERY totals_daily ON ' + args.influx_db + ' RESAMPLE EVERY 1m BEGIN SELECT spread(solar_total) AS solar_daily, spread(bezug_total) AS bezug_daily, spread(consumption_total) AS consumption_daily, spread(einspeisung_total) AS einspeisung_daily INTO ' + args.influx_db + '.autogen.totals_daily FROM ' + args.influx_db + '.autogen.totals GROUP BY time(1d) TZ(\'Europe/Berlin\') END',
    'solar_max': 'CREATE CONTINUOUS QUERY solar_max ON ' + args.influx_db + ' RESAMPLE EVERY 5m BEGIN SELECT max(solar_5min) AS solar_max INTO ' + args.influx_db + '.autogen.totals_daily FROM ' + args.influx_db + '.autogen.actuals_5min GROUP BY time(1d) TZ(\'Europe/Berlin\') END',
    'consumption_min': 'CREATE CONTINUOUS QUERY consumption_min ON ' + args.influx_db + ' RESAMPLE EVERY 5m BEGIN SELECT min(consumption_5min) AS consumption_min INTO ' + args.influx_db + '.autogen.totals_daily FROM ' + args.influx_db + '.autogen.actuals_5min GROUP BY time(1d) TZ(\'Europe/Berlin\') END'
}

# Catch Stopping the Docker Container
def handler_stop_signals(signum, frame):
    global sid
    global ip
    if logout(ip, sid, mode):
        print(datetime.now(), "SMA Device Logout Successfull.")
    else:
        print(datetime.now(), "SMA Device Logout Failed.")
    print(datetime.now(), "Container Stopping...")
    sys.exit(0)
signal.signal(signal.SIGINT, handler_stop_signals)
signal.signal(signal.SIGTERM, handler_stop_signals)

# Login Function
def login(ip, pw, mode):
    url = mode + "//" + ip + "/dyn/login.json"
    payload = "{\"right\":\"usr\",\"pass\":\"" + pw + "\"}"
    try:
        response = requests.request("POST", url, data = payload, verify=False)
    #print(response.json())
    #print(response.status_code)
        if response.status_code == 200:
            if "result" in response.json():
                return response.json()['result']['sid']
        return None
    except:
        return None

# Logout Function
def logout(ip, sid, mode):
    url = mode + "://" + ip + "/dyn/logout.json?sid=" + sid
    response = requests.request("POST", url, data = "{}", verify=False)
    if response.status_code == 200:
        return True
    else:
        return False

# SMA Value Query
def query_values(ip, mode):
    global sid
    global pw
    url = mode + "://" + ip + "/dyn/getValues.json?sid=" + sid
    payload = {"destDev": [], "keys ": [] }
    measurements = []
    for measurement in measurement_list:
        if measurement_list[measurement]['key'] not in measurements and measurement_list[measurement]['key'] is not None:
            measurements.append(measurement_list[measurement]['key'])
    payload = json.dumps({"destDev": [], "keys": measurements})
    try:
        response = requests.request("POST", url, data = payload, verify=False)
        if "err" in response.json():
            if response.json()['err'] == 401:
                # Login on SMA Device
                sid = login(ip, pw, mode)
                while not sid:
                    print(datetime.now(), "Login on SMA Device (" + ip + ") failed.")
                    time.sleep(60)
                    sid = login(ip, pw, mode)
                print(datetime.now(), "Login on SMA Device successfull.")
        else:
            for id in response.json()['result']:
                sma_data = response.json()['result'][id]
    except:
        print(datetime.now(), "Query Failed...")

    values = {}
    for measurement in measurement_list:
        if measurement_list[measurement]['key'] is not None:
            key = measurement_list[measurement]['key']
            typ = measurement_list[measurement]['type']
            val = measurement_list[measurement]['val']
            if typ == int:
                try:
                    values[measurement] = int(sma_data[key]['1'][val]['val'])
                except:
                    values[measurement] = 0
            else:
                try:
                    values[measurement] = str(sma_data[key]['1'][val]['val'])
                except:
                    values[measurement] = str("-")
    try:
        values['consumption_act'] = values['solar_act']-values['einspeisung_act']+values['bezug_act']
    except:
        values['consumption_act'] = 0
    try:
        values['consumption_total'] = values['solar_total']-values['einspeisung_total']+values['bezug_total']
    except:
        values['consumption_total'] = 0
    try:
        if "consumption_1" in measurement_list:
            values['consumption_1'] = values['power_1']-values['supply_1']+values['acquisition_1']
    except:
        values['consumption_1'] = 0
    try:
        if "consumption_2" in measurement_list:
            values['consumption_2'] = values['power_2']-values['supply_2']+values['acquisition_2']
    except:
        values['consumption_2'] = 0
    try:
        if "consumption_3" in measurement_list:
            values['consumption_3'] = values['power_3']-values['supply_3']+values['acquisition_3']
    except:
        values['consumption_3'] = 0
    return values

# Session Check Function
def session_check(ip, mode):
    url = mode + "://" + ip + "/dyn/sessionCheck.json"
    try:
        response = requests.request("POST", url, data = "{}", verify=False)
    except:
        return (False, "No response from SMA Device (" + ip + ")!")
    #print(response.json())
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
session_status = session_check(ip)
while not session_status[0]:
    print(datetime.now(), session_status[1])
    time.sleep(10)
    session_status = session_check(ip)
print(datetime.now(), session_status[1])

now = datetime.now()
new_time = ceil_time(now, timedelta(seconds=int(args.interval)))

print(now, "Actual Time:", now, "waiting for:", new_time)    

# Wait for Full Minute / Half Minute
while now < new_time:
    time.sleep(0.5)
    now = datetime.now()

client = InfluxDBClient(host=args.influx_ip, port=args.influx_port, username=args.influx_user, password=args.influx_pw)

# Login on SMA Device
sid = login(ip, pw, mode)
while not sid:
    print(datetime.now(), "Login on SMA Device (" + ip + ") failed.")
    time.sleep(60)
    sid = login(ip, pw, mode)
print(datetime.now(), "Login on SMA Device successfull.")

# Execute Query every Xs
solar_values_last = {}
try:
    while True:
        solar_values = query_values(ip, mode)
        print(datetime.now(), "SMA Device Values: ", solar_values)
        # Connect to InfluxDB and save Solar Values
        try:
            client = InfluxDBClient(host=args.influx_ip, port=args.influx_port, username=args.influx_user, password=args.influx_pw)
            #print(client.get_list_database())
            if not {'name': args.influx_db} in client.get_list_database():
                client.create_database(args.influx_db)
                print(datetime.now(), "InfluxDB (" + args.influx_db + ") created.")
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
                                print(datetime.now(), "Incorrect Continuous Query dropped:", query['name'])
            for query in continuous_queries:
                influx_query = client.query(continuous_queries[query])
                print(datetime.now(), "Added Continuous Query:", query, "Result: ", influx_query)
                sel_start = continuous_queries[query].find("SELECT")
                sel_end = continuous_queries[query].find("END")
                sel_query = continuous_queries[query][sel_start:sel_end]
                influx_query = client.query(sel_query)
                print(datetime.now(), "Filled Statistical Tables for:", query, "Result: ", influx_query)

            # Write Solar data to InfluxDB 
            try:
                # Workaround for missing / wrong (lower) total values after SMA restart
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
                        },
                        "time": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                        "fields": {}
                    }
                    for measurement in measurement_list:
                        if measurement_list[measurement]['group'] == group:
                            if solar_values[measurement] is not None:
                                temp_body['fields'][measurement] = solar_values[measurement]
                    if str(solar_values['sma_sn']) != "unknown":
                        json_body.append(temp_body)
                    else:
                        print(datetime.now(), "Incorrect Serial Number, skipping data, SN: " + str(solar_values['sma_sn']))
                #print(datetime.now(), "InfluxDB write data DEBUG:" + str(json_body))
                if args.write == 1:
                    influx_result = client.write_points(json_body)
                    if influx_result:
                        print(datetime.now(), "InfluxDB write data successfull:" + str(json_body))
                    else:
                        print(datetime.now(), "InfluxDB write data FAILED:" + str(json_body))
                        print(influx_result)
                #solar_values_last = solar_values
            except Exception as e:
                print(datetime.now(), "InfluxDB error writing the Solar Values", e)
            finally:
                client.close()
        except Exception as e:
            print(datetime.now(), "InfluxDB connection failed (%s@%s)." % (args.influx_ip, args.influx_port))

        time.sleep(args.interval - ((time.time() - new_time.timestamp()) % args.interval))
except KeyboardInterrupt:
    print("Script aborted...")
finally:
    if logout(ip, sid, mode):
        print(datetime.now(), "SMA Device Logout Successfull.")
    else:
        print(datetime.now(), "SMA Device Logout Failed.")
