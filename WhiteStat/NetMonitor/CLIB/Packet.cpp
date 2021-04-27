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

struct HashedPacket
{
    ushort sourceIP;
    ushort destIP;
    ushort  sourceMAC;
    ushort  destMAC;
    uint dataSize;    
};

struct Packet
{
public:
    bool IsV6;
    BYTES sourceIP;
    BYTES destIP;
    BYTES  sourceMAC;
    BYTES  destMAC;
    uint dataSize;

    Packet(bool isV6, BYTE* srcIP, BYTE* dstIP, BYTE* srcMAC, BYTE* dstMAC,uint length);

    ~Packet() {}
    
};

Packet::Packet(bool isV6, BYTE* srcIP, BYTE* dstIP, BYTE* srcMAC, BYTE* dstMAC,uint length):
IsV6(isV6),
dataSize(length) 
{ 
    CUtility::Copy(srcIP, isV6 ? 16: 4,sourceIP);
    CUtility::Copy(dstIP, isV6 ? 16: 4, destIP);
    CUtility::Copy(srcMAC, 6, sourceMAC);
    CUtility::Copy(dstMAC, 6, destMAC);
}

#endif
