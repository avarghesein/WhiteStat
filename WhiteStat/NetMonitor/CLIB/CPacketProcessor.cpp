#ifndef INC_CPacketProcessor
#define INC_CPacketProcessor

#include "./Include.hpp"
#include "./Packet.cpp"
#include "./Frame.cpp"

using std::string;
using PacketQueue = std::queue<std::shared_ptr<Packet>>;
using PacketMap = boost::container::map<std::string,std::shared_ptr<Packet>>;

class CPacketProcessor
{
    private:
        PacketQueue& _queue;
        PacketMap _map;
        bool _isStop;

    private:


    public:
        CPacketProcessor(PacketQueue& queue);
        std::future<bool> Process();
        bool Stop();
};


CPacketProcessor::CPacketProcessor(PacketQueue& queue) : _queue(queue), _isStop(false) {}

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

                using boost::format;
                auto formatter = boost::format("IP %1%,  MAC=%2% , DATA=%3%") % val->sourceIP % 
                val->sourceMAC % val->dataSize;

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