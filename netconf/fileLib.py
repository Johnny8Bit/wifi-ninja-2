import logging
from datetime import datetime
import csv

WLC_HEADINGS = ["date",
                "time",
                "clients-now",
                "clients-max",
                "lan-interface",
                "in-bytes",
                "out-bytes",
                "in-discards",
                "in-discards-64",
                "in-unknown-protos",
                "in-unknown-protos-64",
                "out-discards",
                "per-phy",
                "top-os",
                ]


log = logging.getLogger(__name__)


class InitCsv():

    def __init__(self):

        self.path = "../logs/"
        self.stamp = str(datetime.now())[:-7].replace(':', "-").replace(" ", "_")
        self.wlc_filename = f"{self.path}{self.stamp}_WLC.csv"
        self.ap_2_filename = f"{self.path}{self.stamp}_AP2.csv"
        self.ap_5_filename = f"{self.path}{self.stamp}_AP5.csv"
        self.ap_6_filename = f"{self.path}{self.stamp}_AP6.csv"

        write_csv(self.wlc_filename, WLC_HEADINGS)


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
        row_data.append(wlc_dict["per-phy"])
        row_data.append(wlc_dict["top-os"])
    except KeyError:
        log.warning(f"No WLC data to write to CSV")
    else:
        write_csv(init.wlc_filename, row_data)


def ap_to_csv(ap_dict):

    row_data = date_time()
    try:
        row_data.append(ap_dict["all_clients"])
        row_data.append(ap_dict["max_clients"])
        row_data.append(ap_dict["lan_interface"])
        row_data.append(ap_dict["in_bytes"])
        row_data.append(ap_dict["out_bytes"])
        row_data.append(ap_dict["per_phy"])
        row_data.append(ap_dict["top_os"])
    except KeyError:
        log.warning(f"No AP data to write to CSV")
    else:
        write_csv(init.ap_filename, row_data)


init = InitCsv()