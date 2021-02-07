import datetime
import time
import os
import threading, queue
import pandas as pd
import WhiteStat.Common.Utility as UTL
import WhiteStat.NetMonitor.RemoteServer as RS

class Dispatcher(threading.Thread):

    def __init__(self, dispatcherQueue):
        
        self.dispatcherQueue = dispatcherQueue
        self.startFlag = False
        super().__init__()

        self.utl = UTL.Utility.getInstance()

        self.remoteServer = RS.RemoteServer()
        self.remoteManager = RS.RemoteManager()

        self.dataFrame = pd.DataFrame(None, columns = [
                "IP",
                "MAC",
                "In",
                "Out",
                "LastSeen"]) 
    

    def start(self):
        self.startFlag = True
        super().start()
        self.remoteServer.start()        

    def run(self):

        sleepSeconds = 1
        remoteRefreshSeconds = 10
        sleptSeconds = 0

        while(self.startFlag):

            while((not self.dispatcherQueue.empty()) and self.startFlag):

                packet = None

                try:
                    packet = (srcMac,srcIP,srcPort, dstMac,dstIP, dstPort,sizeInBytes,protocol) = self.dispatcherQueue.get_nowait()
                    self.dispatcherQueue.task_done()

                except queue.Empty:
                    break

                lastSeen = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                frame = self.dataFrame
                self.PopulateFrame(frame,srcMac,srcIP,sizeInBytes,lastSeen,True)
                self.PopulateFrame(frame,dstMac,dstIP,sizeInBytes,lastSeen,False)               
                packet = None

                if sleptSeconds >= remoteRefreshSeconds:
                    self.remoteManager.connect()
                    curFrame = self.remoteManager.RemoteUsageFrame()
                    curFrame.SetFrame(frame)
                    sleptSeconds = 0

                    curFrame = self.remoteManager.RemoteUsageFrame()
                    remoteFrame = curFrame.GetFrame()
                   
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print(remoteFrame)

            time.sleep(sleepSeconds)
            sleptSeconds += sleepSeconds

    def PrintFrame(self, frame):
        pass

    def PopulateFrame(self, frame, mac,ip,sizeInBytes,lastSeen, isSource = True):

        index = -1

        if self.utl.IsLANIPBytes(ip):
            if (frame.MAC == mac).any():
                index = frame[frame.MAC == mac].index.tolist()[0]
                frame.at[index,'IP'] = ip                
                frame.at[index,'LastSeen'] = lastSeen
            else:
                frame.loc[len(frame.index)] = [ip,mac,0,0,lastSeen]
                index = len(frame.index) - 1
        else:
            if (frame.IP == ip).any():
                index = frame[frame.IP == ip].index.tolist()[0]
                frame.at[index,'MAC'] = mac
                frame.at[index,'LastSeen'] = lastSeen
            else:
                frame.loc[len(frame.index)] = [ip,mac,0,0,lastSeen]
                index = len(frame.index) - 1


        if isSource:
            frame.at[index,'Out'] += sizeInBytes
        else:
            frame.at[index,'In'] += sizeInBytes

    def stop(self):
        self.remoteServer.stop()
        self.startFlag = False
        super().join()        