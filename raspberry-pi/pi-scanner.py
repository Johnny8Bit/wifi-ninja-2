import re
import sys
import json
import time
import subprocess

import requests


WLAN_INTERFACE = "wlan0"
SCAN_INTERVAL = 15 #seconds
SENSOR_TYPE = "raspberry-pi"
SENSOR_LOCATION = "default"
DASHBOARD_API_KEY = "12345"
DASHBOARD_IP = "192.168.6.6"
DASHBOARD_PORT = "80"


def send(parse_input):


    scanner_data = {}
    scanner_data["sensor"] = {}
    scanner_data["sensor"]["sensor_type"] = SENSOR_TYPE
    scanner_data["sensor"]["sensor-location"] = SENSOR_LOCATION 
    scanner_data["results"] = parse_input

    dashboard_api = f"http://{DASHBOARD_IP}:{DASHBOARD_PORT}/PostSensorData"
    headers = {"api_key" : DASHBOARD_API_KEY}
    try:
        requests.post(dashboard_api, headers=headers, data=json.dumps(scanner_data), verify=False, timeout=2)
    except requests.exceptions.ConnectTimeout:
        pass
    except requests.exceptions.ConnectionError:
        pass


def parse(scan_input):


    scan_data = scan_input.decode("utf-8")
    bss_list = re.split("\nBSS", scan_data)
    bss_data = {}
    for bss in bss_list:
        for line in bss.splitlines():
            line = line.lstrip()
            try:
                bssid = re.match("(BSS )?(([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2})", line).group(2)
                if bssid not in bss_data.keys():
                    bss_data[bssid] = {}
            except AttributeError:
                pass
            try:
                channel = re.match("DS Parameter set: channel (\d{1,3})", line).group(1)
                bss_data[bssid]["channel"] = channel
            except AttributeError:
                pass
            try:
                signal = re.match("signal: (-\d{2})", line).group(1)
                bss_data[bssid]["signal"] = signal
            except AttributeError:
                pass
            try:
                ssid = re.match("SSID: (.+)", line).group(1)
                bss_data[bssid]["ssid"] = ssid
            except AttributeError:
                pass
            try:
                data_rates = re.match("Supported rates: (.+)", line).group(1)
                bss_data[bssid]["data_rates"] = data_rates.rstrip()
            except AttributeError:
                pass
            try:
                country = re.match("Country: ([A-Z]{2})", line).group(1)
                bss_data[bssid]["country"] = country
            except AttributeError:
                pass
            try:
                authentication = re.match("\* Authentication suites: (.+)", line).group(1)
                bss_data[bssid]["authentication"] = authentication
            except AttributeError:
                pass
            try:
                pairwise_cipher = re.match("\* Pairwise ciphers: (.+)", line).group(1)
                bss_data[bssid]["pairwise_cipher"] = pairwise_cipher
            except AttributeError:
                pass
            try:
                group_cipher = re.match("\* Group mgmt cipher suite: (.+)", line).group(1)
                bss_data[bssid]["group_cipher"] = group_cipher
            except AttributeError:
                pass
            try:
                sta_count = re.match("\* station count: (\d{1,3})", line).group(1)
                bss_data[bssid]["sta_count"] = sta_count
            except AttributeError:
                pass
            try:
                ch_util = re.match("\* channel utilisation: (\d{1,3}/\d{1,3})", line).group(1)
                bss_data[bssid]["ch_util"] = ch_util
            except AttributeError:
                pass

    send(bss_data)


def run():

    subprocess.run(["echo", "Wi-Fi Ninja 2 : Running"])
    while True:
        try:
            iw_output = subprocess.run(["sudo", "iw", "dev", WLAN_INTERFACE, "scan" ], capture_output=True)
            parse(iw_output.stdout)
            time.sleep(SCAN_INTERVAL)

        except KeyboardInterrupt:
            subprocess.run(["clear"])
            subprocess.run(["echo", "Wi-Fi Ninja 2 : Stopped"])
            sys.exit()


if __name__ == '__main__':

    run()
