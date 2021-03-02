
import warnings
warnings.filterwarnings('ignore')

import os
import sys
import time
import WhiteStat.Common.Utility as UTL
import WhiteStat.NetMonitor.Monitor as MTR
import WhiteStat.Analyzer.Manager as MR
import WhiteStat.Analyzer.WebServer as WS

def main(argv):    
    #os.system('cls' if os.name == 'nt' else 'clear')  
    utl = None
    try:
        role = UTL.GetEnv("ROLE","MONITOR|ANALYZER")
        print(role)
        dataStore = UTL.GetEnv("DATA_STORE","/media/TMP-DSK/Python/WhiteStatGit/WhiteStat/Test/UbuntuConfig")
        #dataStore = UTL.GetEnv("DATA_STORE","/mnt/whitestat/Config")
        print(dataStore)
        url = UTL.GetEnv("MONITOR_URL",":888")
        print(url)
        serverPort = UTL.GetEnv("ANALYZER_PORT",777)
        print(serverPort)
        hostIface = UTL.GetEnv("HOST_INTERFACE","eth0")
        print(hostIface)
        UTL.Initialize(role, dataStore, url, serverPort, hostIface)
        utl = UTL.Utility.getInstance()

        monitor = None
        analyzer = None
        webServer = None

        if(utl.IsMonitor()):
            monitor = MTR.Monitor()
            monitor.start()
        
        if(utl.IsAnalyzer()):
            analyzer = MR.Manager()
            webServer = WS.WebServer()

            analyzer.start()
            webServer.start()

        try:
            while True:
                time.sleep(30) 
        finally:
            if not (webServer is None):
                webServer.stop()

            if not (analyzer is None):
                analyzer.stop()

            if not (monitor is None):
                monitor.stop()   
        
    except Exception as e:
        if not (utl is None):
            utl.Log(e)

if __name__ == "__main__":
  main(sys.argv)
