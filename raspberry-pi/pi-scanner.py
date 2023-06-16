import re
import subprocess

wlan_interface = "wlan0"

scan_output = subprocess.call(["sudo", "iw", "dev", wlan_interface, "scan" ])

list = scan_output.split("BSS")
print(list)