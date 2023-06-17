from flask import Flask, render_template, request
import json

web_monitor = Flask(__name__)

sensor_data = []

@web_monitor.route('/PostMonitorData', methods = ['POST'])
def data():

    global sensor_data
    sensor_data = (json.loads(request.data))
    return 'OK', 200

@web_monitor.route('/', methods = ['GET'])
def index():
    
    return render_template('index.html', data_list = sensor_data)


if __name__ == '__main__':

    web_monitor.run(host='0.0.0.0', port=80, debug=False)