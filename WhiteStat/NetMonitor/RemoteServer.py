from multiprocessing.connection import Listener
from multiprocessing.connection import Client
import pickle
import threading
import time
import WhiteStat.Common.Utility as UTL
import socket

class RemoteServer(threading.Thread):
    __slots__ = ['startFlag','remoteManager']

    def __init__(self):        
        self.startFlag = False
        super().__init__()
        self.remoteManager = RemoteManager()

    def start(self):       
        self.startFlag = True
        super().start()
        
    def run(self): 
        while(self.startFlag):
            try:
                self.remoteManager.Serve()
            finally:
                pass

    def stop(self):
        self.remoteManager.Shutdown()
        self.startFlag = False
        super().join()

class RemoteManager(object):
    __slots__ = ['utl','address', 'listener']

    def __init__(self):
        self.utl = UTL.Utility.getInstance()
        (ip,port) = self.utl.url.split(':')
        self.address = (ip, int(port))
        self.listener = None        

    def Serve(self):

        if self.listener is None:
            self.listener = Listener(self.address, authkey=b'whitestat')

        with self.listener.accept() as client:

            frame = RemoteUsageFrame.getInstance().GetFrame()
            bytesTosend = pickle.dumps(frame)
            client.send_bytes(bytesTosend)
            closureBytes = client.recv_bytes()
            client.close()

            del closureBytes
            del client
            del bytesTosend
            del frame

    def Shutdown(self):
        pass
    
    def FetchFrame(self):
        with Client(self.address, authkey=b'whitestat') as client:

            bytesRecvd = client.recv_bytes()
            closureBytes = bytearray.fromhex('ff')
            client.send_bytes(closureBytes)
            client.close()
            frame = pickle.loads(bytesRecvd)

            del closureBytes
            del client
            del bytesRecvd

            return frame

class RemoteUsageFrame(object):
    __slots__ = ['__weakref__', '_lock','_localIPs','_remoteIPs']

    __instance = None

    @staticmethod 
    def getInstance():
        """ Static access method. """
        if RemoteUsageFrame.__instance == None:
            RemoteUsageFrame()
        return RemoteUsageFrame.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if RemoteUsageFrame.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            RemoteUsageFrame.__instance = self

        self._lock = threading.Lock()
        self._localIPs = None
        self._remoteIPs = None

    def GetFrame(self):
        return (self._localIPs, self._remoteIPs)

    def SetFrame(self, localIPs, remoteIPs):
        with self._lock:
            del self._localIPs
            del self._remoteIPs
            self._localIPs = localIPs;
            self._remoteIPs = remoteIPs;