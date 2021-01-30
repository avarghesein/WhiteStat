import os
import time
import warnings
from datetime import datetime
warnings.filterwarnings('ignore')

import pandas as pd

import WhiteStatUtils as UTL
import WhiteStat as DE

os.system('cls' if os.name == 'nt' else 'clear')

dataStore = UTL.GetEnv("DATA_STORE","/media/TMP-DSK/Python/WhiteStat_GitHub/RunConfig")
#dataStore = UTL.GetEnv("DATA_STORE","/mnt/whitestat/Config")
print(dataStore)
url = UTL.GetEnv("DARKSTAT_URL","http://192.168.1.5:777")
print(url)
serverPort = UTL.GetEnv("SERVER_PORT",777)
print(serverPort)

UTL.Initialize(dataStore,url,serverPort)
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
        startTimeFrame, startUsageFrame,prevUsageFrame = extender.RestoreFromDailyDB()

    while today <= utcDate:

        time.sleep(sleepSeconds)
        totalSleepSeconds += sleepSeconds
       
        if (startTimeFrame is None) or (startUsageFrame is None):
            startTimeFrame, startUsageFrame, prevUsageFrame = extender.GetDayFirstFrame(prevUsageFrame) 
                
            if prevUsageFrame is None:
                extender.ArchivePrevFrameToDB()
            continue
        else:
            if totalSleepSeconds >= dbRefreshSeconds:
                extender.PersistToDailyDB(startTimeFrame, startUsageFrame)
                totalSleepSeconds = 0

        nextTimeFrame,nextUsageFrame = extender.GetDayNextFrame(startTimeFrame, startUsageFrame)

        if nextTimeFrame is None:
            continue

        os.system('cls' if os.name == 'nt' else 'clear')

        #print(nextUsageFrame)

        startTimeFrame, startUsageFrame = nextTimeFrame,nextUsageFrame

        today = datetime.strptime(extender.GetNowUtc(), '%Y-%m-%d %H:%M:%S')
    