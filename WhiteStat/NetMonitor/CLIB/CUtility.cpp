#ifndef INC_CUtility
#define INC_CUtility

#include "./Include.hpp"
#include "./Packet.cpp"
#include "./Frame.cpp"

using std::string;
using StringArray = std::vector<std::string>;
using StringBoolHash = boost::container::map<std::string,bool>;
using PacketQueue = std::queue<std::shared_ptr<Packet>>;
using IntHash = boost::container::map<std::string,int>;
using FrameMap = boost::container::map<int,std::shared_ptr<Frame>>;

class CUtility
{
    private:
        StringArray _lanSegs;
        StringBoolHash _ipLanHash;
        int _sleepSeconds;
        int _refreshSeconds;

    private:

    public:
        CUtility(string lanV4Segs, string lanV6Segs, int sleepSeconds, int refreshSeconds);
        bool IsLANIP(string ip);
        int SleepSeconds();
        int RemoteRefreshSeconds();
};

int CUtility::SleepSeconds()
{
    return _sleepSeconds;
}

int CUtility::RemoteRefreshSeconds()
{
    return _refreshSeconds;
}

CUtility::CUtility(string lanV4Segs, string lanV6Segs, int sleepSeconds, int refreshSeconds):
_sleepSeconds(sleepSeconds), _refreshSeconds(refreshSeconds)
{    
    boost::algorithm::split(_lanSegs, lanV4Segs + lanV6Segs, boost::is_any_of("|"));
}

bool CUtility::IsLANIP(string ip)
{
    if(_ipLanHash.contains(ip)) return _ipLanHash[ip];

    bool isLan = false;

    for(auto lanSeg: _lanSegs)
    {
        if (ip.rfind(lanSeg, 0) == 0) 
        {
            isLan = true;
            break;
        }
    }
    
    _ipLanHash[ip] = isLan;

    return isLan;
}

#endif