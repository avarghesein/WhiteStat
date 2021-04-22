#ifndef INC_CPacketProcessor
#define INC_CPacketProcessor

#include "./Include.hpp"
#include "./Packet.cpp"
#include "./Frame.cpp"
#include "./CUtility.cpp"

using std::string;
using IntBoolHash = boost::container::map<int,bool>;
using PacketQueue = std::queue<std::shared_ptr<Packet>>;
using IntHash = boost::container::map<std::string,int>;
using IntStringHash = boost::container::map<int,std::string>;
using FrameMap = boost::container::map<int,std::shared_ptr<Frame>>;

class CPacketProcessor
{
    private:
        CUtility& _utility;
        PacketQueue& _queue;
        FrameMap  _localIPMap;
        FrameMap  _remoteIPMap;
        string _serializedLocalIPs;
        string _serializedRemoteIPs;

        int _intHashIdx;
        IntHash _intHash;
        IntStringHash _intStrHash;
        IntBoolHash _ipLanHash;

        bool _isStop;

        boost::gregorian::date _today;

    private:
        int GetIntHash(string value);
        bool IsLANIP(string ip);
        bool ProcessFrame(int mac, int ip, u_long size, bool isSource , bool isLan);
        bool SerializeFrames();        

    public:
        bool GetFrames(string& localIPs, string& remoteIps);
        CPacketProcessor(PacketQueue& queue, CUtility& utility);
        std::future<bool> Process();
        bool Stop();
};

bool CPacketProcessor::GetFrames(string& localIPs, string& remoteIps)
{
    localIPs = _serializedLocalIPs;
    remoteIps = _serializedRemoteIPs;
    return true;
}

bool CPacketProcessor::SerializeFrames()
{
    auto serializeLambda = [&](FrameMap map, bool isLocalIPs)->string
    {
        std::stringstream stream;

        for(auto framePtr: map)
        {
            Frame& frame = *(framePtr.second);
            auto mac = _intStrHash[frame.MAC];
            auto ip = _intStrHash[frame.IP];
            auto in = frame.In;
            auto out = frame.Out;

            using boost::format;

            if(isLocalIPs)
            {
                auto formatter = boost::format("%1%|%2%|%3%|%4%|%5%") 
                % mac %ip % in % out % frame.GetCurrentTime();                  
                stream << formatter << std::endl;
            }
            else
            {
                auto formatter = boost::format("%2%|%1%|%3%|%4%|%5%") 
                % mac %ip % in % out % frame.GetCurrentTime();                  
                stream << formatter << std::endl;                
            }
        }

        return stream.str();          
    };

    _serializedLocalIPs = serializeLambda(_localIPMap, true);
    _serializedRemoteIPs = serializeLambda(_remoteIPMap, false);

    return true;  
}

bool CPacketProcessor::ProcessFrame(int mac, int ip, u_long size, bool isSource, bool isLan )
{
    FrameMap* mapPtr = nullptr;    
    int key = 0;

    if(isLan)
    {
        mapPtr = &_localIPMap;   
        key = mac; 
    }
    else
    {
        mapPtr = &_remoteIPMap;
        key = ip;
    }

    FrameMap& map = *mapPtr;  

    if(!map.contains(key))
    {
        map[key] = std::shared_ptr<Frame>(new Frame(ip,mac,0,0));
    }

    std::shared_ptr<Frame>& frame = map[key];

    if(isSource)
    {
        (*frame).Out += size;
    }
    else
    {
        (*frame).In += size;
    }

    (*frame).SetCurrentDateTime();

    return true;
}

bool CPacketProcessor::IsLANIP(string ip)
{
    int ipHash = GetIntHash(ip);
    if(_ipLanHash.contains(ipHash)) return _ipLanHash[ipHash];

    bool isLan = _utility.IsLANIP(ip);
    _ipLanHash[ipHash] = isLan;
    return isLan;
}

int CPacketProcessor::GetIntHash(string value)
{
    if(_intHash.contains(value)) return _intHash[value];
    ++_intHashIdx;
    _intHash[value] = _intHashIdx;
    _intStrHash[_intHashIdx] = value;
    return _intHashIdx;
}

CPacketProcessor::CPacketProcessor(PacketQueue& queue,CUtility& utility) : _queue(queue),
 _isStop(false), _intHashIdx(-1), _utility(utility),
 _today(boost::gregorian::day_clock::local_day()) {}

bool CPacketProcessor::Stop()
{
    _isStop = true;
    return true;
}

std::future<bool> CPacketProcessor::Process()
{
    using namespace std::chrono_literals;

    auto looper = [&]()->bool {

        int sleptSeconds = 0;
        int sleepSeconds = _utility.SleepSeconds();
        int refreshSeconds = _utility.RemoteRefreshSeconds();
        
        while(!_isStop)
        {
            int packetCount = 0;

            while(!_isStop && !_queue.empty() && ++packetCount <= 2000)
            {
                if(sleptSeconds >= refreshSeconds)
                {
                    SerializeFrames();                    

                    auto curDate(boost::gregorian::day_clock::local_day());
                    
                    if(curDate > _today)
                    {
                        _localIPMap.clear();
                        _remoteIPMap.clear();
                        _today = curDate;
                    }

                    sleptSeconds = 0;
                }

                auto val = _queue.front();
                _queue.pop();

                Packet& packet = *val;

                if(packet.sourceIP == "" || packet.destIP == "")
                {
                    continue;
                }

                int srcMacHash = GetIntHash(packet.sourceMAC);
                bool isSrcLan = IsLANIP(packet.sourceIP);
                int srcIpHash = GetIntHash(packet.sourceIP);
                int dstMacHash = GetIntHash(packet.destMAC);
                bool isDstLan = IsLANIP(packet.destIP);
                int dstIpHash = GetIntHash(packet.destIP);

                ProcessFrame(srcMacHash,srcIpHash,val->dataSize,true,isSrcLan);
                ProcessFrame(dstMacHash,dstIpHash,val->dataSize,false,isDstLan); 
            }

            //std::this_thread::sleep_for(1s);
            std::this_thread::sleep_for(std::chrono::seconds(sleepSeconds));
            sleptSeconds += sleepSeconds;
        }

        return true;
    };

    std::future<bool> loopFun = std::async(std::launch::async,looper);

    return loopFun;
}

#endif