
import Wrapper
import time

wrapper = Wrapper.Wrapper()

#clib.main.restype = ctypes.c_int
#clib.main.argtypes = [ctypes.c_int,ctypes.POINTER(ctypes.c_char_p)]
#result = clib.main(3,ctypes.POINTER(ctypes.c_char_p)())

iface = "eth0"
lanOnlyFilter = "not ( ( src net 0.0.0.0 or src net 10 or src net 192.168 or src net 172.16 or src net 172.17 ) and ( dst net 0.0.0.0 or dst net 10 or dst net 192.168 or dst net 172.16 or dst net 172.17 ) ) and not (multicast or ip multicast or ip6 multicast)"
ipv4mask = "192.168.1|172.16|10"
ipv6mask = ""
sleep = 1
refresh = 5
log="/media/TMP-DSK/HOME/WhiteStat/WhiteStat/Common/RunConfig/WhiteStatLog.txt"
trace="/media/TMP-DSK/HOME/WhiteStat/WhiteStat/Common/RunConfig/WhiteStatTrace.txt"

wrapper.StartCapture(iface,lanOnlyFilter,ipv4mask,ipv6mask,sleep,refresh,log,trace)

i = 1;
while i <= 5:
    curDate, localFrame, remoteFrame = wrapper.GetFrames()
    time.sleep(5)
    i+=1
    print(curDate)
    print(localFrame)
    print(remoteFrame)   
    

wrapper.StopCapture()
