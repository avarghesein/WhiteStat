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
app = Flask(__name__, static_url_path='/media/TMP-DSK/Python/WhiteStat_GitHub/UI')

serverInstance = None

class WebServer(threading.Thread):

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
        app.run()
        #app.run(host="0.0.0.0", port=self.utl.GetServerPort())

    def stop(self):        
        self.startFlag = False
        super().join()
    
@app.route('/')
def root():
    return send_from_directory('./UX/dist', 'index.html')

@app.route('/<path:path>')
def send_static(path):
    if not bool(re.search('\.[^\./]{2,4}$', path)):
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
    
    return serverInstance.extender.GetHistoricRecords(startDate,endDate)

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



       
    
