import os
import time
from datetime import datetime
import WhiteStat.Common.Utility as UTL
import WhiteStat.Analyzer.Analyzer as WA
import threading, queue
import socket
import gc

class Manager(threading.Thread):

    def __init__(self):        
        self.utl = UTL.Utility.getInstance()
        self.extender = WA.Analyzer()
        self.startFlag = False
        super().__init__()


    def start(self):       
        self.startFlag = True
        super().start()

        self.dnsUpdateThread = threading.Thread(None, self.UpdateDnsRecords, args=[], daemon=True)
        self.dnsUpdateThread.start()

    def run(self):  

        dbRefreshSeconds = self.utl.GetUpdateDBSeconds()
        sleepSeconds = self.utl.GetSleepSeconds()
        totalSleepSeconds = 0
        
        while self.startFlag:

            utcDate = datetime.strptime(self.extender.GetNowUtc(), '%Y-%m-%d %H:%M:%S')
            today=utcDate

            startUsageFrame = None

            if startUsageFrame is None:
                startUsageFrame,prevUsageFrame = self.extender.RestoreFromDailyDB(today)       

            while today <= utcDate:

                time.sleep(sleepSeconds)
                totalSleepSeconds += sleepSeconds
            
                if (startUsageFrame is None):
                    startUsageFrame, prevUsageFrame = self.extender.GetDayFirstFrame(today, prevUsageFrame) 
                        
                    if prevUsageFrame is None:
                        self.extender.ArchivePrevFrameToDB(today)
                    else:
                        startUsageFrame = None

                    continue
                else:
                    prevUsageFrame = None
                    if totalSleepSeconds >= dbRefreshSeconds:
                        self.extender.PersistToDailyDB(startUsageFrame,today)
                        totalSleepSeconds = 0
                        gc.collect()

                nextUsageFrame = self.extender.GetDayNextFrame(today, startUsageFrame)

                if nextUsageFrame is None:
                    continue
                
                #os.system('cls' if os.name == 'nt' else 'clear')
                #print(self.extender.PrintableFrame(nextUsageFrame))

                today = datetime.strptime(self.extender.GetNowUtc(), '%Y-%m-%d %H:%M:%S')

                if today > utcDate:
                    continue

                startUsageFrame = nextUsageFrame

    def stop(self):        
        self.startFlag = False     
        super().join()
        self.dnsUpdateThread.join()

    
    def UpdateDnsRecords(self):
        
        while self.startFlag:
            try:
                dnsRecs = self.extender.GetEmptyDnsRecords()

                if len(dnsRecs) <= 0:
                    time.sleep(15)
                    continue

                dnsNames = {}

                for ip in dnsRecs:
                    try:
                        ipAddr = ip[0]
                        addr = socket.gethostbyaddr(ipAddr)
                        dnsNames[ipAddr] = addr[0]
                    except Exception as ex:
                        if str(ex).find("Unknown") >= 0:
                            dnsNames[ipAddr] = "(None)"
                        continue
                
                self.extender.SetDnsRecords([ [dnsNames[key], key] for key in dnsNames.keys()])
                time.sleep(5)
            except Exception as e:
                self.utl.Log(e)




       
    