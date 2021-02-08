
import WhiteStat.NetMonitor.pcapy as PCAPY
import sys
import socket
import threading, queue
import time
import WhiteStat.NetMonitor.PacketFilter as PF


class Monitor(threading.Thread):

    def __init__(self):        
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

        lans = ["0.0.0.0","192.168", "10", "172.16","172.17"]
        srcLanRange = "or".join([f" src net {net} " for net in lans])
        dstLanRange = "or".join([f" dst net {net} " for net in lans])
        lanOnlyFilter = f"not ( ({srcLanRange}) and ({dstLanRange}) )" 

        dev = "eth0"
        cap = PCAPY.open_live(dev , 65536 , 1 , 1000)
        cap.filter = lanOnlyFilter        

        def CapCallBack(userData, header, packet):
            self.packetQueue.put_nowait(packet)
            packet = None            

        while(self.startFlag):
            try:        
                while(True) :
                    cap.loop(-1, CapCallBack, None) 
                    #cap.dispatch(-1, CapCallBack, None)
                    time.sleep(10)
            except Exception:
                pass

        cap.breakloop()
        cap.close()
            


    def stop(self):
        self.packetFilter.stop()
        self.packetFilter.join()
        #self.packetQueue.join()
        self.startFlag = False
        super().join()
