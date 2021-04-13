#ifndef INC_Frame
#define INC_Frame

#include "./Include.hpp"

using std::string;

struct Frame
{
    string IP;
    string MAC;
    int In;
    int Out;
    boost::posix_time::ptime lastSeen;

    Frame(string ip, string mac, int in, int out);
    void SetCurrentDateTime();

    ~Frame() {}
    
};

Frame::Frame(string ip, string mac, int in, int out):
IP(ip), MAC(mac),
In(in), Out(out)
{
}

void Frame::SetCurrentDateTime()
{
    lastSeen = boost::posix_time::second_clock::local_time();
}



#endif
