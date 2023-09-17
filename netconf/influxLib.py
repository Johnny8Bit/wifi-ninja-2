import time
import logging

import commsLib
import envLib

env = envLib.read_config_file()
log = logging.getLogger(__name__)


def send_to_influx_wlc(env, wlc_data):

    commsLib.send_to_influx(env,
        f"wlcData,wlcName=WLC9800 "\
        f"inBytes={wlc_data['in-bytes']},"\
        f"outBytes={wlc_data['out-bytes']},"\
        f"inDrops={wlc_data['in-drops']},"\
        f"outDrops={wlc_data['out-drops']} "
    )

    commsLib.send_to_influx(env,
        f"wlcData,wlcName=WLC9800 "\
        f"connectedClients={wlc_data['all-clients']},"\
        f"authClients={wlc_data['client-states']['auth']},"\
        f"ipLearnClients={wlc_data['client-states']['iplearn']},"\
        f"webAuthClients={wlc_data['client-states']['webauth']},"\
        f"mobilityClients={wlc_data['client-states']['mobility']},"\
        f"deleteClients={wlc_data['client-states']['delete']},"\
        f"runClients={wlc_data['client-states']['run']},"\
        f"randomMacClients={wlc_data['client-states']['random-mac']} "
    )

    phy_list = [
        "Wi-Fi_6_(6GHz)",
        "Wi-Fi_6_(5GHz)",
        "Wi-Fi_6_(2.4GHz)",
        "Wi-Fi_5",
        "Wi-Fi_4_(5GHz)",
        "Wi-Fi_4_(2.4GHz)",
        "Wi-Fi_3",
        "Wi-Fi_2",
        "Wi-Fi_1"
    ]
    line_protocol = f"wlcData,wlcName=WLC9800 "
    for phy in phy_list:
        try:
            line_protocol += f"{phy}={wlc_data['per-phy'][phy]},"
        except KeyError:
            line_protocol += f"{phy}=0,"
    line_protocol = line_protocol.rstrip(",") + " "
    commsLib.send_to_influx(env, line_protocol)


def send_to_influx_ap(env, ap_data):

    all_rf_data_2ghz = ""
    all_rf_data_5ghz = ""
    all_rf_data_6ghz = ""
    for ap in ap_data.keys():
        for slot in range(0, int(env["MAX_SLOTS"])):
            slot = str(slot)
            try:
                if ap_data[ap][slot]["band"] == "dot11-2-dot-4-ghz-band":
                    rf_data_2ghz = (
                        #tags
                        f"rf2ghz,"\
                        f"apName={ap_data[ap]['ap_name']},"\
                        f"radioMode={ap_data[ap][slot]['mode']},"\
                        f"radioSlot={slot},"\
                        f"radioState={ap_data[ap][slot]['state']},"\
                        f"rfTag={ap_data[ap]['rf-tag']},"\
                        f"siteTag={ap_data[ap]['site-tag']} "\
                        #fields
                        f"radioStas={ap_data[ap][slot]['stations']},"\
                        f"radioUtil={ap_data[ap][slot]['ch_util']},"\
                        f"radioChanges={ap_data[ap][slot]['ch_changes']} "\
                        #timestamp
                        #f" {str(time.time()).replace('.', '')}"
                        f"\n"
                    )
                    all_rf_data_2ghz += rf_data_2ghz

                elif ap_data[ap][slot]["band"] == "dot11-5-ghz-band":
                    rf_data_5ghz = (
                        #tags
                        f"rf5ghz,"\
                        f"apName={ap_data[ap]['ap_name']},"\
                        f"radioMode={ap_data[ap][slot]['mode']},"\
                        f"radioSlot={slot},"\
                        f"radioState={ap_data[ap][slot]['state']},"\
                        f"rfTag={ap_data[ap]['rf-tag']},"\
                        f"siteTag={ap_data[ap]['site-tag']} "\
                        #fields
                        f"radioStas={ap_data[ap][slot]['stations']},"\
                        f"radioUtil={ap_data[ap][slot]['ch_util']},"\
                        f"radioChanges={ap_data[ap][slot]['ch_changes']} "\
                        #timestamp
                        #f" {str(time.time()).replace('.', '')}"
                        f"\n"
                    )
                    all_rf_data_5ghz += rf_data_5ghz

                elif ap_data[ap][slot]["band"] == "dot11-6-ghz-band":
                    rf_data_6ghz = (
                        #tags
                        f"rf6ghz,"\
                        f"apName={ap_data[ap]['ap_name']},"\
                        f"radioMode={ap_data[ap][slot]['mode']},"\
                        f"radioSlot={slot},"\
                        f"radioState={ap_data[ap][slot]['state']},"\
                        f"rfTag={ap_data[ap]['rf-tag']},"\
                        f"siteTag={ap_data[ap]['site-tag']} "\
                        #fields
                        f"radioStas={ap_data[ap][slot]['stations']},"\
                        f"radioUtil={ap_data[ap][slot]['ch_util']},"\
                        f"radioChanges={ap_data[ap][slot]['ch_changes']} "\
                        #timestamp
                        #f" {str(time.time()).replace('.', '')}"
                        f"\n"
                    )
                    all_rf_data_6ghz += rf_data_6ghz

            except KeyError:
                continue

    commsLib.send_to_influx(env, all_rf_data_2ghz)
    commsLib.send_to_influx(env, all_rf_data_5ghz)
    commsLib.send_to_influx(env, all_rf_data_6ghz)



