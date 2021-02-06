import datetime
import time
import os
import threading, queue
import pandas as pd
import WhiteStat.Common.Utility as UTL
from multiprocessing.managers import BaseManager


class Dispatcher(threading.Thread,):

    def __init__(self, dispatcherQueue):
        
        self.dispatcherQueue = dispatcherQueue
        self.startFlag = False
        super().__init__()

        self.utl = UTL.Utility.getInstance()

        self.dataFrame = pd.DataFrame(None, columns = [
                "IP",
                "MAC",
                "In",
                "Out",
                "LastSeen"]) 

    def start(self):
        self.startFlag = True
        super().start()

        Dispatcher.register('usage_data', callable=lambda:self.dataFrame)
        self.remotePipe = Dispatcher(address=('', 888), authkey=b'whitestat')
        self.remotingServer = remotePipe.get_server()
        self.remotingServer.serve_forever()

    def run(self):

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

                os.system('cls' if os.name == 'nt' else 'clear')
                print(frame)

            time.sleep(1)


    def PopulateFrame(self, frame, mac,ip,sizeInBytes,lastSeen, isSource = True):

        index = -1

        if self.utl.IsLANIP(ip):
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
        self.startFlag = False
        super().join()