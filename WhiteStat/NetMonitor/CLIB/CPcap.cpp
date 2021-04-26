#ifndef INC_CPcap
#define INC_CPcap

#include "./Include.hpp"
#include "./Packet.cpp"
#include "./CUtility.cpp"

using std::string;
using PacketQueue = std::queue<std::shared_ptr<Packet>>;

class CPcap
{
    private:
        CUtility& _utility;
        string _iface;  
   
        pcap_t*_handle; 
        struct bpf_program _filterProgram; 
        char _errbuf[256];       
        //char _sourceIp[INET6_ADDRSTRLEN];
	    //char _destIp[INET6_ADDRSTRLEN];
        //char _sourceMAC[20];
	    //char _destMAC[20];
        PacketQueue& _queue;
    
    private:
        char* ConvertToMACString(const struct ether_addr *addr, char *buf);
        bool HandlePacket(u_char *userData, const struct pcap_pkthdr* pkthdr, const u_char* packet);
        bool SetFilter();

    public:
        CPcap(string& iface, CUtility& utility, PacketQueue& queue);
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

CPcap::CPcap(string& iface, CUtility& utility, PacketQueue& queue) : _iface(iface), _handle(nullptr),
_queue(queue), _utility(utility) {}

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

char* CPcap::ConvertToMACString(const struct ether_addr *addr, char *buf)
{
    sprintf(buf, "%02x:%02x:%02x:%02x:%02x:%02x",
            addr->ether_addr_octet[0], addr->ether_addr_octet[1],
            addr->ether_addr_octet[2], addr->ether_addr_octet[3],
            addr->ether_addr_octet[4], addr->ether_addr_octet[5]);
    return buf;
}

bool CPcap::HandlePacket(u_char *userData, const struct pcap_pkthdr* pkthdr, const u_char* packet)
{
	const struct ether_header* eHeader = (struct ether_header*) packet;
    int len = sizeof(struct ether_header);

    //ConvertToMACString((const struct ether_addr *)eHeader->ether_shost, _sourceMAC);
    //ConvertToMACString((const struct ether_addr *)eHeader->ether_dhost, _destMAC);
    //snprintf(_sourceMAC, 20, "%s", ether_ntoa((struct ether_addr *)eHeader->ether_shost));
    //snprintf(_destMAC, 20, "%s", ether_ntoa((struct ether_addr *)eHeader->ether_dhost));

    BYTE* srcMac = const_cast<BYTE*>(eHeader->ether_shost);
    BYTE* dstMac = const_cast<BYTE*>(eHeader->ether_dhost);

    if (ntohs(eHeader->ether_type) == ETHERTYPE_IP)
    {
        const struct ip* ipHeader = (struct ip*)(packet + sizeof(struct ether_header));
        IPV4 srcV4, dstV4;
        srcV4.address.address = ipHeader->ip_src.s_addr;
        dstV4.address.address = ipHeader->ip_dst.s_addr;
		//inet_ntop(AF_INET, &(ipHeader->ip_src), _sourceIp, INET_ADDRSTRLEN);
		//inet_ntop(AF_INET, &(ipHeader->ip_dst), _destIp, INET_ADDRSTRLEN);
        len += ntohs(ipHeader->ip_len);

        _queue.push(std::shared_ptr<Packet>(new Packet(false,srcV4.address.bytes,dstV4.address.bytes,srcMac,dstMac,len)));
    }
    if (ntohs(eHeader->ether_type) == ETHERTYPE_IPV6)
    {        
        const struct ip6_hdr* ipHeader = (struct ip6_hdr*)(packet + sizeof(struct ether_header));
        auto srcIp = const_cast<BYTE*>(ipHeader->ip6_src.__in6_u.__u6_addr8);
        auto dstIp = const_cast<BYTE*>(ipHeader->ip6_dst.__in6_u.__u6_addr8);
		//inet_ntop(AF_INET6, &(ipHeader->ip6_src), _sourceIp, INET6_ADDRSTRLEN);
		//inet_ntop(AF_INET6, &(ipHeader->ip6_dst), _destIp, INET6_ADDRSTRLEN);
        len += ntohs(ipHeader->ip6_ctlun.ip6_un1.ip6_un1_plen);

        _queue.push(std::shared_ptr<Packet>(new Packet(true,srcIp,dstIp,srcMac,dstMac,len)));
    }

    return true;
}

#endif