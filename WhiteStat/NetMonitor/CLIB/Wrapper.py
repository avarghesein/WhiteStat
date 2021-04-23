import ctypes

class Wrapper:
    def __init__(self):
        self._libPath = "./WhiteStat/NetMonitor/CLIB/build/libWhiteStat.so"
        self._clib = ctypes.CDLL(self._libPath)

        CHAR_P = ctypes.c_char_p
        INT = ctypes.c_int

        self._clib.StartCapture.argtypes = [CHAR_P, CHAR_P,CHAR_P,CHAR_P,INT,INT,CHAR_P,CHAR_P]
        self._clib.FetchLocalFrame.restype = CHAR_P
        self._clib.FetchRemoteFrame.restype = CHAR_P
        self._clib.GetCurrentDate.restype = CHAR_P
    
    def StartCapture(self,iface,lanOnlyFilter,ipv4mask,ipv6mask,sleep,refresh,log,trace):
        self._clib.StartCapture(iface.encode('utf-8'),lanOnlyFilter.encode('utf-8'),
        ipv4mask.encode('utf-8'),ipv6mask.encode('utf-8'),sleep,refresh,
        log.encode('utf-8'),trace.encode('utf-8'))        
    
    def GetFrames(self):
        localFrame = self._clib.FetchLocalFrame().decode('UTF-8')
        remoteFrame = self._clib.FetchRemoteFrame().decode('UTF-8')
        curDate = self._clib.GetCurrentDate().decode('UTF-8')
        return (curDate,localFrame,remoteFrame)
    
    def StopCapture(self):
        self._clib.EndCapture()

