
import WhiteStat.NetMonitor.pcapy as PCAPY
import sys
import socket
import time
import WhiteStat.NetMonitor.PacketFilter as PF
import WhiteStat.Common.Utility as UTL
import threading, queue

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

            pcaps = [ PCAPY.open_live(dev , 65536 , 1 , 1000) for dev in interfaces] 

            def SniffPackets(cap):
                socket.setdefaulttimeout(2)
                socket.socket();
                cap.filter = lanOnlyFilter

                def CapCallBack(userData, header, packet):
                    self.packetQueue.put_nowait(packet)
                    packet = None            

                try:
                    while(self.startFlag):
                        cap.loop(-1, CapCallBack, None)
                        #cap.dispatch(-1, CapCallBack, None)
                        time.sleep(10)
                finally:
                    cap.breakloop()
                    cap.close()
    
            if(len(pcaps) > 1):
                pThreads = [threading.Thread(target=SniffPackets, args=(cap,),daemon=True) for cap in pcaps[1:]]

                def StartThread(thread):
                    thread.start()
                    return None
                
                list(map(lambda t:StartThread(t),pThreads))

            SniffPackets(pcaps[0]) 

        except Exception as e:
            self.utl.Log(e)

    def stop(self):        
        self.packetFilter.stop()
        self.packetFilter.join()
        #self.packetQueue.join()
        self.startFlag = False
        super().join()
