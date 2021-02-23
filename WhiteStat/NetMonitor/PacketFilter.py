import socket
import datetime
import time
#import pcapy

from struct import pack, unpack
import sys
import socket
from socket import AF_INET6

import threading, queue
import WhiteStat.NetMonitor.Dispatcher as WD
import WhiteStat.Common.Utility as UTL

class PacketFilter(threading.Thread):
    __slots__ = ['utl', 'packetQueue', 'startFlag', 'dispatcherQueue',
    'dispatcher', '_hashLock', 'ipBytesHashMap','macBytesHashMap']

    def __init__(self, packetQueue):        
        self.utl = UTL.Utility.getInstance()

        self.packetQueue = packetQueue
        self.startFlag = False

        self.dispatcherQueue = queue.Queue()
        self.dispatcher = WD.Dispatcher(self.dispatcherQueue)

        self._hashLock = threading.Lock()
        self.ipBytesHashMap = {}
        self.macBytesHashMap = {}

        super().__init__()

    def IpBytesToHash(self, ipBytes):
        if ipBytes in self.ipBytesHashMap:
            return self.ipBytesHashMap[ipBytes]
        
        utl = self.utl

        ipHash = 0
        with self._hashLock:
            ipHash = utl.IpToHash(utl.PackBytesToInt(ipBytes))
            self.ipBytesHashMap[ipBytes] = ipHash
         
        return ipHash
    
    def MacBytesToHash(self, macBytes):
        if macBytes in self.macBytesHashMap:
            return self.macBytesHashMap[macBytes]
        
        utl = self.utl

        macHash = 0
        with self._hashLock:
            macHash = utl.MacToHash(utl.PackBytesToInt(macBytes))
            self.macBytesHashMap[macBytes] = macHash
         
        return macHash

    def start(self):       
        self.startFlag = True
        super().start()
        self.dispatcher.start()

    def run(self):               

        while(self.startFlag):
            packCount = 0

            while((not self.packetQueue.empty()) and packCount <= 2000 and self.startFlag):
                packCount += 1    
                packet = None

                try:
                    packet = self.packetQueue.get_nowait()
                    self.packetQueue.task_done()                    
                except queue.Empty:
                    break

                processedPacket = (srcMac,srcIP,srcPort, dstMac,dstIP, dstPort,sizeInBytes,protocol) = self.ParsePacket(packet)                
               
                del packet

                if (sizeInBytes > 0 and 
                    (protocol == 56710 or protocol == 8) and 
                    not (srcIP <= 0 or dstIP <= 0) and 
                    not (self.utl.IsLANIPHash(srcIP) and self.utl.IsLANIPHash(dstIP)) ):

                    self.dispatcherQueue.put_nowait(processedPacket)

            time.sleep(2)


    def stop(self):

        self.dispatcher.stop()
        self.dispatcher.join()
        #self.dispatcherQueue.join()

        self.startFlag = False
        super().join()

    #function to parse a packet
    def ParsePacket(self,packet) :

        utl = self.utl
        fnIpToHash = lambda ipBytes : self.IpBytesToHash(ipBytes)
        fnMacToHash = lambda macBytes : self.MacBytesToHash(macBytes)

        srcMac = 0
        dstMac = 0
        srcIP = 0
        dstIP = 0
        srcPort = 0
        dstPort = 0
        sizeInBytes = 0
        protocol = 0
        
        #parse ethernet header
        eth_length = 14

        eth_header = packet[:eth_length]
        eth = unpack('!6s6sH' , eth_header)
        eth_protocol = socket.ntohs(eth[2])

        dstMac = fnMacToHash(packet[0:6])       
        srcMac = fnMacToHash(packet[6:12])  

        sizeInBytes = len(packet)

        #protocolInt = str(eth_protocol)
        #Parse IP V6 packets, 
        if eth_protocol == 56710:
            #IP V6 (https://github.com/Arturogv15/sniffer/blob/master/main.py)
            ip_header = packet[eth_length:40+eth_length]
            iph = unpack('!4sHBB16s16s' , ip_header)
            srcIP = fnIpToHash(iph[4])
            dstIP = fnIpToHash(iph[5])           
            
        #Parse IP V4 packets, IP Protocol number = 8
        if eth_protocol == 8 :
            #https://github.com/allfro/pcappy
            #https://www.binarytides.com/code-a-packet-sniffer-in-python-with-pcapy-extension/
            #Parse IP header
            #take first 20 characters for the ip header
            ip_header = packet[eth_length:20+eth_length]
            iph = unpack('!BBHHHBBH4s4s' , ip_header)
            srcIP = fnIpToHash(iph[8])
            dstIP = fnIpToHash(iph[9])
            #unpack('!BBH' , ip_header[0:4])[2] #is the total length from IP header


        return (srcMac,srcIP,srcPort, dstMac,dstIP, dstPort,sizeInBytes,eth_protocol)