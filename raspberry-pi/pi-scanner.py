import re
import sys
import time
import subprocess


WLAN_INTERFACE = "wlan0"


def parse(input):


    scan_data = input.decode("utf-8")
    bss_list = re.split("\nBSS", scan_data)
    for bss in bss_list:
        for line in bss.splitlines():
            line = line.lstrip()
            try:
                bssid = re.match("(([0-9A-F]{2}:){5}[0-9A-F]{2})", line.upper()).group(1)
            except AttributeError:
                pass
            try:
                channel = re.match("DS Parameter set: channel (\d{1,3})", line).group(1)
            except AttributeError:
                pass
            try:
                signal = re.match("signal: (-\d{2})", line).group(1)
            except AttributeError:
                pass
            try:
                ssid = re.match("SSID: (.+)", line).group(1)
            except AttributeError:
                pass
            try:
                rates = re.match("Supported rates: (.+)", line).group(1)
                rate_list = rates.split()
            except AttributeError:
                pass
            try:
                country = re.match("Country: ([A-Z]{2})", line).group(1)
            except AttributeError:
                pass
            try:
                authentication = re.match("\* Authentication suites: (.+)", line).group(1)
            except AttributeError:
                pass
            try:
                pairwise_cipher = re.match("\* Pairwise ciphers: (.+)", line).group(1)
            except AttributeError:
                pass
            try:
                group_cipher = re.match("\* Group mgmt cipher suite: (.+)", line).group(1)
            except AttributeError:
                pass
            try:
                sta_count = re.match("\* station count: (\d{1,3})", line).group(1)
            except AttributeError:
                pass
            try:
                ch_util = re.match("\* channel utilisation: (\d{1,3}/\d{1,3})", line).group(1)
            except AttributeError:
                pass
        try:
            print(bssid, channel, signal, ssid, rate_list, country, authentication, pairwise_cipher, group_cipher, sta_count, ch_util)
        except UnboundLocalError:
            pass


def run():


    while True:
        try:
            iw_output = subprocess.run(["sudo", "iw", "dev", WLAN_INTERFACE, "scan" ], capture_output=True)
            parse(iw_output.stdout)

        except KeyboardInterrupt:
            subprocess.run(["clear"])
            subprocess.run(["echo", "Wi-Fi Ninja 2 : Stopped"])
            sys.exit()


if __name__ == '__main__':

    run()
