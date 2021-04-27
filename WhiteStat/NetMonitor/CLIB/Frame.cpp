#ifndef INC_Frame
#define INC_Frame

#include "./Include.hpp"

using std::string;

struct Frame
{
    ushort IP;
    ushort MAC;
    ulong In;
    ulong Out;
    boost::posix_time::ptime lastSeen;

    Frame(ushort ip, ushort mac, ulong in, ulong out);
    void SetCurrentDateTime();
    string GetCurrentTime();

    ~Frame() {}
    
};

Frame::Frame(ushort ip, ushort mac, ulong in, ulong out):
IP(ip), MAC(mac),
In(in), Out(out)
{
}

void Frame::SetCurrentDateTime()
{
    lastSeen = boost::posix_time::second_clock::local_time();
}

string Frame::GetCurrentTime()
{
    auto time = to_tm(lastSeen);
    std::stringstream stream;
    //stream << std::put_time(&time,"%d-%m-%Y %H:%M:%S");
    stream << std::put_time(&time,"%H:%M:%S");
    return stream.str();
}



#endif
