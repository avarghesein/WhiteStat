#ifndef INC_CPacketProcessor
#define INC_CPacketProcessor

#include "./Include.hpp"
#include "./Packet.cpp"
#include "./Frame.cpp"
#include "./CUtility.cpp"

using std::string;
using PacketQueue = std::queue<std::shared_ptr<HashedPacket>>;

using BytesIntHash = boost::bimap<BYTES,ushort>;
using IntStrHash = boost::container::map<ushort,string>;
using IntBoolHash = boost::container::map<ushort,bool>;

using FrameMap = boost::container::map<ushort,std::shared_ptr<Frame>>;

class CPacketProcessor
{
    private:
        CUtility& _utility;
        PacketQueue& _queue;
        FrameMap  _localIPMap;
        FrameMap  _remoteIPMap;

        std::mutex _mutex; 
        string _serializedLocalIPs;
        string _serializedRemoteIPs;
        string _serializedLocalIPsCopy;
        string _serializedRemoteIPsCopy;
        bool _printInReadableFormat;

        ushort _bytesIntHashIdx;
        BytesIntHash _bytesIntHash;
        IntBoolHash _ipLanHash;
        IntStrHash _intStrHash;

        bool _isStop;

        boost::gregorian::date _today;
        string _todayDateString;

    private:
        static string AddressToString(BYTES& bytes);
        static char* ConvertToMACString(const struct ether_addr *addr, char *buf);
        ushort GetBytesIntHash(BYTES& value);
        bool IsLANIP(ushort ipHash);
        bool ProcessFrame(ushort mac, ushort ip, u_long size, bool isSource , bool isLan);
        bool SerializeFrames();        

    public:
        void SetPrintableFormat(bool isEnable  = true);
        bool GetFrames(string*& localIPs, string*& remoteIps);
        std::shared_ptr<HashedPacket> HashPacket(Packet& packet);
        string& GetCurrentDate();
        CPacketProcessor(PacketQueue& queue, CUtility& utility);
        std::future<bool> Process();
        bool Stop();
};

void CPacketProcessor::SetPrintableFormat(bool isEnable)
{
    _printInReadableFormat = isEnable;
}

string& CPacketProcessor::GetCurrentDate()
{  
    std::ostringstream is;
    auto df = new boost::gregorian::date_facet("%Y-%m-%d");
    is.imbue(std::locale(is.getloc(), df));

    {
        const std::lock_guard<std::mutex> lock(_mutex);
        is << _today;
    }

    _todayDateString = is.str();
    return _todayDateString;
}

bool CPacketProcessor::GetFrames(string*& localIPs, string*& remoteIps)
{
    {
        const std::lock_guard<std::mutex> lock(_mutex);
        _serializedLocalIPsCopy = _serializedLocalIPs;
        _serializedRemoteIPsCopy = _serializedRemoteIPs;
    }

    localIPs = &_serializedLocalIPsCopy;
    remoteIps = &_serializedRemoteIPsCopy;

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

            auto mac = isLocalIPs ? framePtr.first: frame.MAC;
            auto ip = isLocalIPs ? frame.IP : framePtr.first;

            auto lambdaBytesToStr = [](BYTES& bytes)
            {
                std::ostringstream ss;
                ss << std::hex << /*std::uppercase << */std::setfill( '0' );
                std::for_each( bytes.cbegin(), bytes.cend(), [&]( int c ) { ss << std::setw( 2 ) << c; } );
                return ss.str();
            };

            auto lambdaBytesToReadableStr = [](BYTES& bytes)
            {
                return CPacketProcessor::AddressToString(bytes);
            };

            auto lambdaStr = _printInReadableFormat ? lambdaBytesToReadableStr : lambdaBytesToStr;

            string macStr;
            string ipStr;

            if(_intStrHash.contains(mac))
            {
                macStr = _intStrHash[mac];
            }
            else
            {
                auto macBytes = (_bytesIntHash.right.find(mac)->second);

                macStr = lambdaStr(macBytes);
                _intStrHash[mac] = macStr;
            }

            if(_intStrHash.contains(ip))
            {
                ipStr = _intStrHash[ip];
            }
            else
            {
                auto ipBytes = (_bytesIntHash.right.find(ip)->second);
                ipStr = lambdaStr(ipBytes);
                _intStrHash[ip] = ipStr;
            }

            auto in = frame.In;
            auto out = frame.Out;

            using boost::format;

            if(isLocalIPs)
            {
                auto formatter = boost::format("%1%|%2%|%3%|%4%|%5%") 
                % macStr %ipStr % in % out % frame.GetCurrentTime();                  
                stream << formatter << std::endl;
            }
            else
            {
                auto formatter = boost::format("%2%|%1%|%3%|%4%|%5%") 
                % macStr %ipStr % in % out % frame.GetCurrentTime();                  
                stream << formatter << std::endl;                
            }
        }

        return stream.str();          
    };

    {
        const std::lock_guard<std::mutex> lock(_mutex);
        _serializedLocalIPs = serializeLambda(_localIPMap, true);
        _serializedRemoteIPs = serializeLambda(_remoteIPMap, false);
    }

    return true;  
}

bool CPacketProcessor::ProcessFrame(ushort mac, ushort ip, u_long size, bool isSource, bool isLan )
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

    if(isLan)
    {
        (*frame).IP = ip;
    }
    else
    {
        (*frame).MAC = mac;
    }

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

bool CPacketProcessor::IsLANIP(ushort ipHash)
{
    if(_ipLanHash.contains(ipHash)) return _ipLanHash[ipHash];

    auto ip = (_bytesIntHash.right.find(ipHash)->second);
    bool isLan = _utility.IsLANIP(ip);
    _ipLanHash[ipHash] = isLan;
    return isLan;
}

ushort CPacketProcessor::GetBytesIntHash(BYTES& value)
{
    auto itr = _bytesIntHash.left.find(value);
    if(itr != _bytesIntHash.left.end())
    {
        return itr->second;
    }

    ++_bytesIntHashIdx;
    _bytesIntHash.insert({value, _bytesIntHashIdx});
    return _bytesIntHashIdx;
}

CPacketProcessor::CPacketProcessor(PacketQueue& queue,CUtility& utility) : _queue(queue),
 _isStop(false), _bytesIntHashIdx(0), _utility(utility),
 _today(boost::gregorian::day_clock::local_day()),
 _printInReadableFormat(false) {}

bool CPacketProcessor::Stop()
{    
    _isStop = true;
    return true;
}

std::shared_ptr<HashedPacket> CPacketProcessor::HashPacket(Packet& packet)
{
    if(packet.sourceIP.empty() || packet.destIP.empty())
    {
        nullptr;
    }

    return std::shared_ptr<HashedPacket>( new HashedPacket { 
        .sourceIP = GetBytesIntHash(packet.sourceIP),
        .destIP = GetBytesIntHash(packet.destIP),
        .sourceMAC = GetBytesIntHash(packet.sourceMAC),
        .destMAC = GetBytesIntHash(packet.destMAC),
        .dataSize = packet.dataSize 
    });
}

std::future<bool> CPacketProcessor::Process()
{
    using namespace std::chrono_literals;

    auto looper = [&]()->bool {

        ushort sleptSeconds = 0;
        ushort sleepSeconds = _utility.SleepSeconds();
        ushort refreshSeconds = _utility.RemoteRefreshSeconds();
        
        while(!_isStop)
        {
            ushort packetCount = 0;

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

                        {
                            const std::lock_guard<std::mutex> lock(_mutex);
                            _today = curDate;
                        }
                    }

                    sleptSeconds = 0;
                }

                auto val = _queue.front();
                _queue.pop();

                HashedPacket& packet = *val;

                int srcMacHash = packet.sourceMAC;                
                int srcIpHash = packet.sourceIP;
                bool isSrcLan = IsLANIP(packet.sourceIP);

                int dstMacHash = packet.destMAC;                
                int dstIpHash = packet.destIP;
                bool isDstLan = IsLANIP(packet.destIP);

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

string CPacketProcessor::AddressToString(BYTES& bytes)
{
    char address[INET6_ADDRSTRLEN];
    BYTE* pAddress = bytes.data();

    switch (bytes.size())
    {
        case 4:
            inet_ntop(AF_INET, pAddress, address, INET_ADDRSTRLEN);
            break;

        case 6:
            //snprintf(_sourceMAC, 20, "%s", ether_ntoa((struct ether_addr *)eHeader->ether_shost));
            ConvertToMACString((const struct ether_addr *)pAddress, address);
            break;

        case 16:
            inet_ntop(AF_INET6, pAddress, address, INET6_ADDRSTRLEN);
            break;

        default:
            break;
    }

    return address;
}

char* CPacketProcessor::ConvertToMACString(const struct ether_addr *addr, char *buf)
{
    sprintf(buf, "%02x:%02x:%02x:%02x:%02x:%02x",
            addr->ether_addr_octet[0], addr->ether_addr_octet[1],
            addr->ether_addr_octet[2], addr->ether_addr_octet[3],
            addr->ether_addr_octet[4], addr->ether_addr_octet[5]);
    return buf;
}

#endif