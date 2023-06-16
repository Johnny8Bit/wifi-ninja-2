import subprocess

wlan_interface = "wlan0"

subprocess.call(["sudo", "iw", "dev", wlan_interface, "scan" ])