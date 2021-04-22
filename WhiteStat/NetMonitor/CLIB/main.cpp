#include "./Include.hpp"
#include "./Packet.cpp"
#include "CPcap.cpp"
#include "CPacketProcessor.cpp"


using std::string;
using PacketQueue = std::queue<std::shared_ptr<Packet>>;
using boost::container::deque;

int main(int, char**) {

    using namespace std::string_literals;
    using namespace std::chrono_literals;

    CUtility c("eth0"s,"","192.168.1|172.16|10", "",1, 5);

    // pcap_if_t *ifs = nullptr;
    // pcap_findalldevs(&ifs,nullptr);
    // std::cout << ifs[0].name << std::endl;
    // pcap_freealldevs(ifs);   

    PacketQueue queue; 

    CPacketProcessor processor(queue,c);

    auto iface = "eth0"s;
    CPcap cap(iface, queue);
    cap.Open();
    auto futureVal = cap.CaptureLoop();

    auto procFutureVal = processor.Process();

    for(int i = 1; i <= 10; ++i)
    {
        std::system("clear");

        string local;
        string remote;
        processor.GetFrames(local,remote);
        std::cout << local << std::endl << std::endl << remote;

        std::this_thread::sleep_for(10s);
    }


    cap.Close();    
    auto val = futureVal.get(); 

    processor.Stop();  
    auto val1 = procFutureVal.get();     

    return 0;


    /*std::vector<std::string> vect { "First", "Modern", "C++", "APP"};

    for(auto token : vect)
    {
        std::cout << token << " ";
    }
    std::cout << std::endl;
    std::cout << std::endl;

    //128 bit integer to support IPV6 operations
    using namespace boost::multiprecision;
    int128_t v = 777;
    std::cout << "Big Integer Value:" << v << std::endl;
    
    return 0;*/
}
