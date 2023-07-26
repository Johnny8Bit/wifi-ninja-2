import logging
from datetime import datetime

import commsLib

NETCONF_CYCLE_AP_DATA = 60 #seconds
NETCONF_CYCLE_WLC_DATA = 10 #seconds

AP_CLIENTS_HIGH = 75
AP_CLIENTS_LOW = 50
AP_UTIL_HIGH = 60
AP_UTIL_LOW = 40
SEND_TOP = 10

WLC_MONITOR_INTERFACE = "Port-channel1"

log = logging.getLogger(__name__)


class Ninja2():

    def __init__(self):

        self.ap_lastrun = datetime.now()
        self.wlc_lastrun = datetime.now()
        self.ap_firstrun = True
        self.wlc_firstrun = True
        self.max_clients = 0
        self.wlc_data = {}
        self.ap_data = {}
        self.ap_data_ops = {}

init = Ninja2()


def netconf_wlc_data():

    idle_period = datetime.now() - init.wlc_lastrun
    if init.wlc_firstrun or idle_period.seconds >= NETCONF_CYCLE_WLC_DATA:

        get_netconf_wlc_client()
        get_netconf_wlc_interfaces()
        commsLib.send_to_dashboard("WLC", init.wlc_data)
        
        init.wlc_firstrun = False
        init.wlc_lastrun = datetime.now()


def netconf_ap_data():

    idle_period = datetime.now() - init.ap_lastrun
    if init.ap_firstrun or idle_period.seconds >= NETCONF_CYCLE_AP_DATA:

        get_netconf_ap_name()
        get_netconf_ap_ops()
        get_netconf_ap_rrm()
        sort_rrm_data()
        commsLib.send_to_dashboard("AP", init.ap_data_ops)

        init.ap_firstrun = False
        init.ap_lastrun = datetime.now()


def get_netconf_wlc_client():

    filter_client = '''
        <client-oper-data xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-wireless-client-oper">
            <dot11-oper-data/>
        </client-oper-data>
    '''
    phy_data = {}
    total_clients = 0
    input_data = commsLib.netconf_get(filter_client)
    try:
        client_data = input_data["data"]["client-oper-data"]["dot11-oper-data"]
    except KeyError:
        log.warning(f"No client_data")
    else:
        if type(client_data) == dict: #Single client on WLC
            phy = rename_phy(client_data["ewlc-ms-phy-type"])
            total_clients, phy_data[phy] = 1, 1

        elif type(client_data) == list: #Multiple clients on WLC
            for item in client_data:
                phy = rename_phy(item["ewlc-ms-phy-type"])
                total_clients += 1
                if phy in phy_data.keys():
                    phy_data[phy] += 1
                else:
                    phy_data[phy] = 1

        if total_clients > init.max_clients:
            init.max_clients = total_clients

        phy_data = {"all_clients" : total_clients,
                    "max_clients" : init.max_clients,
                    "per_phy" : dict(sorted(phy_data.items(), reverse=True))}

        init.wlc_data = {**init.wlc_data, **phy_data}


def get_netconf_wlc_interfaces():

    filter_interface = '''
        <interfaces xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-interfaces-oper">
            <interface>
                <name/>
                <statistics/>
            </interface>
      </interfaces>
    '''
    input_data = commsLib.netconf_get(filter_interface)
    try:
        interface_data = input_data["data"]["interfaces"]["interface"]
    except KeyError:
        in_octets, out_octets = 0, 0
        log.warning(f"No interface data")
    else:
        for item in interface_data:
            if item["name"] == WLC_MONITOR_INTERFACE:
                in_octets = item["statistics"]["in-octets"]
                out_octets = item["statistics"]["out-octets-64"]

        interface_data = {"lan_interface" : WLC_MONITOR_INTERFACE,
                          "in_bytes" : change_units(in_octets), 
                          "out_bytes" : change_units(out_octets)}

        init.wlc_data = {**init.wlc_data, **interface_data}


def get_netconf_ap_name():

    filter_ap_name = '''
        <access-point-oper-data xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-wireless-access-point-oper">
            <ap-name-mac-map/>
        </access-point-oper-data>
    '''
    input_data = commsLib.netconf_get(filter_ap_name)
    try:
        ap_name_data = input_data["data"]["access-point-oper-data"]["ap-name-mac-map"]
    except KeyError:
        log.warning(f"No AP name data")
    else:
        if type(ap_name_data) == dict: #Single AP on WLC
            ap_name = ap_name_data["wtp-name"]
            ap_mac_lan = ap_name_data["eth-mac"]
            ap_mac_wifi = ap_name_data["wtp-mac"]
            init.ap_data[ap_mac_wifi] =  {"ap_name" : ap_name, "eth_mac" : ap_mac_lan}
            
        elif type(ap_name_data) == list: #Multiple APs on WLC
            for ap in ap_name_data:
                ap_name = ap["wtp-name"]
                ap_mac_lan = ap["eth-mac"]
                ap_mac_wifi = ap["wtp-mac"]
                init.ap_data[ap_mac_wifi] =  {"ap_name" : ap_name, "eth_mac" : ap_mac_lan}


def get_netconf_ap_ops():
    
    filter_ap_ops = '''
        <access-point-oper-data xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-wireless-access-point-oper">
            <radio-oper-data>
                <wtp-mac/>
                <radio-slot-id/>
                <slot-id/>
                <oper-state/>
                <radio-mode/>
                <current-active-band/>
                <phy-ht-cfg>
                    <cfg-data>
                        <curr-freq/>
                        <chan-width/>
                    </cfg-data>
                </phy-ht-cfg>
            </radio-oper-data>
        </access-point-oper-data>
    '''
    input_data = commsLib.netconf_get(filter_ap_ops)
    try:
        ap_ops_data = input_data["data"]["access-point-oper-data"]["radio-oper-data"]
    except KeyError:
        log.warning(f"No AP operational data")
    else:
        for radio in ap_ops_data:
            init.ap_data[radio["wtp-mac"]][radio["radio-slot-id"]] = {}
            init.ap_data[radio["wtp-mac"]][radio["radio-slot-id"]]["state"] = radio["oper-state"]
            init.ap_data[radio["wtp-mac"]][radio["radio-slot-id"]]["mode"] = radio ["radio-mode"]
            init.ap_data[radio["wtp-mac"]][radio["radio-slot-id"]]["band"] = radio["current-active-band"]
            init.ap_data[radio["wtp-mac"]][radio["radio-slot-id"]]["channel"] = radio["phy-ht-cfg"]["cfg-data"]["curr-freq"]
            init.ap_data[radio["wtp-mac"]][radio["radio-slot-id"]]["width"] = radio["phy-ht-cfg"]["cfg-data"]["chan-width"]          


def get_netconf_ap_rrm():

    filter_ap_rrm = '''
        <rrm-oper-data xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-wireless-rrm-oper">
            <rrm-measurement>
                <wtp-mac/>
                <radio-slot-id/>
                    <load>
                        <stations/>
                        <rx-noise-channel-utilization/>
                    </load>
            </rrm-measurement>
        </rrm-oper-data>
    '''
    input_data = commsLib.netconf_get(filter_ap_rrm)
    try:
        ap_rrm_data = input_data["data"]["rrm-oper-data"]["rrm-measurement"]
    except KeyError:
        log.warning(f"No AP RRM data")
    else:
        for radio in ap_rrm_data:
            init.ap_data[radio["wtp-mac"]][radio["radio-slot-id"]]["stations"] = radio["load"]["stations"]
            init.ap_data[radio["wtp-mac"]][radio["radio-slot-id"]]["ch_util"] = radio["load"]["rx-noise-channel-utilization"]


def sort_rrm_data():

    top_sta_2, top_util_2 = [], []
    top_sta_5, top_util_5 = [], []
    top_sta_6, top_util_6 = [], []

    for ap in init.ap_data.keys():
        for slot in range(0, 5): #radio slots
            try:
                ap_name = init.ap_data[ap]["ap_name"]
                ap_slot = slot
                ap_ch = init.ap_data[ap][str(slot)]["channel"]
                ap_sta = int(init.ap_data[ap][str(slot)]["stations"])
                ap_util = int(init.ap_data[ap][str(slot)]["ch_util"])

                ap_sta_colour = "orange"
                if ap_sta < AP_CLIENTS_LOW:
                    ap_sta_colour = "green"
                if ap_sta >= AP_CLIENTS_HIGH:
                    ap_sta_colour = "red"

                ap_util_colour = "orange"
                if ap_util < AP_UTIL_LOW:
                    ap_util_colour = "green"
                if ap_util >= AP_UTIL_HIGH:
                    ap_util_colour = "red"
                
                if init.ap_data[ap][str(slot)]["band"] == "dot11-2-dot-4-ghz-band":    
                    top_sta_2.append((ap_name, ap_slot, ap_ch, ap_sta_colour, ap_sta))
                    top_util_2.append((ap_name, ap_slot, ap_ch, ap_util_colour, ap_util))

                if init.ap_data[ap][str(slot)]["band"] == "dot11-5-ghz-band":    
                    top_sta_5.append((ap_name, ap_slot, ap_ch, ap_sta_colour, ap_sta))
                    top_util_5.append((ap_name, ap_slot, ap_ch, ap_util_colour, ap_util))

                if init.ap_data[ap][str(slot)]["band"] == "dot11-6-ghz-band":
                    top_sta_6.append((ap_name, ap_slot, ap_ch, ap_sta_colour, ap_sta))
                    top_util_6.append((ap_name, ap_slot, ap_ch, ap_util_colour, ap_util))

            except KeyError:
                log.info(f"No data for {ap} slot {slot}")
    
    init.ap_data_ops["ch_util_2"] = sorted(top_util_2, key=lambda tup: tup[4], reverse=True)[0:SEND_TOP]
    init.ap_data_ops["ch_util_5"] = sorted(top_util_5, key=lambda tup: tup[4], reverse=True)[0:SEND_TOP]
    init.ap_data_ops["ch_util_6"] = sorted(top_util_6, key=lambda tup: tup[4], reverse=True)[0:SEND_TOP]
    init.ap_data_ops["stations_2"] = sorted(top_sta_2, key=lambda tup: tup[4], reverse=True)[0:SEND_TOP]
    init.ap_data_ops["stations_5"] = sorted(top_sta_5, key=lambda tup: tup[4], reverse=True)[0:SEND_TOP]
    init.ap_data_ops["stations_6"] = sorted(top_sta_6, key=lambda tup: tup[4], reverse=True)[0:SEND_TOP]


def rename_phy(phy):

    phy = phy.lstrip("client-").rstrip("-prot")
    if phy == "dot11ax-6ghz": phy = "Wi-Fi 6 (6GHz)"
    if phy == "dot11ax-5ghz": phy = "Wi-Fi 6 (5GHz)"
    if phy == "dot11ax-24ghz": phy = "Wi-Fi 6 (2.4GHz)"
    if phy == "dot11ac": phy = "Wi-Fi 5"
    if phy == "dot11n-5-ghz": phy = "Wi-Fi 4 (5GHz)"
    if phy == "dot11n-24-ghz": phy = "Wi-Fi 4 (2.4GHz)"
    if phy == "dot11g": phy = "Wi-Fi 3"
    if phy == "dot11a": phy = "Wi-Fi 2"
    if phy == "dot11b": phy = "Wi-Fi 1"

    return phy


def change_units(bytes):

    if len(bytes) > 3:
        throughput = str(round(int(bytes) / 1000, 1)) + " KB"
    if len(bytes) > 6:
        throughput = str(round(int(bytes) / 1000000, 1)) + " MB"
    if len(bytes) > 9:
        throughput = str(round(int(bytes) / 1000000000, 1)) + " GB"
    if len(bytes) > 12:
        throughput = str(round(int(bytes) / 1000000000000, 1)) + " TB"
    if len(bytes) > 15:
        throughput = str(round(int(bytes) / 1000000000000000, 1)) + " PB"
    
    return throughput



