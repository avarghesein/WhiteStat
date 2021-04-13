#ifndef INC_Packet
#define INC_Packet

#include "./Include.hpp"

using std::string;

struct Packet
{
    string sourceIP;
    string destIP;
    string sourceMAC;
    string destMAC;
    unsigned int dataSize;

    Packet(char* srcIP, char* dstIP, char* srcMAC, char* dstMAC,unsigned int length);

    ~Packet() {}
    
};

Packet::Packet(char* srcIP, char* dstIP, char* srcMAC, char* dstMAC,unsigned int length):
sourceIP(srcIP), destIP(dstIP),
sourceMAC(srcMAC), destMAC(dstMAC),
dataSize(length)
{
}

#endif
