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
        StringArray _interfaces;
        string _pcapFilter;
        string _logFile;
        string _traceFile;

    private:
        void AppendToFile(string fileName, string line);

    public:
        CUtility(string interfaces, string pcapFilter,
        string lanV4Segs, string lanV6Segs, 
        int sleepSeconds, int refreshSeconds,
        string logFile, string traceFile);

        void Log(string message, bool isTrace = false);
        bool IsLANIP(string ip);
        int SleepSeconds();
        int RemoteRefreshSeconds();
        StringArray& GetInterfaces();
        string& GetPcapFilter();
};

void CUtility::AppendToFile(string fileName, string line)
{
    try
    {
        std::cout << line << std::endl;

        std::ofstream file;
        file.open(fileName, std::ios::out | std::ios::app);
        if (file.fail())
            throw std::ios_base::failure(std::strerror(errno));

        file.exceptions(file.exceptions() | std::ios::failbit | std::ifstream::badbit);

        file << line << std::endl;

        file.close();
    }
    catch(const std::exception& e)
    {
        std::cout << line << std::endl;
        std::cerr << e.what() << std::endl;
    } 
}

void CUtility::Log(string message, bool isTrace)
{
    auto currentTime = boost::posix_time::second_clock::local_time();
    auto time = to_tm(currentTime);
    std::stringstream stream;
    stream << std::put_time(&time,"%d-%m-%Y %H:%M:%S") << " " << message;

    AppendToFile(isTrace ? _traceFile : _logFile, stream.str());
}

StringArray& CUtility::GetInterfaces()
{
    return _interfaces;
}

string& CUtility::GetPcapFilter()
{
    return _pcapFilter;
}

int CUtility::SleepSeconds()
{
    return _sleepSeconds;
}

int CUtility::RemoteRefreshSeconds()
{
    return _refreshSeconds;
}

CUtility::CUtility(
        string interfaces, string pcapFilter,
        string lanV4Segs, string lanV6Segs, 
        int sleepSeconds, int refreshSeconds,
        string logFile, string traceFile):
_sleepSeconds(sleepSeconds), _refreshSeconds(refreshSeconds),
_pcapFilter(pcapFilter),
_logFile(logFile), _traceFile(traceFile)
{    
    boost::algorithm::split(_lanSegs, lanV4Segs + lanV6Segs, boost::is_any_of("|"));
    boost::algorithm::split(_interfaces, interfaces, boost::is_any_of("|"));
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