import os
import time
import warnings
from datetime import datetime
warnings.filterwarnings('ignore')

import pandas as pd

import WhiteStatUtils as UTL
import WhiteStat as DE

os.system('cls' if os.name == 'nt' else 'clear')

dataStore = UTL.GetEnv("DATA_STORE","/media/TMP-DSK/Python/WhiteStat_GitHub/PiDockerConfig")
#dataStore = UTL.GetEnv("DATA_STORE","/mnt/whitestat/Config")
print(dataStore)
url = UTL.GetEnv("DARKSTAT_URL","http://192.168.1.5:777")
print(url)
serverPort = UTL.GetEnv("SERVER_PORT",777)
print(serverPort)
lanSegments = UTL.GetEnv("LAN_SEGMENT_MASKS","192.168.1|192.168.0")
print(lanSegments)
lanRouters = UTL.GetEnv("LAN_ROUTERS_TO_SKIP","")
print(lanSegments)

UTL.Initialize(dataStore,url,serverPort,lanSegments,lanRouters)
utl = UTL.WhiteStatUtils.getInstance()

dbRefreshSeconds = utl.GetUpdateDBSeconds()
sleepSeconds = utl.GetSleepSeconds()
totalSleepSeconds = 0

extender = DE.WhiteStat()

while True:

    utcDate = datetime.strptime(extender.GetNowUtc(), '%Y-%m-%d %H:%M:%S')
    today=utcDate

    startTimeFrame, startUsageFrame = None,None

    if startTimeFrame is None:
        startTimeFrame, startUsageFrame,prevUsageFrame = extender.RestoreFromDailyDB(today)       

    while today <= utcDate:

        time.sleep(sleepSeconds)
        totalSleepSeconds += sleepSeconds
       
        if (startTimeFrame is None) or (startUsageFrame is None):
            startTimeFrame, startUsageFrame, prevUsageFrame = extender.GetDayFirstFrame(today, prevUsageFrame) 
                
            if prevUsageFrame is None:
                extender.ArchivePrevFrameToDB(today)
            else:
                (startTimeFrame, startUsageFrame) = (None, None)

            continue
        else:
            prevUsageFrame = None
            if totalSleepSeconds >= dbRefreshSeconds:
                extender.PersistToDailyDB(startTimeFrame, startUsageFrame,today)
                totalSleepSeconds = 0

        nextTimeFrame,nextUsageFrame = extender.GetDayNextFrame(today, startTimeFrame, startUsageFrame)

        if nextTimeFrame is None:
            continue

        os.system('cls' if os.name == 'nt' else 'clear')

        #print(nextUsageFrame)

        today = datetime.strptime(extender.GetNowUtc(), '%Y-%m-%d %H:%M:%S')

        if today > utcDate:
            continue

        startTimeFrame, startUsageFrame = nextTimeFrame,nextUsageFrame

       
    