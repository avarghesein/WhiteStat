
import WhiteStat.NetMonitor.pcapy as PCAPY
import sys
import socket
import threading, queue
import time
import WhiteStat.NetMonitor.PacketFilter as PF
import WhiteStat.Common.Utility as UTL


class Monitor(threading.Thread):

    def __init__(self):        
        self.utl = UTL.Utility.getInstance()
        self.startFlag = False
        self.packetQueue = queue.Queue()
        self.packetFilter = PF.PacketFilter(self.packetQueue)
        super().__init__()

    def start(self):       
        self.startFlag = True
        super().start()
        self.packetFilter.start()

    def run(self):   

        socket.setdefaulttimeout(2)
        socket.socket();

        lans = self.utl.GetV4LANMasks()

        if (lans is None) or len(lans) <= 0:
            lans = self.utl.GetAllV4LANMasks()

        srcLanRange = "or".join([f" src net {net} " for net in lans])
        dstLanRange = "or".join([f" dst net {net} " for net in lans])
        lanOnlyFilter = f"not ( ({srcLanRange}) and ({dstLanRange}) )" 

        pcapFilterExtra = self.utl.GetExtraPcapFilter()

        if (not pcapFilterExtra) and pcapFilterExtra != "":
            lanOnlyFilter += f" and ({pcapFilterExtra}) "

        interfaces = self.utl.GetHostInterfaces()        

        pcaps = [ PCAPY.open_live(dev , 65536 , 1 , 1000) for dev in interfaces]  

        def ApplyCapFilter(cap):
          cap.filter = lanOnlyFilter
          return None

        list(map(lambda cap: ApplyCapFilter(cap), pcaps))

        def CapCallBack(userData, header, packet):
            self.packetQueue.put_nowait(packet)
            packet = None            

        try:
            while(self.startFlag):

                def LoopCap(cap):
                    cap.loop(-1, CapCallBack, None)
                    return None

                list(map(lambda cap: LoopCap(cap), pcaps))       

                #cap.dispatch(-1, CapCallBack, None)
                time.sleep(10)
        finally:
            def StopCap(cap):
                cap.breakloop()
                cap.close()
                return None

            list(map(lambda cap: StopCap(cap), pcaps))
 

    def stop(self):        
        self.packetFilter.stop()
        self.packetFilter.join()
        #self.packetQueue.join()
        self.startFlag = False
        super().join()
