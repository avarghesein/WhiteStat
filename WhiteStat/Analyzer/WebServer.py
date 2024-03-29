import os
import time
import json 
import re
from datetime import datetime
import WhiteStat.Common.Utility as UTL
import WhiteStat.Analyzer.Analyzer as WA
import threading, queue
import flask
from flask import (
    Flask, 
    request, 
    Response, 
    send_from_directory,
    g,
    redirect,
    render_template,
    url_for,
    jsonify,
)

app = flask.Flask(__name__)
app.config["DEBUG"] = True
# set the project root directory as the static folder, you can set others.
app = Flask(__name__, static_url_path='/mnt/app/')

app.config['CORS_HEADERS'] = 'Content-Type'

serverInstance = None

class WebServer(threading.Thread):
    __slots__ = ['utl', 'extender', 'startFlag']

    def __init__(self):        
        self.utl = UTL.Utility.getInstance()
        self.extender = WA.Analyzer()
        self.startFlag = False
        super().__init__()
        global serverInstance
        serverInstance = self

    def start(self):       
        self.startFlag = True
        super().start()

    def run(self):         
        #app.run()
        app.run(host="0.0.0.0", port=self.utl.GetServerPort())

    def stop(self):        
        self.startFlag = False

        func = request.environ.get('werkzeug.server.shutdown')
        if not (func is None):
            func()
        
        super().join()
    

@app.route('/')
def root():
    return send_from_directory('./UX/dist', 'index.html')

@app.route('/<path:path>')
def send_static(path):
    if not bool(re.search('\.[^\./]{2,5}$', path)):
        path += "/index.html"
    return send_from_directory('./UX/dist', path)

@app.route('/json', methods=['GET'])
def dailyJson():
    #return "<html><body>test</body></html>"
    frame = serverInstance.extender.GetDailyUsageRecords()

    response = None

    if not (frame is None):
        response = jsonify(frame)
    else:
        response = Response("<html><body>No Historic Data</body></html>")
    
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

def GetHistory():
    startDate = request.args.get('start')
    endDate = request.args.get('end')

    if not startDate:
        startDate = serverInstance.extender.GetNowUtc()
    
    if not endDate:
        endDate = serverInstance.extender.GetNowUtc()

    if startDate > endDate:
        startDate, endDate = endDate, startDate
    
    publicIP = request.args.get('includePublicIP')
    includePublicIPs = False
    if publicIP and publicIP.lower() == "yes":
        includePublicIPs = True

    return serverInstance.extender.GetHistoricRecords(startDate, endDate, includePublicIPs)

@app.route('/json/history', methods=['GET'])
def historyJson():
    frame = GetHistory()

    response = None

    if not (frame is None):
        response = jsonify(frame)       
    else:
        response = Response("<html><body>No Historic Data</body></html>")
    
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

@app.route('/json/lansegments', methods=['GET'])
def lanSegmentsJson():
    lans = serverInstance.utl.GetLANSegments()
    response = Response(json.dumps(lans),  mimetype='application/json')
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

@app.route('/json/hostname', methods=['POST'])
def updateHostName():
    json_data = json.loads([ formData for formData in flask.request.form][0])
    ip = json_data['ip']
    mac = json_data['mac']
    hostName = json_data['name']
    isLocal = json_data['local']
    serverInstance.extender.SetHostName(ip,mac,hostName,isLocal)
    response = Response(json.dumps(json_data["name"]),  mimetype='application/json')
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

    




       
    
