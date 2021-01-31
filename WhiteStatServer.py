import flask
import os
import warnings
from flask import request
from flask import Flask, request, send_from_directory

warnings.filterwarnings('ignore')


app = flask.Flask(__name__)
app.config["DEBUG"] = True

# set the project root directory as the static folder, you can set others.
app = Flask(__name__, static_url_path='/media/TMP-DSK/Python/WhiteStat_GitHub/UI')

import WhiteStatUtils as UTL
import WhiteStat as DE

#os.system('cls' if os.name == 'nt' else 'clear')

dataStore = UTL.GetEnv("DATA_STORE","/media/TMP-DSK/Python/WhiteStat_GitHub/RunConfig/")
#dataStore = UTL.GetEnv("DATA_STORE","/mnt/whitestat/Config")
print(dataStore)
url = UTL.GetEnv("DARKSTAT_URL","http://192.168.1.5:777")
print(url)
serverPort = UTL.GetEnv("SERVER_PORT",777)
print(serverPort)

import WhiteStatUtils as UTL
import WhiteStat as DE
import re

UTL.Initialize(dataStore,url,serverPort)
utl = UTL.WhiteStatUtils.getInstance()
extender = DE.WhiteStat()

#@app.route('/')
#def root():
#    return send_from_directory('./UI/dist', 'index.html')

#@app.route('/<path:path>')
#def send_static(path):
#    if not bool(re.search('\.[^\./]{2,4}$', path)):
#        path += "/index.html"
#    return send_from_directory('./UI/dist', path)

@app.route('/', methods=['GET'])
def daily():
    #return "<html><body>test</body></html>"
    timeframe,frame = extender.GetDailyUsageRecords()
    if not (frame is None):
        return frame.to_html()
    else:
        return "<html><body>No Data</body></html>"

@app.route('/history', methods=['GET'])
def history():
    startDate = request.args.get('start')
    endDate = request.args.get('end')

    if not startDate:
        startDate = extender.GetNowUtc()
    
    if not endDate:
        endDate = extender.GetNowUtc()

    frame = extender.GetHistoricRecords(startDate,endDate)
    if not (frame is None) and not frame.empty:
        return frame.to_html()
    else:
        return "<html><body>No Historic Data</body></html>"

if __name__ == '__main__':
    #app.run()
    app.run(host="0.0.0.0", port=utl.GetServerPort())
