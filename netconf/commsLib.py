import os
import re
import json
import logging

from ncclient import manager, transport, operations

import xmltodict
import requests

import envLib

env = envLib.read_config_file()
log = logging.getLogger(__name__)

DASHBOARD_API_KEY = os.environ["DASHBOARD_API_KEY"]
INFLUX_API_KEY = os.environ["INFLUX_API_KEY"]
WLC_USER = os.environ["WLC_USER"]
WLC_PASS = os.environ["WLC_PASS"]


def send_to_influx(data, precision="s"):

    influx_api = f'http://{env["INFLUX_IP"]}:{env["INFLUX_PORT"]}/api/v2/write'
    headers = {
        "Content-Type" : "text/plain; charset=utf-8",
        "Accept" : "application/json",
        "Authorization": f'Token {INFLUX_API_KEY}'
    }
    params = {
        "org" : env["INFLUX_ORG"],
        "bucket" : env["INFLUX_BUCKET"],
        "precision" : precision
    }
    try:
        requests.post(influx_api, headers=headers, params=params, data=data)
    except requests.exceptions.ConnectTimeout:
        log.error(f"Influx timeout")
    except requests.exceptions.ConnectionError:
        log.error(f"Influx error") 


def send_to_dashboard(api, data):

    dashboard_api = f'http://{env["DASHBOARD_IP"]}:{env["DASHBOARD_PORT"]}/Post{api}Data'
    headers = {"Api-Key" : DASHBOARD_API_KEY}
    try:
        requests.post(dashboard_api, 
                      headers=headers, 
                      data=json.dumps(data), 
                      verify=False, 
                      timeout=2)
    except requests.exceptions.ConnectTimeout:
        log.error(f"Dashboard timeout")
    except requests.exceptions.ConnectionError:
        log.error(f"Dashboard error")


def netconf_get(filter): #Using xmltodict

    try:
        with manager.connect(host=env["WLC_HOST"],
                             port=830,
                             username=WLC_USER,
                             password=WLC_PASS,
                             device_params={"name":"iosxe"},
                             hostkey_verify=False) as ncc:
            netconf_output = xmltodict.parse(ncc.get(filter=("subtree", filter)).data_xml)

    except (transport.errors.SSHError, operations.errors.TimeoutExpiredError):
        netconf_output = {}
        log.error(f"NETCONF error")
    return netconf_output


def netconf_get_x(filter): #Using XPath

    try:
        with manager.connect(host=env["WLC_HOST"],
                             port=830,
                             username=WLC_USER,
                             password=WLC_PASS,
                             device_params={"name":"iosxe"},
                             hostkey_verify=False) as ncc:
            netconf_output = ncc.get(filter=("subtree", filter)).data_xml
            netconf_output = re.sub('xmlns="[^"]+"', "", netconf_output)

    except (transport.errors.SSHError, operations.errors.TimeoutExpiredError):
        netconf_output = ""
        log.error(f"NETCONF error")
    return netconf_output


def netconf_get_config(filter): #Using xmltodict

    try:
        with manager.connect(host=env["WLC_HOST"],
                             port=830,
                             username=WLC_USER,
                             password=WLC_PASS,
                             device_params={"name":"iosxe"},
                             hostkey_verify=False) as ncc:
            netconf_output = xmltodict.parse(ncc.get_config(source="running", filter=("subtree", filter)).data_xml)

    except (transport.errors.SSHError, operations.errors.TimeoutExpiredError):
        netconf_output = {}
        log.error(f"NETCONF error")
    return netconf_output