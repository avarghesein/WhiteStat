#ifndef INC_CPcap
#define INC_CPcap

#include "./Include.hpp"
#include "./Packet.cpp"

using std::string;
using PacketQueue = std::queue<std::shared_ptr<Packet>>;

class CPcap
{
    private:
        string _iface;       
        pcap_t*_handle; 
        char _sourceIp[INET6_ADDRSTRLEN];
	    char _destIp[INET6_ADDRSTRLEN];
        char _sourceMAC[20];
	    char _destMAC[20];
        PacketQueue& _queue;
    
    private:
        bool HandlePacket(u_char *userData, const struct pcap_pkthdr* pkthdr, const u_char* packet);

    public:
        CPcap(string& iface, PacketQueue& queue);
        bool Open();
        bool Close();
        std::future<bool> CaptureLoop();
};


CPcap::CPcap(string& iface, PacketQueue& queue) : _iface(iface), _handle(nullptr),
_queue(queue) {}

bool CPcap::Close()
{
    if(_handle != nullptr)
    {
        try
        {
            char errbuf[256];
            pcap_breakloop(_handle);
            pcap_close(_handle);
            _handle = nullptr;
        }
        catch(const std::exception& e)
        {
            //std::cerr << e.what() << '\n';
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
            char errbuf[256];
            _handle = pcap_open_live(_iface.c_str(), 65536 , 1 , 1000, errbuf);
        }
        catch(const std::exception& e)
        {
            //std::cerr << e.what() << '\n';
        }        

        if(!_handle) return false;
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
            auto looper = [&]()->bool {
                return pcap_loop(_handle,-1, handler,(u_char*)(this)) != 0;
            };

            std::future<bool> loopFun = std::async(std::launch::async,looper);

            return loopFun;
        }
        catch(const std::exception& e)
        {
            //std::cerr << e.what() << '\n';
        }        

        if(!_handle) throw std::invalid_argument( "Invalid Handle" );
    }

    throw std::invalid_argument( "Already started Capturing" );
}

bool CPcap::HandlePacket(u_char *userData, const struct pcap_pkthdr* pkthdr, const u_char* packet)
{
	const struct ether_header* eHeader = (struct ether_header*) packet;
    int len = sizeof(struct ether_header);

    snprintf(_sourceMAC, 20, "%s", ether_ntoa((struct ether_addr *)eHeader->ether_shost));
    snprintf(_destMAC, 20, "%s", ether_ntoa((struct ether_addr *)eHeader->ether_dhost));

    if (ntohs(eHeader->ether_type) == ETHERTYPE_IP)
    {
        const struct ip* ipHeader = (struct ip*)(packet + sizeof(struct ether_header));
		inet_ntop(AF_INET, &(ipHeader->ip_src), _sourceIp, INET_ADDRSTRLEN);
		inet_ntop(AF_INET, &(ipHeader->ip_dst), _destIp, INET_ADDRSTRLEN);
        len += ntohs(ipHeader->ip_len);
    }
    if (ntohs(eHeader->ether_type) == ETHERTYPE_IPV6)
    {        
        const struct ip6_hdr* ipHeader = (struct ip6_hdr*)(packet + sizeof(struct ether_header));
		inet_ntop(AF_INET6, &(ipHeader->ip6_src), _sourceIp, INET6_ADDRSTRLEN);
		inet_ntop(AF_INET6, &(ipHeader->ip6_dst), _destIp, INET6_ADDRSTRLEN);
        len += ntohs(ipHeader->ip6_ctlun.ip6_un1.ip6_un1_plen);
    }

    _queue.push(std::shared_ptr<Packet>(new Packet(_sourceIp,_destIp,_sourceMAC,_destMAC,len)));

    return true;
}

#endif