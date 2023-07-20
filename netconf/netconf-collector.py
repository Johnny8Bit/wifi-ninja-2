import sys
import json
import time

from ncclient import manager, transport
import xmltodict
import requests


DASHBOARD_IP = "127.0.0.1"
DASHBOARD_PORT = "80"
DASHBOARD_API_KEY = "12345"

WLC_HOST = "192.168.6.8"
WLC_USER = "netconf"
WLC_PASS = "netconf"

WLC_MONITOR_INTERFACE = "Port-channel1"

REPEAT_AFTER = 15 #seconds


class Ninja2():

    def __init__(self):

        self.max_clients = 0
        self.send_top = 10
        self.ap_clients_red = 75
        self.ap_clients_green = 50
        self.ap_util_red = 60
        self.ap_util_green = 40
        self.wlc_data = {}
        self.ap_data = {}
        self.ap_data_ops = {}
    

def send_to_dashboard(api, data):

    dashboard_api = f"http://{DASHBOARD_IP}:{DASHBOARD_PORT}/Post{api}Data"
    headers = {"api_key" : DASHBOARD_API_KEY}
    try:
        requests.post(dashboard_api, 
                      headers=headers, 
                      data=json.dumps(data), 
                      verify=False, 
                      timeout=2)
    except requests.exceptions.ConnectTimeout:
        print("Dashboard timeout")
    except requests.exceptions.ConnectionError:
        print("Dashboard error")


def netconf_get(filter):

    try:
        with manager.connect(host=WLC_HOST,
                         port=830, 
                         username=WLC_USER, 
                         password=WLC_PASS, 
                         device_params={'name':'iosxe'}, 
                         hostkey_verify=False) as ncc:
            netconf_output = xmltodict.parse(ncc.get(filter=('subtree', filter)).data_xml)

    except transport.errors.SSHError:
        netconf_output = {}
        print("NETCONF error")
    return netconf_output


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


def get_netconf_wlc_client():

    filter_client = '''
        <client-oper-data xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-wireless-client-oper">
            <dot11-oper-data/>
        </client-oper-data>
    '''
    phy_data = {}
    total_clients = 0
    input_data = netconf_get(filter_client)
    try:
        client_data = input_data["data"]["client-oper-data"]["dot11-oper-data"]
    except KeyError:
        print("No client_data")
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


def get_netconf_wlc_interfaces():

    filter_interface = '''
        <interfaces xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-interfaces-oper">
            <interface>
                <name/>
                <statistics/>
            </interface>
      </interfaces>
    '''
    input_data = netconf_get(filter_interface)
    try:
        interface_data = input_data["data"]["interfaces"]["interface"]
    except KeyError:
        in_octets, out_octets = 0, 0
        print("No interface data")
    else:
        for item in interface_data:
            if item["name"] == WLC_MONITOR_INTERFACE:
                in_octets = item["statistics"]["in-octets"]
                out_octets = item["statistics"]["out-octets"]

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
    input_data = netconf_get(filter_ap_name)
    try:
        ap_name_data = input_data["data"]["access-point-oper-data"]["ap-name-mac-map"]
    except KeyError:
        print("No AP name data")
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
    input_data = netconf_get(filter_ap_ops)
    try:
        ap_ops_data = input_data["data"]["access-point-oper-data"]["radio-oper-data"]
    except KeyError:
        print("No AP operational data")
    else:
        temp = {}
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
    input_data = netconf_get(filter_ap_rrm)
    try:
        ap_rrm_data = input_data["data"]["rrm-oper-data"]["rrm-measurement"]
    except KeyError:
        print("No AP RRM data")
    else:
        for radio in ap_rrm_data:
            init.ap_data[radio["wtp-mac"]][radio["radio-slot-id"]]["stations"] = radio["load"]["stations"]
            init.ap_data[radio["wtp-mac"]][radio["radio-slot-id"]]["ch_util"] = radio["load"]["rx-noise-channel-utilization"]


def sort_rrm_data():

    top_client_5, top_util_5 = [], []
    top_client_6, top_util_6 = [], []

    for ap in init.ap_data.keys():
        for slot in range(0, 5): #radio slots
            try:
                ap_name = init.ap_data[ap]["ap_name"]
                ap_slot = slot
                ap_stas = init.ap_data[ap][str(slot)]["stations"]
                ap_load = init.ap_data[ap][str(slot)]["ch_util"]

                ap_stas_colour = "orange"
                if int(ap_stas) < init.ap_clients_green:
                    ap_stas_colour = "green"
                if int(ap_load) >= init.ap_clients_red:
                    ap_stas_colour = "red"

                ap_load_colour = "orange"
                if int(ap_load) < init.ap_util_green:
                    ap_load_colour = "green"
                if int(ap_load) >= init.ap_util_red:
                    ap_load_colour = "red"
                
                if init.ap_data[ap][str(slot)]["band"] == "dot11-5-ghz-band":    
                    top_client_5.append((ap_name, ap_slot, ap_stas_colour, ap_stas))
                    top_util_5.append((ap_name, ap_slot, ap_load_colour, ap_load))

                if init.ap_data[ap][str(slot)]["band"] == "dot11-6-ghz-band":
                    top_client_6.append((ap_name, ap_slot, ap_stas_colour, ap_stas))
                    top_util_6.append((ap_name, ap_slot, ap_load_colour, ap_load))

            except KeyError:
                print("No data for slot", slot)
        
    init.ap_data_ops["stations_5"] = sorted(top_client_5, key=lambda tup: tup[3], reverse=True)[0:init.send_top]
    init.ap_data_ops["ch_util_5"] = sorted(top_util_5, key=lambda tup: tup[3], reverse=True)[0:init.send_top]
    init.ap_data_ops["stations_6"] = sorted(top_client_6, key=lambda tup: tup[3], reverse=True)[0:init.send_top]
    init.ap_data_ops["ch_util_6"] = sorted(top_util_6, key=lambda tup: tup[3], reverse=True)[0:init.send_top]
    #({k: v for k, v in sorted(bss_data.items(), key=lambda x: x[1]["signal"])})


def run():

        try:
            while True:
                get_netconf_ap_name()
                get_netconf_ap_ops()
                get_netconf_ap_rrm()
                sort_rrm_data()
                send_to_dashboard("AP", init.ap_data_ops)
                get_netconf_wlc_client()
                get_netconf_wlc_interfaces()
                send_to_dashboard("WLC", init.wlc_data)
                time.sleep(REPEAT_AFTER)

        except KeyboardInterrupt:
            #subprocess.run(["clear"])
            #subprocess.run(["echo", "Wi-Fi Ninja 2 : Stopped"])
            sys.exit()


if __name__ == '__main__':

    init = Ninja2()
    run()