#ifndef INC_CPcap
#define INC_CPcap

#include "./Include.hpp"
#include "./Packet.cpp"
#include "./CUtility.cpp"
#include "./CPacketProcessor.cpp"

using std::string;
using PacketQueue = std::queue<std::shared_ptr<HashedPacket>>;

class CPcap
{
    private:
        CUtility& _utility;
        string _iface;  
   
        pcap_t*_handle; 
        struct bpf_program _filterProgram; 
        char _errbuf[256];       
        PacketQueue& _queue;
        CPacketProcessor& _processor;
    
    private:
        bool HandlePacket(u_char *userData, const struct pcap_pkthdr* pkthdr, const u_char* packet);
        bool SetFilter();

    public:
        CPcap(string& iface, CUtility& utility, PacketQueue& queue,CPacketProcessor& processor);
        ~CPcap();
        bool Open();
        bool Close();        
        std::future<bool> CaptureLoop();        
};

bool CPcap::SetFilter()
{
    if(_handle == nullptr ) return  false;

    if (pcap_compile(_handle, &_filterProgram, _utility.GetPcapFilter().c_str(), 0, PCAP_NETMASK_UNKNOWN) == -1) 
    {
        _utility.Log(pcap_geterr(_handle));
        return false;
    }

    if (pcap_setfilter(_handle, &_filterProgram) == -1) 
    {
        _utility.Log(pcap_geterr(_handle));
        return false;
    }
    return true;
}

CPcap::~CPcap()
{
    Close();
}

CPcap::CPcap(string& iface, CUtility& utility, PacketQueue& queue, CPacketProcessor& processor) : _iface(iface), _handle(nullptr),
_queue(queue), _utility(utility), _processor(processor) {}

bool CPcap::Close()
{
    if(_handle != nullptr)
    {
        try
        {
            pcap_breakloop(_handle);
            pcap_close(_handle);
            _handle = nullptr;
        }
        catch(const std::exception& e)
        {
            _utility.Log(e.what());
            return false;
        } 
    }

    return true;
}

bool CPcap::Open()
{    
    if(_handle == nullptr)
    {
        try
        {
            _handle = pcap_open_live(_iface.c_str(), 65536 , 1 , 1000, _errbuf);
        }
        catch(const std::exception& e)
        {
            _utility.Log(e.what());
        }        

        if(!_handle) 
        {
            _utility.Log(_errbuf);
            return false;
        }
    }

    return true;
}

std::future<bool> CPcap::CaptureLoop()
{
    if(_handle != nullptr)
    {
        auto handler = [](u_char* userData, const struct pcap_pkthdr *hdr, const u_char *packet) {
            if(packet != nullptr)
            {
                ((CPcap*)userData)->HandlePacket(userData,hdr,packet);
            }
        };

        try
        {
            SetFilter();

            auto looper = [&]()->bool {
                return pcap_loop(_handle,-1, handler,(u_char*)(this)) != 0;
            };

            auto captureFuture = std::async(std::launch::async,looper);

            return captureFuture;
        }
        catch(const std::exception& e)
        {
            _utility.Log(e.what());
        }        

        if(!_handle) throw std::invalid_argument( "Invalid Handle" );
    }

    throw std::invalid_argument( "Already started Capturing" );
}

bool CPcap::HandlePacket(u_char *userData, const struct pcap_pkthdr* pkthdr, const u_char* packet)
{
	const struct ether_header* eHeader = (struct ether_header*) packet;
    int len = sizeof(struct ether_header);

    if (ntohs(eHeader->ether_type) == ETHERTYPE_IP)
    {
        const struct ip* ipHeader = (struct ip*)(packet + sizeof(struct ether_header));
        len += ntohs(ipHeader->ip_len);

        auto hashedPacket = new HashedPacketV4();
        hashedPacket->dataSize = len;

        std::memcpy(&(hashedPacket->sourceMAC),&(eHeader->ether_shost),sizeof(struct ether_addr));
        std::memcpy(&(hashedPacket->destMAC),&(eHeader->ether_dhost),sizeof(struct ether_addr));

        std::memcpy(&(hashedPacket->sourceIP),&(ipHeader->ip_src),sizeof(struct IPV4_addr));
        std::memcpy(&(hashedPacket->destIP),&(ipHeader->ip_dst),sizeof(struct IPV4_addr));

        _queue.push(std::shared_ptr<HashedPacket>(hashedPacket));
    }
    if (ntohs(eHeader->ether_type) == ETHERTYPE_IPV6)
    {        
        const struct ip6_hdr* ipHeader = (struct ip6_hdr*)(packet + sizeof(struct ether_header));
        len += ntohs(ipHeader->ip6_ctlun.ip6_un1.ip6_un1_plen);

        auto hashedPacket = new HashedPacketV6();
        hashedPacket->dataSize = len;

        std::memcpy(&(hashedPacket->sourceMAC),&(eHeader->ether_shost),sizeof(struct ether_addr));
        std::memcpy(&(hashedPacket->destMAC),&(eHeader->ether_dhost),sizeof(struct ether_addr));

        std::memcpy(&(hashedPacket->sourceIP),&(ipHeader->ip6_src),sizeof(struct in6_addr));
        std::memcpy(&(hashedPacket->destIP),&(ipHeader->ip6_dst),sizeof(struct in6_addr));

        _queue.push(std::shared_ptr<HashedPacket>(hashedPacket));
    }

    return true;
}

#endif