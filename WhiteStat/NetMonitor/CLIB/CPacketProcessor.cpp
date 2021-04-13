#ifndef INC_CPacketProcessor
#define INC_CPacketProcessor

#include "./Include.hpp"
#include "./Packet.cpp"
#include "./Frame.cpp"

using std::string;
using PacketQueue = std::queue<std::shared_ptr<Packet>>;
using IntHash = boost::container::map<std::string,int>;
using FrameMap = boost::container::map<int,std::shared_ptr<Frame>>;

class CPacketProcessor
{
    private:
        PacketQueue& _queue;
        FrameMap  _localIPMap;
        FrameMap  _remoteIPMap;

        int _intHashIdx;
        IntHash _intHash;

        bool _isStop;

    private:
        int GetIntHash(string value);


    public:
        CPacketProcessor(PacketQueue& queue);
        std::future<bool> Process();
        bool Stop();
};

int CPacketProcessor::GetIntHash(string value)
{
    if(_intHash.contains(value)) return _intHash[value];
    ++_intHashIdx;
    _intHash[value] = _intHashIdx;
    return _intHashIdx;
}

CPacketProcessor::CPacketProcessor(PacketQueue& queue) : _queue(queue), _isStop(false),
_intHashIdx(-1) {}

bool CPacketProcessor::Stop()
{
    _isStop = true;
    return true;
}

std::future<bool> CPacketProcessor::Process()
{
    using namespace std::chrono_literals;

    auto looper = [&]()->bool {
        while(!_isStop)
        {
            if(!_queue.empty())
            {
                auto val = _queue.front();
                _queue.pop();

                Packet& packet = *val;

                int srcMacHash = GetIntHash(packet.sourceMAC);
                int srcIpHash = GetIntHash(packet.sourceIP);
                int dstMacHash = GetIntHash(packet.destMAC);
                int dstIpHash = GetIntHash(packet.destIP);

                _localIPMap[srcMacHash] = std::shared_ptr<Frame>(new Frame(srcIpHash,srcMacHash,val->dataSize,0));

                using boost::format;
                auto formatter = boost::format("IP %1%,  MAC=%2% , DATA=%3%") % val->sourceIP % 
                val->sourceMAC % _localIPMap[srcMacHash]->In;

                std::cout << formatter << std::endl;

                std::this_thread::sleep_for(1s);
            }
        }
        return true;
    };

    std::future<bool> loopFun = std::async(std::launch::async,looper);

    return loopFun;
    //Modern C++ high performance Dictionary
    // boost::container::map<std::string,std::string> dict;
    // dict["program"] = "Modern C++";
    // dict["program"] = "Modern C++ Program";

    // std::cout <<"KeyValue:"<< dict["program"] << std::endl;
    
 
}

#endif