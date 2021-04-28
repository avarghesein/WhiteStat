#ifndef INC_Packet
#define INC_Packet

#include "./Include.hpp"
#include "./CUtility.cpp"

using std::string;

struct IPV4_addr
{
    union
    {
        unsigned char bytes[4];
        unsigned int  address;
    } address;
};

struct HashedPacket
{
    uint dataSize;
    ether_addr  sourceMAC;
    ether_addr  destMAC;

    virtual ~HashedPacket() {};
};

struct HashedPacketV4 : public HashedPacket
{
    IPV4_addr sourceIP;
    IPV4_addr destIP;
};

struct HashedPacketV6 : public HashedPacket
{
    in6_addr sourceIP;
    in6_addr destIP;
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
