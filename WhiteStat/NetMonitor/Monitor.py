import socket
import datetime
#import pcapy

from struct import pack, unpack
import pcapy
import sys
import socket
import threading, queue
import  WhiteStat.NetMonitor.PacketFilter as WF
import os
import time

import  WhiteStat.Common.Utility as UTL


def main(argv):

    os.system('cls' if os.name == 'nt' else 'clear')

    dataStore = UTL.GetEnv("DATA_STORE","/media/TMP-DSK/Python/WhiteStatGit/WhiteStat/Test/UbuntuConfig")
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
    utl = UTL.Utility.getInstance()

    #list all devices
    #devices = pcapy.findalldevs()
    '''
    open device
    # Arguments here are:
    #   device
    #   snaplen (maximum number of bytes to capture _per_packet_)
    #   promiscious mode (1 for true)
    #   timeout (in milliseconds)
    '''
    socket.setdefaulttimeout(2)
    socket.socket();
    #s.settimeout(100); 

    lans = ["192.168", "10", "172.16","172.17"]
    srcLanRange = "or".join([f" src net {net} " for net in lans])
    dstLanRange = "or".join([f" dst net {net} " for net in lans])
    lanOnlyFilter = f"not ( ({srcLanRange}) and ({dstLanRange}) )" 

    dev = "eth0"
    cap = pcapy.open_live(dev , 65536 , 1 , 1000)
    cap.filter = lanOnlyFilter

    packetQueue = queue.Queue()
    packetFilter = WF.PacketFilter(packetQueue)
    packetFilter.start()

    def CapCallBack(userData, header, packet):
        packetQueue.put_nowait(packet)
        packet = None

    #start sniffing packets
    #cap.loop(-1, CapCallBack, None)  

    try:        
        while(True) :
            cap.dispatch(-1, CapCallBack, None)
            time.sleep(5)
    except Exception:
        pass

    cap.breakloop()
    cap.close()
    packetFilter.stop()
    packetFilter.join()
    packetQueue.join()

if __name__ == "__main__":
  main(sys.argv)