#ifndef INC_Packet
#define INC_Packet

#include "./Include.hpp"
#include "./CUtility.cpp"

using std::string;

struct IPV4
{
    union
    {
        unsigned char bytes[4];
        unsigned int  address;
    } address;
};

struct Packet
{
private:


public:
    int IsV6;
    BYTES sourceIP;
    BYTES destIP;
    BYTES  sourceMAC;
    BYTES  destMAC;
    unsigned int dataSize;

    Packet(int isV6, BYTE* srcIP, BYTE* dstIP, BYTE* srcMAC, BYTE* dstMAC,unsigned int length);

    ~Packet() {}
    
};

Packet::Packet(int isV6, BYTE* srcIP, BYTE* dstIP, BYTE* srcMAC, BYTE* dstMAC,unsigned int length):
IsV6(isV6),
dataSize(length) 
{ 
    CUtility::Copy(srcIP, isV6 ? 16: 4,sourceIP);
    CUtility::Copy(dstIP, isV6 ? 16: 4, destIP);
    CUtility::Copy(srcMAC, 6, sourceMAC);
    CUtility::Copy(dstMAC, 6, destMAC);
}

#endif
