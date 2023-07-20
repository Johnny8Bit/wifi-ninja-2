import re
import sys
import json
import time
import subprocess

import requests


WLAN_INTERFACE = "wlan1"


DASHBOARD_API_KEY = "12345"
DASHBOARD_IP = "192.168.6.6"
DASHBOARD_PORT = "80"


class Sensor():

    def __init__(self, client_mac):
        self.mac = re.search("addr (([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2})", client_mac.decode("utf-8").lstrip()).group(1).upper()

    location = "default"
    type = "raspberry-pi"
    scan_interval = 15 #seconds



def send(parse_input):


    scanner_data = {}
    scanner_data["sensor"] = {}
    scanner_data["sensor"]["sensor_mac"] = pi.mac
    scanner_data["sensor"]["sensor_type"] = pi.type
    scanner_data["sensor"]["sensor_location"] = pi.location
    scanner_data["sensor"]["results"] = parse_input

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
                bssid = re.match("(BSS )?(([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2})", line).group(2).upper()
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
               freq = re.match("freq: (.+)", line).group(1)
               bss_data[bssid]["freq"] = freq
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
                bss_data[bssid]["data_rates"] = data_rates.rstrip().replace(".0", "")
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
                bss_data[bssid]["ch_util"] = str(round((int(ch_util.split("/")[0]) / int(ch_util.split("/")[1])) * 100)) #Convert from base 255 to %
            except AttributeError:
                pass
            try:
                ap_name = re.match("Unknown IE \(133\): ([0-9a-fA-F]{2} ){10}(([0-9a-fA-F]{2} ){15})", line).group(2).rstrip()
                bss_data[bssid]["ap_name"] = bytes.fromhex(ap_name.replace(" ", "")).decode("utf-8")
            except AttributeError:
                pass

    send({k: v for k, v in sorted(bss_data.items(), key=lambda x: x[1]["signal"])})


def run():


    while True:
        try:
            iw_output = subprocess.run(["sudo", "iw", "dev", WLAN_INTERFACE, "scan", "-u"], capture_output=True)
            parse(iw_output.stdout)
            time.sleep(pi.scan_interval)

        except KeyboardInterrupt:
            subprocess.run(["clear"])
            subprocess.run(["echo", "Wi-Fi Ninja 2 : Stopped"])
            sys.exit()


if __name__ == '__main__':


    subprocess.run(["echo", "Wi-Fi Ninja 2 : Running"])
    mac_addr = subprocess.run(["iw", "dev", WLAN_INTERFACE, "info"], capture_output=True)
    pi = Sensor(mac_addr.stdout)

    run()
