import multiprocessing.managers as MP
import pandas as pd
import threading
import time
import WhiteStat.Common.Utility as UTL

class RemoteServer(threading.Thread):

    def __init__(self):        
        self.startFlag = False
        super().__init__()
        self.remoteManager = RemoteManager()

    def start(self):       
        self.startFlag = True
        super().start()
        self.remoteManager.Serve()

    def run(self):       

        while(self.startFlag):
            time.sleep(5)

    def stop(self):
        self.remoteManager.Shutdown()
        self.startFlag = False
        super().join()

class RemoteManager(MP.SyncManager):
    def __init__(self):
        self.utl = UTL.Utility.getInstance()
        (ip,port) = self.utl.url.split(':')
        super().__init__(address=(ip, int(port)), authkey=b'whitestat')

    def Serve(self):
        RemoteManager.register("RemoteUsageFrame",  callable = RemoteUsageFrame.getInstance)
        self.start()

    def Shutdown(self):
        self.shutdown()


class RemoteUsageFrame:
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
        self._localIPs = {}
        self._remoteIPs = {}

    def GetFrame(self):
        return (self._localIPs, self._remoteIPs)

    def SetFrame(self, localIPs, remoteIPs):
        with self._lock:
            self._localIPs = localIPs;
            self._remoteIPs = remoteIPs;