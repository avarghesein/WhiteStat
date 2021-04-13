#ifndef INC_Frame
#define INC_Frame

#include "./Include.hpp"

using std::string;

struct Frame
{
    int IP;
    int MAC;
    int In;
    int Out;
    boost::posix_time::ptime lastSeen;

    Frame(int ip, int mac, int in, int out);
    void SetCurrentDateTime();

    ~Frame() {}
    
};

Frame::Frame(int ip, int mac, int in, int out):
IP(ip), MAC(mac),
In(in), Out(out)
{
}

void Frame::SetCurrentDateTime()
{
    lastSeen = boost::posix_time::second_clock::local_time();
}



#endif
