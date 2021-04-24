#include "./Include.hpp"
#include "./Packet.cpp"
#include "CPcap.cpp"
#include "CPacketProcessor.cpp"

using namespace std::string_literals;
using namespace std::chrono_literals;

using std::string;
using FutureQueue = std::queue<std::shared_ptr<std::future<bool>>>;
using PacketQueue = std::queue<std::shared_ptr<Packet>>;
using CapList = std::vector<std::shared_ptr<CPcap>>;
using boost::container::deque;

CUtility* Utility = nullptr;
PacketQueue* Queue = nullptr; 
CPacketProcessor* Processor = nullptr;
FutureQueue FutureList;
CapList PcapList;

extern "C" void StartCapture(
    const char* ifaces, const char* pcapFilter, 
    const char* v4LanMask, const char* v6LanMask,
    int sleepSeconds,
    int frameRefreshSeconds,
    const char* logFile,
    const char* traceFile
)
{
    Utility = new CUtility(ifaces,pcapFilter,
        v4LanMask, v6LanMask,
        sleepSeconds, frameRefreshSeconds,
        logFile,traceFile);
    
    Queue = new PacketQueue();    

    for(auto iface : Utility->GetInterfaces())
    {
        auto capPtr = std::shared_ptr<CPcap>(new CPcap(iface, *Utility, *Queue));

        if(!capPtr->Open())
        {
            delete Queue;
            Queue = nullptr;
            delete Utility;
            Utility = nullptr;
            throw std::invalid_argument( "Unable to open interface for capture" );
        }

        FutureList.push(
            std::shared_ptr<std::future<bool>>(new std::future<bool>(capPtr->CaptureLoop())));
        PcapList.push_back(capPtr);
    }

    Processor = new CPacketProcessor(*Queue, *Utility);
    FutureList.push(std::shared_ptr<std::future<bool>>(new std::future<bool>(Processor->Process())));
}

extern "C" const char* FetchLocalFrame()
{
    string* local;
    string* remote;
    Processor->GetFrames(local,remote);
    return local->c_str();
}

extern "C" const char* FetchRemoteFrame()
{
    string* local;
    string* remote;
    Processor->GetFrames(local,remote);
    return remote->c_str();
}

extern "C" const char* GetCurrentDate()
{
    return Processor->GetCurrentDate().c_str();
}

extern "C" void EndCapture()
{
    PacketQueue empty;
    std::swap( *Queue, empty );

    while(!PcapList.empty()) 
    {
        auto pcap = PcapList.back();
        PcapList.pop_back();
        pcap->Close();  
    }

    Processor->Stop();

    while(!FutureList.empty())
    {
        auto promise = FutureList.front();
        FutureList.pop();
        promise->get();
    }

    delete Processor;
    Processor = nullptr;
    delete Queue;
    Queue = nullptr;
    delete Utility;
    Utility = nullptr;
}

extern "C" int main(int, char**) 
{
    auto ifaces = "eth0"s;
    auto lanOnlyFilter = "not ( ( src net 0.0.0.0 or src net 10 or src net 192.168 or src net 172.16 or src net 172.17 ) and ( dst net 0.0.0.0 or dst net 10 or dst net 192.168 or dst net 172.16 or dst net 172.17 ) ) and not (multicast or ip multicast or ip6 multicast)"s;

    StartCapture(ifaces.c_str(),lanOnlyFilter.c_str(),"192.168.1|172.16|10", "",
    1,5,"/media/TMP-DSK/HOME/WhiteStat/WhiteStat/Common/RunConfig/WhiteStatLog.txt",
    "/media/TMP-DSK/HOME/WhiteStat/WhiteStat/Common/RunConfig/WhiteStatTrace.txt");

    for(int i = 1; i <= 10; ++i)
    {
        std::system("clear");

        std::cout << GetCurrentDate() << std::endl;
        std::cout << FetchLocalFrame() << std::endl << std::endl << FetchRemoteFrame();

        std::this_thread::sleep_for(10s);
    }


    EndCapture();     

    return 0;


    /*
    //128 bit integer to support IPV6 operations
    using namespace boost::multiprecision;
    int128_t v = 777;
    std::cout << "Big Integer Value:" << v << std::endl;    
    return 0;*/
}
