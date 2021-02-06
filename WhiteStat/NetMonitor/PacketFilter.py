import socket
import datetime
import time
#import pcapy

from struct import pack, unpack
import pcapy
import sys
import socket

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
                    (protocol == "TCP" or protocol == "UDP" or protocol == "ICMP")): #and 
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
        return '%02x:%02x:%02x:%02x:%02x:%02x' % (macByte[0],macByte[1],macByte[2],macByte[3],
        macByte[4],macByte[5])


    #function to parse a packet
    def ParsePacket(self,packet) :

        srcMac = ""
        dstMac = ""
        srcIP = ""
        dstIP = ""
        srcPort = 0
        dstPort = 0
        sizeInBytes = 0
        protocolUsed = "NA"
        
        #parse ethernet header
        eth_length = 14

        eth_header = packet[:eth_length]
        eth = unpack('!6s6sH' , eth_header)
        eth_protocol = socket.ntohs(eth[2])

        dstMac = self.ParseMac(packet[0:6])
        srcMac = self.ParseMac(packet[6:12]) 

        #protocolInt = str(eth_protocol)

        #Parse IP packets, IP Protocol number = 8
        if eth_protocol == 8 :
            #Parse IP header
            #take first 20 characters for the ip header
            ip_header = packet[eth_length:20+eth_length]

            #now unpack them :)
            iph = unpack('!BBHHHBBH4s4s' , ip_header)

            version_ihl = iph[0]
            version = version_ihl >> 4
            ihl = version_ihl & 0xF

            iph_length = ihl * 4

            ttl = iph[5]
            protocol = iph[6]
            srcIP = s_addr = socket.inet_ntoa(iph[8]);
            dstIP = d_addr = socket.inet_ntoa(iph[9]);

            #print('Version : ' + str(version) + ' IP Header Length : ' + str(ihl) + ' TTL : ' + str(ttl) + ' Protocol : ' + str(protocol) + ' Source Address : ' + str(s_addr) + ' Destination Address : ' + str(d_addr))

            #TCP protocol
            if protocol == 6 :
                protocolUsed = "TCP"

                #t = iph_length + eth_length
                #tcp_header = packet[t:t+20]

                #now unpack them :)
                #tcph = unpack('!HHLLBBHHH' , tcp_header)

                #srcPort = source_port = tcph[0]
                #dstPort = dest_port = tcph[1]
                #sequence = tcph[2]
                #acknowledgement = tcph[3]
                #doff_reserved = tcph[4]
                #tcph_length = doff_reserved >> 4

                #print('Source Port : ' + str(source_port) + ' Dest Port : ' + str(dest_port) + ' Sequence Number : ' + str(sequence) + ' Acknowledgement : ' + str(acknowledgement) + ' TCP header length : ' + str(tcph_length))

                #h_size = eth_length + iph_length + tcph_length * 4
                #data_size = len(packet) - h_size

                #get data from the packet
                #data = packet[h_size:]

                #print 'Data : ' + data

                sizeInBytes = len(packet)

            #ICMP Packets
            elif protocol == 1 :
                protocolUsed = "ICMP"

                #u = iph_length + eth_length
                #icmph_length = 4
                #icmp_header = packet[u:u+4]

                #now unpack them :)
                #icmph = unpack('!BBH' , icmp_header)

                #icmp_type = icmph[0]
                #code = icmph[1]
                #checksum = icmph[2]

                #print('Type : ' + str(icmp_type) + ' Code : ' + str(code) + ' Checksum : ' + str(checksum))

                #h_size = eth_length + iph_length + icmph_length
                #data_size = len(packet) - h_size

                #get data from the packet
                #data = packet[h_size:]

                #print 'Data : ' + data1

                sizeInBytes = len(packet)

            #UDP packets
            elif protocol == 17 :
                protocolUsed = "UDP"

                #u = iph_length + eth_length
                #udph_length = 8
                #udp_header = packet[u:u+8]

                #now unpack them :)
                #udph = unpack('!HHHH' , udp_header)

                #srcPort = source_port = udph[0]
                #dstPort = dest_port = udph[1]
                #length = udph[2]
                #checksum = udph[3]

                #print('Source Port : ' + str(source_port) + ' Dest Port : ' + str(dest_port) + ' Length : ' + str(length) + ' Checksum : ' + str(checksum))

                #h_size = eth_length + iph_length + udph_length
                #data_size = len(packet) - h_size

                #get data from the packet
                #data = packet[h_size:]

                #print 'Data : ' + data

                sizeInBytes = len(packet)

            #some other IP packet like IGMP
            else :
                #print('Protocol other than TCP/UDP/ICMP')
                pass

        return (srcMac,srcIP,srcPort, dstMac,dstIP, dstPort,sizeInBytes,protocolUsed)