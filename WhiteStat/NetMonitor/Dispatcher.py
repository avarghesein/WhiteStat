import datetime
import time
import os
import threading, queue
import WhiteStat.Common.Utility as UTL
import WhiteStat.NetMonitor.RemoteServer as RS
import gc

class Dispatcher(threading.Thread):
    __slots__ = ['utl', 'dispatcherQueue', 'startFlag', 'remoteServer', 'remoteManager', 
    'localIPs','remoteIPs']

    def __init__(self, dispatcherQueue):
        
        self.dispatcherQueue = dispatcherQueue
        self.startFlag = False
        super().__init__()

        self.utl = UTL.Utility.getInstance()

        self.remoteServer = RS.RemoteServer()
        self.remoteManager = RS.RemoteManager()

        self.localIPs = {}
        self.remoteIPs = {}

 
    def start(self):
        self.startFlag = True
        super().start()
        self.remoteServer.start()        

    def run(self):

        sleepSeconds = 1
        remoteRefreshSeconds = self.utl.GetSleepSeconds()
        sleptSeconds = 0
        curDate = datetime.datetime.now().date()

        while(self.startFlag):
            packCount = 0

            while((not self.dispatcherQueue.empty()) and packCount <= 2000 and self.startFlag):
                packCount += 1
                packet = None

                try:
                    packet = (srcMac,srcIP,srcPort, dstMac,dstIP, dstPort,sizeInBytes,protocol) = self.dispatcherQueue.get_nowait()
                    self.dispatcherQueue.task_done()

                except queue.Empty:
                    break

                lastSeen = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.PopulateFrame(srcMac,srcIP,sizeInBytes,lastSeen,True)
                self.PopulateFrame(dstMac,dstIP,sizeInBytes,lastSeen,False)               
                packet = None

                if sleptSeconds >= remoteRefreshSeconds:
                    utl = self.utl
                    fnHashToIp = lambda ipHash : utl.HashToIp(ipHash)    
                    fnHashToMac = lambda macHash : utl.HashToMac(macHash) 

                    localIPS = { fnHashToMac(key) : [fnHashToIp(value[0])] + value[1:]
                    for key, value in self.localIPs.items() }

                    remoteIPs = { fnHashToIp(key) : [fnHashToMac(value[0])] + value[1:]
                    for key, value in self.remoteIPs.items() }

                    #client = RS.RemoteManager()
                    #client.connect()
                    #curFrame = client.RemoteUsageFrame()
                    #curFrame.SetFrame(localIPS,remoteIPs)
                    localMonitor = RS.RemoteUsageFrame.getInstance()
                    localMonitor.SetFrame(localIPS,remoteIPs)

                    sleptSeconds = 0
                    gc.collect()

                    #curFrame = client.RemoteUsageFrame()
                    #remoteFrame = curFrame.GetFrame()                   
                    #os.system('cls' if os.name == 'nt' else 'clear')
                    #self.PrintFrame(remoteFrame[0],remoteFrame[1])

                    today = datetime.datetime.now().date()

                    if today > curDate:
                        self.localIPs.clear()
                        self.remoteIPs.clear()
                        curDate = today

            time.sleep(sleepSeconds)
            sleptSeconds += sleepSeconds

    def PrintFrame(self, localFrame,remoteFrame):
        frame = localFrame
        vals = "\n".join([f'{self.utl.UnPackPackedIntToString(key)}\t{self.utl.UnPackIPPackedIntToString(value[0])}\t{value[1]}\t{value[2]}\t{value[3]}' for key, value in frame.items()])
        print(vals)
        frame = remoteFrame
        vals = "\n".join([f'{self.utl.UnPackIPPackedIntToString(key)}\t{self.utl.UnPackPackedIntToString(value[0])}\t{value[1]}\t{value[2]}\t{value[3]}' for key, value in frame.items()])
        print(vals)

    def PopulateFrame(self, mac,ip,sizeInBytes,lastSeen, isSource = True):
        IP_IDX = 0
        MAC_IDX = 0
        IN_IDX = 1
        OUT_IDX = 2
        SEEN_IDX = 3

        rec = []

        if self.utl.IsLANIPHash(ip):
            frame = self.localIPs

            if ( mac in frame.keys()):
                rec = frame[mac]
                rec[IP_IDX] = ip
                rec[SEEN_IDX] = lastSeen
            else:
                #IP,IN,OUT,SEEN
                frame[mac] = rec = [ip,0,0,lastSeen]
        else:
            frame = self.remoteIPs

            if ( ip in frame.keys()):
                rec = frame[ip]                
                rec[MAC_IDX] = mac
                rec[SEEN_IDX] = lastSeen
            else:
                #MAC,IN,OUT,SEEN
                frame[ip] = rec = [mac,0,0,lastSeen]

        if isSource:
            rec[OUT_IDX] += sizeInBytes
        else:
            rec[IN_IDX] += sizeInBytes

    def stop(self):
        self.remoteServer.stop()
        self.startFlag = False
        super().join()        