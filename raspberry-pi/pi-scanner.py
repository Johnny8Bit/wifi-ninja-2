import re
import subprocess

WLAN_INTERFACE = "wlan0"

scan_output = subprocess.run(["sudo", "iw", "dev", WLAN_INTERFACE, "scan" ], capture_output=True)

list = scan_output.stdout.decode('UTF-8').split("BSS")
print(list)