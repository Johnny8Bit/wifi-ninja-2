import json

from flask import Flask, render_template, request

DASHBOARD_API_KEY = "12345"


dashboard = Flask(__name__)

sensor_data = {}


@dashboard.route('/PostSensorData', methods = ['POST'])
def data():

    global sensor_data
    received_auth = request.headers.get("api_key")
    if received_auth == DASHBOARD_API_KEY:
        sensor_data.update(json.loads(request.data))
        return 'OK', 200
    else:
        return 'Nope', 401


@dashboard.route('/', methods = ['GET'])
def index():
    print(sensor_data)
    return render_template('index.html', data = sensor_data)


if __name__ == '__main__':

    dashboard.run(host='0.0.0.0', port=80, debug=False)