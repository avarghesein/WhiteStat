import socket
import datetime
import time
#import pcapy

from struct import pack, unpack
import pcapy
import sys
import socket
from socket import AF_INET6

import threading, queue
import WhiteStat.NetMonitor.Dispatcher as WD
import WhiteStat.Common.Utility as UTL

class PacketFilter(threading.Thread):

    def __init__(self, packetQueue):        
        self.utl = UTL.Utility.getInstance()

        self.packetQueue = packetQueue
        self.startFlag = False

        self.dispatcherQueue = queue.Queue()
        self.dispatcher = WD.Dispatcher(self.dispatcherQueue)

        super().__init__()

    def start(self):       
        self.startFlag = True
        super().start()
        self.dispatcher.start()

    def run(self):       

        while(self.startFlag):

            while((not self.packetQueue.empty()) and self.startFlag):

                packet = None

                try:
                    packet = self.packetQueue.get_nowait()
                    self.packetQueue.task_done()                    
                except queue.Empty:
                    break

                processedPacket = (srcMac,srcIP,srcPort, dstMac,dstIP, dstPort,sizeInBytes,protocol) = self.ParsePacket(packet)
                packet = None
                
                if (sizeInBytes > 0 and 
                    (protocol == 56710 or protocol == 8)): #and 
                    #not (self.utl.IsLANIP(srcIP) and self.utl.IsLANIP(dstIP))):

                    self.dispatcherQueue.put_nowait(processedPacket)

            time.sleep(1)


    def stop(self):

        self.dispatcher.stop()
        self.dispatcher.join()
        self.dispatcherQueue.join()

        self.startFlag = False
        super().join()

        #Convert a string of 6 characters of ethernet address into a dash separated hex string
    def ParseMac (self,macByte) :
        return self.utl.PackMacBytes(macByte);


    #function to parse a packet
    def ParsePacket(self,packet) :

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

        dstMac = self.ParseMac(packet[0:6])
        srcMac = self.ParseMac(packet[6:12]) 

        #protocolInt = str(eth_protocol)
        #Parse IP V6 packets, 
        if eth_protocol == 56710:
            #IP V6 (https://github.com/Arturogv15/sniffer/blob/master/main.py)
            ip_header = packet[eth_length:40+eth_length]
            iph = unpack('!4sHBB16s16s' , ip_header)
            srcIP = iph[4]
            dstIP = iph[5]
            sizeInBytes = len(packet)
        #Parse IP V4 packets, IP Protocol number = 8
        if eth_protocol == 8 :
            #https://github.com/allfro/pcappy
            #https://www.binarytides.com/code-a-packet-sniffer-in-python-with-pcapy-extension/
            #Parse IP header
            #take first 20 characters for the ip header
            ip_header = packet[eth_length:20+eth_length]
            iph = unpack('!BBHHHBBH4s4s' , ip_header)
            srcIP = iph[8]
            dstIP = iph[9]
            sizeInBytes = len(packet)

        return (srcMac,srcIP,srcPort, dstMac,dstIP, dstPort,sizeInBytes,eth_protocol)