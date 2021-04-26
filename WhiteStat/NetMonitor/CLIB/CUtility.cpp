#ifndef INC_CUtility
#define INC_CUtility

#include "./Include.hpp"
#include "./Packet.cpp"
#include "./Frame.cpp"

struct Packet;

using std::string;
using BytesArray = std::vector<BYTES>;
using StringArray = std::vector<string>;
using BytesBoolHash = boost::container::map<BYTES,bool>;
using PacketQueue = std::queue<std::shared_ptr<Packet>>;
using FrameMap = boost::container::map<int,std::shared_ptr<Frame>>;

class CUtility
{
    private:
        BytesArray _lanSegs;
        BytesBoolHash _ipLanHash;
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
        bool IsLANIP(BYTES& ip);
        int SleepSeconds();
        int RemoteRefreshSeconds();
        StringArray& GetInterfaces();
        string& GetPcapFilter();

        static void Copy(BYTE*& array, int len, BYTES& vector);
};

void CUtility::Copy(BYTE*& array, int len, BYTES& vector)
{
    for(int idx = 0; idx < len; ++idx)
        vector.push_back(array[idx]);
}

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
    boost::algorithm::split(_interfaces, interfaces, boost::is_any_of("|"));

    auto lambdaParseLanSegs = [&](string lanSeg, int isV4)
    {
        if(lanSeg != "")
        {
            std::vector<string> lanSegs;
            boost::algorithm::split(lanSegs, lanSeg, boost::is_any_of("|")); 

            for(auto seg : lanSegs)
            {
                if(!isV4)
                {
                    string v6Seg;

                    for(int i=0; i < seg.size(); i+=2)
                    {
                        v6Seg += seg.substr(i,i+2) + ":";
                    }

                    seg = v6Seg.substr(0,v6Seg.size()-1);
                }
                
                BYTES bytes;
                std::vector<string> octets;
                boost::algorithm::split(octets, seg, boost::is_any_of(isV4 ? "." : ":"));

                for(auto byte: octets)
                {
                    if(isV4)
                    {
                        bytes.push_back((BYTE)std::stoul(byte));
                    }
                    else
                    {
                        std::stringstream ss;
                        uint8_t x;
                        unsigned tmp;
                        ss << byte;
                        ss >> std::hex >> tmp; 
                        x = tmp; 
                        bytes.push_back(x);
                    }                    
                }

                _lanSegs.push_back(bytes);
            }
        }
    };

    lambdaParseLanSegs(lanV4Segs,true);
    lambdaParseLanSegs(lanV6Segs,false);
}


bool CUtility::IsLANIP(BYTES& ip)
{
    if(_ipLanHash.contains(ip)) return _ipLanHash[ip];

    bool isLan = false;

    for(auto lanSeg: _lanSegs)
    {
        /*if (ip.rfind(lanSeg, 0) == 0) 
        {
            isLan = true;
            break;
        }*/

        if(lanSeg.size() <= ip.size())
        {
            if(BYTES(ip.cbegin(),ip.cbegin() + lanSeg.size()) == lanSeg)
            {
                isLan = true;
                break;
            }
        }
    }    

    _ipLanHash[ip] = isLan;

    return isLan;
}

#endif