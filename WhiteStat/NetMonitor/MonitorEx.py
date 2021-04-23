
import WhiteStat.NetMonitor.CLIB.Wrapper as PCAPY
import sys
import time
import WhiteStat.Common.Utility as UTL
import WhiteStat.NetMonitor.RemoteServerEx as RS
import threading, queue

class Monitor(threading.Thread):
    __slots__ = ['utl', 'startFlag', 'pcapyWrapper', 'remoteServer', 'remoteManager']

    def __init__(self):        
        self.utl = UTL.Utility.getInstance()
        self.startFlag = False
        self.pcapyWrapper = PCAPY.Wrapper()
        self.remoteServer = RS.RemoteServer()
        self.remoteManager = RS.RemoteManager()
        super().__init__()

    def start(self):       
        self.startFlag = True
        super().start()
        self.remoteServer.start()

    def run(self):  
        try:
            lans = self.utl.GetV4LANMasks()

            if (lans is None) or len(lans) <= 0:
                lans = self.utl.GetAllV4LANMasks()

            srcLanRange = "or".join([f" src net {net} " for net in lans])
            dstLanRange = "or".join([f" dst net {net} " for net in lans])
            lanOnlyFilter = f"not ( ({srcLanRange}) and ({dstLanRange}) )" 

            pcapFilterExtra = self.utl.GetExtraPcapFilter()

            if (not pcapFilterExtra) and pcapFilterExtra != "":
                lanOnlyFilter += f" and ({pcapFilterExtra}) "

            lanOnlyFilter += " and not (multicast or ip multicast or ip6 multicast)"

            interfaces = self.utl.GetHostInterfaces()        

            self.pcapyWrapper.StartCapture(
                "|".join(interfaces),lanOnlyFilter,
                "|".join(lans), "|".join(self.utl.GetV6LANMasks()),
                self.utl.GetSleepSeconds(),self.utl.GetUpdateDBSeconds(),
                self.utl.GetLog(),self.utl.GetTrace())

            while self.startFlag:
                time.sleep(self.utl.GetUpdateDBSeconds())
                self.RefreshFrames()

        except Exception as e:
            self.utl.Log(e)

    def RefreshFrames(self):
        (date, localFrame, remoteFrame) = self.pcapyWrapper.GetFrames()
        usageFrame = RS.RemoteUsageFrame.getInstance()
        usageFrame.SetFrame(date, localFrame, remoteFrame)

    def stop(self):     
        self.remoteServer.stop()   
        self.pcapyWrapper.StopCapture()
        self.startFlag = False
        super().join()
