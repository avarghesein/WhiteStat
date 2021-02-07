import multiprocessing.managers as MP
import pandas as pd
import threading
import time

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
        super().__init__(address=('', 888), authkey=b'whitestat')

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
        self._dataFrame = pd.DataFrame(None, columns = [
                "IP",
                "MAC",
                "In",
                "Out",
                "LastSeen"]) 
    
    @property
    def CurrentFrame(self):
        return self._dataFrame

    @CurrentFrame.setter
    def CurrentFrame(self, value):
        self._dataFrame = value

    @CurrentFrame.deleter
    def CurrentFrame(self):
        del self._dataFrame

    def GetFrame(self):
        return self._dataFrame

    def SetFrame(self, frame):
        with self._lock:
            # Extract column names into a list
            cols = [col for col in self._dataFrame.columns]
            # Create empty DataFrame with those column names
            newFrame = pd.DataFrame(columns=cols).append(frame)
            self._dataFrame = newFrame