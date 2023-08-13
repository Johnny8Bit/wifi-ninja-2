import os
import json
from datetime import datetime

from flask import Flask, render_template, request

DASHBOARD_API_KEY = os.environ["DASHBOARD_API_KEY"]

dashboard = Flask(__name__)

sensor_data = {}
wlc_data = {}
ap_data = {}


def remove_stale():

    REMOVE_AFTER = 60 #seconds
    stale_data = []

    for key, value in sensor_data.items():
        lastheard = []
        date = value["sensor"]["sensor_lastheard"].split()[0].split("-")
        time = value["sensor"]["sensor_lastheard"].split()[1].split(":")
        for item in date + time:
            if item.startswith("0"):
                lastheard.append(int(item[1:]))
            else:
                lastheard.append(int(item))
        if (datetime.now() - datetime(*lastheard)).seconds > REMOVE_AFTER:
            stale_data.append(key)
            
    for sensor in stale_data:
        del sensor_data[sensor]


@dashboard.route('/PostSensorData', methods = ['POST'])
def post_sensor_data():

    global sensor_data
    
    received_auth = request.headers.get("Api-Key")
    if received_auth == DASHBOARD_API_KEY:
        received_data = json.loads(request.data)
        received_data["sensor"]["sensor_lastheard"] = str(datetime.now())[:-7]
        sensor_data[request.remote_addr] = received_data
        return 'OK', 200
    else:
        return 'NO', 401


@dashboard.route('/PostWLCData', methods = ['POST'])
def post_client_data():

    global wlc_data
    
    received_auth = request.headers.get("Api-Key")
    if received_auth == DASHBOARD_API_KEY:
        received_data = json.loads(request.data)
        received_data["lastheard"] = str(datetime.now())[:-7]
        wlc_data = received_data
        return 'OK', 200
    else:
        return 'NO', 401


@dashboard.route('/PostAPData', methods = ['POST'])
def post_ap_data():

    global ap_data
    
    received_auth = request.headers.get("Api-Key")
    if received_auth == DASHBOARD_API_KEY:
        received_data = json.loads(request.data)
        received_data["lastheard"] = str(datetime.now())[:-7]
        ap_data = received_data
        return 'OK', 200
    else:
        return 'NO', 401


@dashboard.route('/', methods = ['GET'])
def view_sensor():

    remove_stale()
    return render_template('sensor.html', data = sensor_data)


@dashboard.route('/controller', methods = ['GET'])
def view_controller():
    
    return render_template('controller.html', data = wlc_data)


@dashboard.route('/ap2', methods = ['GET'])
def view_aps_2():
    
    return render_template('ap2.html', data = ap_data)


@dashboard.route('/ap5', methods = ['GET'])
def view_aps_5():
    
    return render_template('ap5.html', data = ap_data)


@dashboard.route('/ap6', methods = ['GET'])
def view_aps_6():
    
    return render_template('ap6.html', data = ap_data)


if __name__ == '__main__':

    dashboard.run(host='0.0.0.0', port=8080, debug=False)