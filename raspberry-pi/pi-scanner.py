import re
import subprocess

wlan_interface = "wlan0"

scan_output = subprocess.run(["sudo", "iw", "dev", wlan_interface, "scan" ], capture_output=True)

list = scan_output.stdout
print(list)