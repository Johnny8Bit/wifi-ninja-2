import logging
from datetime import datetime
import csv

MAX_SLOTS = 5 #radio slots

WLC_HEADINGS = ["date", "time", "clients-now", "clients-max", "lan-interface",
                "in-bytes", "out-bytes", "in-discards", "in-discards-64",
                "in-unknown-protos", "in-unknown-protos-64", "out-discards", "per-phy", "top-os"
                ]

AP_HEADINGS = ["date", "time", "ap-name", "radio-mac", "eth-mac",
               "slot", "state", "mode", "band", "channel", "width", "stations", "ch_util", "ch_changes",
               "slot", "state", "mode", "band", "channel", "width", "stations", "ch_util", "ch_changes",
               "slot", "state", "mode", "band", "channel", "width", "stations", "ch_util", "ch_changes",
               "slot", "state", "mode", "band", "channel", "width", "stations", "ch_util", "ch_changes",
               "slot", "state", "mode", "band", "channel", "width", "stations", "ch_util", "ch_changes"
                ]

log = logging.getLogger(__name__)


class InitCsv():

    def __init__(self):

        self.path = "../logs/"
        self.stamp = str(datetime.now())[:-7].replace(':', "-").replace(" ", "_")
        self.wlc_filename = f"{self.path}{self.stamp}_WLC.csv"
        self.ap_filename = f"{self.path}{self.stamp}_AP.csv"

        write_csv(self.wlc_filename, WLC_HEADINGS)
        write_csv(self.ap_filename, AP_HEADINGS)


def date_time():

    dt = []
    stamp = str(datetime.now())[:-7]
    dt.append(stamp.split()[0])
    dt.append(stamp.split()[1])

    return dt


def write_csv(filename, row):

    try:
        with open(filename, "a") as csvfile:
            csvwriter = csv.writer(csvfile, lineterminator="\n", delimiter=",")
            csvwriter.writerow(row)
    except PermissionError:
        log.error(f"Unable to append CSV")


def wlc_to_csv(wlc_dict):

    row_data = date_time()
    try:
        row_data.append(wlc_dict["all-clients"])
        row_data.append(wlc_dict["max-clients"])
        row_data.append(wlc_dict["lan-interface"])
        row_data.append(wlc_dict["in-bytes"])
        row_data.append(wlc_dict["out-bytes"])
        row_data.append(wlc_dict["in-discards"])
        row_data.append(wlc_dict["in-discards-64"])
        row_data.append(wlc_dict["in-unknown-protos"])
        row_data.append(wlc_dict["in-unknown-protos-64"])
        row_data.append(wlc_dict["out-discards"])
        try:
            row_data.append(wlc_dict["per-phy"])
        except KeyError: #append blank cell when no client data exists e.g. 0 clients
            row_data.append("")
        try:
            row_data.append(wlc_dict["top-os"])
        except KeyError: #append blank cell when no client data exists e.g. 0 clients
            row_data.append("")

    except KeyError:
        log.warning(f"WLC data incomplete. Not writing to CSV")
    else:
        write_csv(init.wlc_filename, row_data)


def ap_to_csv(ap_dict):

    dt = date_time()
    for ap_mac, ap_data in ap_dict.items():
        row_data = []
        row_data.append(dt[0])
        row_data.append(dt[1])
        try:
            row_data.append(ap_data["ap_name"])
            row_data.append(ap_mac)
            row_data.append(ap_data["eth_mac"])
            for slot in range(0, MAX_SLOTS): #radio slots
                slot = str(slot)
                row_data.append(f"SLOT {slot}")
                try:
                    row_data.append(ap_data[slot]["state"])
                    row_data.append(ap_data[slot]["mode"])
                    row_data.append(ap_data[slot]["band"])
                    row_data.append(ap_data[slot]["channel"])
                    row_data.append(ap_data[slot]["width"])
                    row_data.append(ap_data[slot]["stations"])
                    row_data.append(ap_data[slot]["ch_util"])
                    row_data.append(ap_data[slot]["ch_changes"])
                except KeyError:
                    row_data = row_data + [" ", " ", " ", " ", " ", " ", " ", " "]
                    log.info(f"No data for {ap_data['ap_name']} slot {slot}") 
    
        except KeyError:
            log.warning(f"AP data incomplete. Not writing to CSV")
        else:
            write_csv(init.ap_filename, row_data)


init = InitCsv()