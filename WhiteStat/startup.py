
import warnings
warnings.filterwarnings('ignore')

import sys
import time
import subprocess
import psutil
import WhiteStat.Common.Utility as UTL
import os

def main(argv):    
    #os.system('cls' if os.name == 'nt' else 'clear') 
    #os.chdir("/media/TMP-DSK/Python/WhiteStatGit/WhiteStat/") 
    #argv[0] = "./WhiteStatService.sh"
    print(argv[1])
    utl = None
    try:
        platform = UTL.GetEnv("PLATFORM","LINUX")
        dataStorePath = "Set env variable DATA_STORE. For debugging Set in .pythonenv"
        role = UTL.GetEnv("ROLE","MONITOR|ANALYZER")
        print(role)
        dataStore = UTL.GetEnv("DATA_STORE",dataStorePath)
        #dataStore = UTL.GetEnv("DATA_STORE","/mnt/whitestat/Config")
        print(dataStore)
        url = UTL.GetEnv("MONITOR_URL",":888")
        print(url)
        serverPort = UTL.GetEnv("ANALYZER_PORT",777)
        print(serverPort)
        hostIface = UTL.GetEnv("HOST_INTERFACE","eth0")
        print(hostIface)
        UTL.Initialize(role, dataStore, url, serverPort, hostIface)
        utl = UTL.Utility.getInstance()

        def bash(s): 
            try:           
                return subprocess.check_output(s,shell=True)
            except:
                pass

        def StartProcess(commandLine):
            popen = subprocess.Popen([commandLine,"",""], start_new_session=True)
            return popen.pid

        def KillProcessTree(pid):
            parent_pid = pid
            parent = psutil.Process(parent_pid)
            for child in parent.children(recursive=True):
                child.kill()
            parent.kill()
        
        def MemoryUsage(pid):
            memUsage = 0.0
            parent_pid = pid
            parent = psutil.Process(parent_pid)
            for child in parent.children(recursive=True):
                memUsage += child.memory_full_info().uss

            memUsage += parent.memory_full_info().uss
            return memUsage

        memoryLimitInMB = utl.GetMemoryLimitInMB()
        commandLine = argv[1]

        processID = -1
        while True:
            if processID == -1:
                processID = StartProcess(commandLine)
                utl.Trace("Started Whitestat")
                time.sleep(5) 
                continue
            
            memoryUsage = MemoryUsage(processID)  # in bytes 

            maxLimit = memoryLimitInMB * 1024 * 1024

            if memoryUsage >= maxLimit:
                #stat = bash(f'kill -9 $(ps -aux | grep main.py | tr -s " " | cut -d " " -f 2)')
                KillProcessTree(processID)
                utl.Trace(f"Terminated Due to Max Memory Usage {memoryUsage}: Whitestat")
                time.sleep(5) 
                processID = StartProcess(commandLine)
                utl.Trace("Restarted WhiteStat")

            time.sleep(30) 
        
        
    except Exception as e:
        if not (utl is None):
            utl.Log(e)

if __name__ == "__main__":
  main(sys.argv)
