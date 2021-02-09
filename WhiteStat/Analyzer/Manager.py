import os
import time
from datetime import datetime
import WhiteStat.Common.Utility as UTL
import WhiteStat.Analyzer.Analyzer as WA
import threading, queue

class Manager(threading.Thread):

    def __init__(self):        
        self.utl = UTL.Utility.getInstance()
        self.startFlag = False
        super().__init__()

    def start(self):       
        self.startFlag = True
        super().start()

    def run(self):  

        utl = UTL.Utility.getInstance()

        dbRefreshSeconds = utl.GetUpdateDBSeconds()
        sleepSeconds = utl.GetSleepSeconds()
        totalSleepSeconds = 0

        extender = WA.Analyzer()

        while self.startFlag:

            utcDate = datetime.strptime(extender.GetNowUtc(), '%Y-%m-%d %H:%M:%S')
            today=utcDate

            startTimeFrame, startUsageFrame = None,None

            if startTimeFrame is None:
                startUsageFrame,prevUsageFrame = extender.RestoreFromDailyDB(today)       

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

                today = datetime.strptime(extender.GetNowUtc(), '%Y-%m-%d %H:%M:%S')

                if today > utcDate:
                    continue

                startTimeFrame, startUsageFrame = nextTimeFrame,nextUsageFrame

    def stop(self):        
        self.startFlag = False
        super().join()





       
    