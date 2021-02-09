
import warnings
warnings.filterwarnings('ignore')

import os
import sys
import time
import WhiteStat.Common.Utility as UTL
import WhiteStat.NetMonitor.Monitor as MTR
import WhiteStat.Analyzer.Manager as MR

def main(argv):

    os.system('cls' if os.name == 'nt' else 'clear')

    dataStore = UTL.GetEnv("DATA_STORE","/media/TMP-DSK/Python/WhiteStatGit/WhiteStat/Test/UbuntuConfig")
    #dataStore = UTL.GetEnv("DATA_STORE","/mnt/whitestat/Config")
    print(dataStore)
    url = UTL.GetEnv("MONITOR",":888")
    print(url)
    serverPort = UTL.GetEnv("SERVER_PORT",777)
    print(serverPort)
    hostIface = UTL.GetEnv("HOST_INTERFACE","eth0")
    print(hostIface)

    UTL.Initialize(dataStore,url,serverPort,hostIface)
    utl = UTL.Utility.getInstance()

    monitor = MTR.Monitor()
    analyzer = MR.Manager()

    monitor.start()
    analyzer.start()

    try:
        while True:
            time.sleep(15) 
    finally:
        monitor.stop()
        analyzer.stop()

if __name__ == "__main__":
  main(sys.argv)