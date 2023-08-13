import logging
from datetime import datetime
from collections import Counter, OrderedDict

import commsLib
import fileLib

NETCONF_CYCLE_LONG = 60 #seconds
NETCONF_CYCLE_SHORT = 10 #seconds

SAVE_CSV = False

AP_CLIENTS_HIGH = 75
AP_CLIENTS_LOW = 50
AP_UTIL_HIGH = 60
AP_UTIL_LOW = 40
SEND_TOP = 10

WLC_MONITOR_INTERFACE = "Port-channel1"

log = logging.getLogger(__name__)


class Ninja2():

    def __init__(self):

        self.long_lastrun = datetime.now()
        self.short_lastrun = datetime.now()
        self.long_firstrun = True
        self.short_firstrun = True
        self.max_clients = 0
        self.wlc_data = {}
        self.ap_data = {}
        self.ap_data_ops = {}

init = Ninja2()


def netconf_collect():

    short_idle_period = datetime.now() - init.short_lastrun
    long_idle_period = datetime.now() - init.long_lastrun

    if init.short_firstrun or short_idle_period.seconds >= NETCONF_CYCLE_SHORT:

        init.short_firstrun = False
        init.short_lastrun = datetime.now()

        get_netconf_interfaces_oper()
        get_netconf_wireless_client_global_oper()
        get_netconf_wireless_client_oper()
        
        commsLib.send_to_dashboard("WLC", init.wlc_data)
        if SAVE_CSV: fileLib.wlc_to_csv(init.wlc_data)
        
    if init.long_firstrun or long_idle_period.seconds >= NETCONF_CYCLE_LONG:

        init.long_firstrun = False
        init.long_lastrun = datetime.now()

        get_netconf_wireless_access_point_oper()
        get_netconf_wireless_rrm_oper()

        commsLib.send_to_dashboard("AP", init.ap_data_ops)


def get_netconf_wireless_client_oper():

    filter = '''
        <client-oper-data xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-wireless-client-oper">
            <dot11-oper-data>
                <ewlc-ms-phy-type/>
            </dot11-oper-data>
            <dc-info>
                <device-type/>
                <device-os/>
            </dc-info>
        </client-oper-data>
    '''
    netconf_data = commsLib.netconf_get(filter)
    parse_netconf_clients(netconf_data)
    parse_netconf_devices(netconf_data)


def parse_netconf_clients(input_data):

    phy_data = {}
    total_clients = 0
    try:
        client_phy = input_data["data"]["client-oper-data"]["dot11-oper-data"]
    except KeyError:
        log.warning(f"No client PHY data")
        if "per-phy" in init.wlc_data: del init.wlc_data["per-phy"]
    else:
        if type(client_phy) in (dict, OrderedDict): #Change to list if only single client on WLC
            client_phy = [client_phy]
        for client in client_phy:
            total_clients += 1
            phy = rename_phy(client["ewlc-ms-phy-type"])
            if phy in phy_data.keys():
                phy_data[phy] += 1
            else:
                phy_data[phy] = 1

        if total_clients > init.max_clients:
            init.max_clients = total_clients
        
        phy_data = {"per-phy" : dict(sorted(phy_data.items(), reverse=True))}

    finally:
        phy_data = {**phy_data, "all-clients" : total_clients, "max-clients" : init.max_clients}
        init.wlc_data = {**init.wlc_data, **phy_data}


def parse_netconf_devices(input_data):

    os_type_data = {}
    try:
        client_types = input_data["data"]["client-oper-data"]["dc-info"]
    except KeyError:
        log.warning(f"No client device data")
        if "top-os" in init.wlc_data: del init.wlc_data["top-os"]
    else:
        if type(client_types) in (dict, OrderedDict): #Change to list if only a single client on WLC
            client_types = [client_types]

        os_data = []
        for client_type in client_types:
            try:
                os_data.append(client_type["device-os"])
            except KeyError:
                log.info(f"Client not classified")
        
        top_os = Counter(os_data)
        top_os_total = sum(top_os.values())
        
        for tup in top_os.most_common(SEND_TOP):
            os_type_data[tup[0]] = f"{int(int(tup[1])/top_os_total*100)} %"
        
        os_type_data = {"top-os" : os_type_data}

    finally:         
        init.wlc_data = {**init.wlc_data, **os_type_data}


def get_netconf_interfaces_oper():

    filter = f'''
        <interfaces xmlns='http://cisco.com/ns/yang/Cisco-IOS-XE-interfaces-oper'>
            <interface>
                <name>{WLC_MONITOR_INTERFACE}</name>
                <statistics>
                    <in-octets/>
                    <in-discards/>
                    <in-discards-64/>
                    <in-unknown-protos/>
                    <in-unknown-protos-64/>
                    <out-octets-64/>
                    <out-discards/>
                </statistics>
            </interface>
        </interfaces>
    '''             
    netconf_data = commsLib.netconf_get(filter)
    try:
        interface_data = netconf_data["data"]["interfaces"]["interface"]
    except KeyError:
        log.warning(f"No interface data")
    else:
        in_octets = change_units(interface_data["statistics"]["in-octets"])
        out_octets = change_units(interface_data["statistics"]["out-octets-64"])
        
        in_discards = int(interface_data["statistics"]["in-discards"])
        in_discards_64 = int(interface_data["statistics"]["in-discards-64"])
        in_unknown_protos = int(interface_data["statistics"]["in-unknown-protos"])
        in_unknown_protos_64 = int(interface_data["statistics"]["in-unknown-protos-64"])
        in_drops = in_discards + in_discards_64 + in_unknown_protos + in_unknown_protos_64
        
        out_discards = int(interface_data["statistics"]["out-discards"])
        out_drops = out_discards

        interface_data = {"lan-interface" : WLC_MONITOR_INTERFACE,
                          "in-bytes" : in_octets,
                          "out-bytes" : out_octets,
                          "in-drops" : in_drops,
                          "out-drops" : out_drops,
                          "out-discards" : out_drops,
                          "in-discards" : in_discards,
                          "in-discards-64" : in_discards_64,
                          "in-unknown-protos" : in_unknown_protos,
                          "in-unknown-protos-64" : in_unknown_protos_64
                          }

        init.wlc_data = {**init.wlc_data, **interface_data}


def get_netconf_wireless_client_global_oper():

    filter = '''
        <client-global-oper-data xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-wireless-client-global-oper">
            <client-live-stats/>
        </client-global-oper-data>
    '''
    netconf_data = commsLib.netconf_get(filter)
    try:
        client_state_data = netconf_data["data"]["client-global-oper-data"]["client-live-stats"]
    except KeyError:
        log.warning(f"No client state data")
    else:
        client_states = {"client-states" : {"auth" : client_state_data["auth-state-clients"],
                                            "mobility" : client_state_data["mobility-state-clients"],
                                            "iplearn" : client_state_data["iplearn-state-clients"],
                                            "webauth" : client_state_data["webauth-state-clients"],
                                            "run" : client_state_data["run-state-clients"],
                                            "delete" : client_state_data["delete-state-clients"],
                                            "random-mac" : client_state_data["random-mac-clients"]
                                            }
                        }
        init.wlc_data = {**init.wlc_data, **client_states}


def get_netconf_wireless_access_point_oper():

    filter = '''
        <access-point-oper-data xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-wireless-access-point-oper">
            <ap-name-mac-map/>
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
    netconf_data = commsLib.netconf_get(filter)
    parse_netconf_ap_name(netconf_data)
    parse_netconf_ap_ops(netconf_data)


def parse_netconf_ap_name(input_data):

    init.ap_data = {}
    try:
        ap_name_data = input_data["data"]["access-point-oper-data"]["ap-name-mac-map"]
    except KeyError:
        log.warning(f"No AP name data")
    else:
        if type(ap_name_data) == dict: #Change to list if only a single AP on WLC
            ap_name_data = [ap_name_data]

        for ap in ap_name_data:
            ap_name = ap["wtp-name"]
            ap_mac_lan = ap["eth-mac"]
            ap_mac_wifi = ap["wtp-mac"]
            init.ap_data[ap_mac_wifi] =  {"ap_name" : ap_name, "eth_mac" : ap_mac_lan}


def parse_netconf_ap_ops(input_data):

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


def get_netconf_wireless_rrm_oper():

    filter = '''
        <rrm-oper-data xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-wireless-rrm-oper">
            <rrm-measurement>
                <wtp-mac/>
                <radio-slot-id/>
                    <load>
                        <stations/>
                        <rx-noise-channel-utilization/>
                    </load>
            </rrm-measurement>
            <radio-slot>
                <wtp-mac/>
                <radio-slot-id/>
                <radio-data>
                    <dca-stats>
                        <chan-changes/>
                    </dca-stats>
                </radio-data>
            </radio-slot>
        </rrm-oper-data>
    '''
    netconf_data = commsLib.netconf_get(filter)
    try:
        ap_rrm_data = netconf_data["data"]["rrm-oper-data"]["rrm-measurement"]
        ap_radio_slot_data = netconf_data["data"]["rrm-oper-data"]["radio-slot"]
    except KeyError:
        log.warning(f"No AP RRM/Radio data")
    else:
        for radio in ap_rrm_data:
            init.ap_data[radio["wtp-mac"]][radio["radio-slot-id"]]["stations"] = radio["load"]["stations"]
            init.ap_data[radio["wtp-mac"]][radio["radio-slot-id"]]["ch_util"] = radio["load"]["rx-noise-channel-utilization"]
        for slot in ap_radio_slot_data:
            init.ap_data[slot["wtp-mac"]][slot["radio-slot-id"]]["ch_changes"] = slot["radio-data"]["dca-stats"]["chan-changes"]
    finally:
        sort_rrm_data()


def sort_rrm_data():

    top_sta_2, top_util_2, top_change_2 = [], [], []
    top_sta_5, top_util_5, top_change_5 = [], [], []
    top_sta_6, top_util_6, top_change_6 = [], [], []

    for ap in init.ap_data.keys():
        for slot in range(0, 5): #radio slots
            try:
                ap_name = init.ap_data[ap]["ap_name"]
                ap_slot = slot
                ap_ch = init.ap_data[ap][str(slot)]["channel"]
                ap_sta = int(init.ap_data[ap][str(slot)]["stations"])
                ap_util = int(init.ap_data[ap][str(slot)]["ch_util"])
                ap_change = int(init.ap_data[ap][str(slot)]["ch_changes"])
                ap_change_colour = "grey"

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
                    top_change_2.append((ap_name, ap_slot, ap_ch, ap_change_colour, ap_change))

                if init.ap_data[ap][str(slot)]["band"] == "dot11-5-ghz-band":    
                    top_sta_5.append((ap_name, ap_slot, ap_ch, ap_sta_colour, ap_sta))
                    top_util_5.append((ap_name, ap_slot, ap_ch, ap_util_colour, ap_util))
                    top_change_5.append((ap_name, ap_slot, ap_ch, ap_change_colour, ap_change))

                if init.ap_data[ap][str(slot)]["band"] == "dot11-6-ghz-band":
                    top_sta_6.append((ap_name, ap_slot, ap_ch, ap_sta_colour, ap_sta))
                    top_util_6.append((ap_name, ap_slot, ap_ch, ap_util_colour, ap_util))
                    top_change_6.append((ap_name, ap_slot, ap_ch, ap_change_colour, ap_change))

            except KeyError:
                log.info(f"No data for {ap} slot {slot}")
    
    init.ap_data_ops["ch_util_2"] = sorted(top_util_2, key=lambda tup: tup[4], reverse=True)[0:SEND_TOP]
    init.ap_data_ops["ch_util_5"] = sorted(top_util_5, key=lambda tup: tup[4], reverse=True)[0:SEND_TOP]
    init.ap_data_ops["ch_util_6"] = sorted(top_util_6, key=lambda tup: tup[4], reverse=True)[0:SEND_TOP]
    init.ap_data_ops["stations_2"] = sorted(top_sta_2, key=lambda tup: tup[4], reverse=True)[0:SEND_TOP]
    init.ap_data_ops["stations_5"] = sorted(top_sta_5, key=lambda tup: tup[4], reverse=True)[0:SEND_TOP]
    init.ap_data_ops["stations_6"] = sorted(top_sta_6, key=lambda tup: tup[4], reverse=True)[0:SEND_TOP]
    init.ap_data_ops["ch_changes_2"] = sorted(top_change_2, key=lambda tup: tup[4], reverse=True)[0:SEND_TOP]
    init.ap_data_ops["ch_changes_5"] = sorted(top_change_5, key=lambda tup: tup[4], reverse=True)[0:SEND_TOP]
    init.ap_data_ops["ch_changes_6"] = sorted(top_change_6, key=lambda tup: tup[4], reverse=True)[0:SEND_TOP]


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



