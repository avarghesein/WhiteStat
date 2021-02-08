
import os
import sys
import time
import WhiteStat.Common.Utility as UTL
import WhiteStat.NetMonitor.Monitor as MTR

def main(argv):

    os.system('cls' if os.name == 'nt' else 'clear')

    dataStore = UTL.GetEnv("DATA_STORE","/media/TMP-DSK/Python/WhiteStatGit/WhiteStat/Test/UbuntuConfig")
    #dataStore = UTL.GetEnv("DATA_STORE","/mnt/whitestat/Config")
    print(dataStore)
    url = UTL.GetEnv("MONITOR",":888")
    print(url)
    serverPort = UTL.GetEnv("SERVER_PORT",777)

    UTL.Initialize(dataStore,url,serverPort)
    utl = UTL.Utility.getInstance()

    monitor = MTR.Monitor()
    monitor.start()

    try:
        while True:
            time.sleep(15) 
    except:
        monitor.stop()

if __name__ == "__main__":
  main(sys.argv)