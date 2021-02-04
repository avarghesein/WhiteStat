import os
import sys
from shutil import copyfile
import json 
from datetime import datetime


def GetEnv(key, defaultVal=""):
    try:
        return os.environ[key] if key in os.environ else defaultVal
    except Exception as e:
        print(e)
        return  defaultVal

def get_script_path():
    return os.path.dirname(os.path.realpath(sys.argv[0]))

def Initialize(configFolder, url, serverPort=777, lanSegMasks="192.168.0|192.168.1", lanRouters=""):
    try:
        scriptPath = get_script_path() + "/Config/"
        if not os.path.exists(f"{configFolder}/WhiteStatConfig.json"):
            copyfile(f"{scriptPath}/WhiteStatConfig.json", f"{configFolder}/WhiteStatConfig.json")
            copyfile(f"{scriptPath}/WhiteStat.db", f"{configFolder}/WhiteStat.db")
            copyfile(f"{scriptPath}/IP_MAC.txt", f"{configFolder}/IP_MAC.txt")
            copyfile(f"{scriptPath}/MAC_MAC.txt", f"{configFolder}/MAC_MAC.txt")
            copyfile(f"{scriptPath}/MAC_MAC.txt", f"{configFolder}/MAC_HOST.txt")

            jsonObj = json.loads(open(f"{configFolder}/WhiteStatConfig.json", 'r').read())
            jsonObj["DARKSTAT_URL"] = url
            jsonObj["SERVER_PORT"] = int(serverPort)
            jsonObj["DATA_STORE"] = configFolder
            jsonObj["LAN_SEGMENT_MASKS"] = lanSegMasks
            jsonObj["LAN_ROUTERS_TO_SKIP"] = lanRouters
            
            f = open(f"{configFolder}/WhiteStatConfig.json", "w")
            json.dump(jsonObj, f, indent = 6) 
            f.close()
        
        jsonObj = json.loads(open(f"{configFolder}/WhiteStatConfig.json", 'r').read())
        utl = WhiteStatUtils.getInstance(jsonObj)

    except Exception as e:
        print(e)  


class WhiteStatUtils:
    __instance = None

    @staticmethod 
    def getInstance(jsonObj=None):
        """ Static access method. """
        if WhiteStatUtils.__instance == None:
            WhiteStatUtils(jsonObj)
        return WhiteStatUtils.__instance

    def __init__(self,jsonObj=None):
        """ Virtually private constructor. """
        if WhiteStatUtils.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            WhiteStatUtils.__instance = self

        self.jsonObj = jsonObj

        self.configFolder = jsonObj["DATA_STORE"]

        self.url = jsonObj["DARKSTAT_URL"]
        self.ipfilter = jsonObj["IPFilter"]
        self.updateDBSeconds = int(jsonObj["UpdateDBSeconds"])
        self.idleSeconds = int(jsonObj["IdleSeconds"])
        self.ServerPort = int(jsonObj["SERVER_PORT"])
        self.macmac = f"{self.configFolder}/{jsonObj['MAC_MAC_REWRITE']}"
        self.macmacDict = self.__ToDictionary(f"{self.macmac}")
        self.ipmac = f"{self.configFolder}/{jsonObj['IP_MAC_REWRITE']}"
        self.ipmacDict = self.__ToDictionary(f"{self.ipmac}")
        self.macHost = f"{self.configFolder}/{jsonObj['MAC_HOST_MAP']}"
        self.macHostDict = self.__ToDictionary(f"{self.macHost}")

        self.db = f"{self.configFolder}/{jsonObj['DBFile']}"
        self.log = f"{self.configFolder}/{jsonObj['LOGFile']}"
        self.trace = f"{self.configFolder}/{jsonObj['TRACEFile']}"
        self.lanSegMasks = f"{jsonObj['LAN_SEGMENT_MASKS']}"
        self.lanRouters = f"{jsonObj['LAN_ROUTERS_TO_SKIP']}"


    def __ToDictionary(self,file):
        try:
            d = {}
            with open(file) as f:
                for line in f:
                    (key, val) = line.split('|')
                    d[key.strip()] = val.strip()
            return d
        except Exception as e:
            self.Log(e)   

        return {}

    def GetLANSegments(self):
        return self.lanSegMasks.split('|')
    
    def GetLANRouters(self):
        return self.lanRouters.split('|')

    def GetMacHostDict(self):
        return self.macHostDict

    def GetMacMacDict(self):
        return self.macmacDict

    def GetIpMacDict(self):
        return self.ipmacDict

    def GetUrl(self):
        return self.url

    def GetUpdateDBSeconds(self):
        return self.updateDBSeconds

    def GetSleepSeconds(self):
        return self.idleSeconds

    def GetIPStabilizeSeconds(self):
        default = 60
        conf = (self.idleSeconds * 2.5)
        return default if conf < default else default

    def GetServerPort(self):
        return self.ServerPort

    def GetDB(self):
        return self.db

    def GeLog(self):
        return self.log

    def GetTrace(self):
        return self.trace

    def GetIPFilter(self):
        return self.ipfilter

    def Trace(self, message):
        try:
            print(message)
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.trace, "a") as logFile:
                logFile.write(date + ":" +message +"\n")
                logFile.close()
        except Exception as e:
            Log(e) 

    def Log(self, exception):
        try:
            print(exception)
            import sys
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            msg=f"{exc_type},{fname},{exc_tb.tb_lineno}"
            print(exc_type, fname, exc_tb.tb_lineno)
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self.log, "a") as logFile:
                logFile.write(date + ":" + str(exception) + ":" + msg +"\n")
                logFile.close()
        except Exception as e:
            print(e)  


    def AssignRouterLanSegments(self, frame):
        if len(self.GetLANRouters()) > 0 and len(self.GetLANSegments()) > 0:
            return
        
        fullLanSeg = ["0.0.0.0","192.168.", "10."] + [f"172.{i}." for i in range(16,17)]

        lanSegs = {}

        def CheckLanSegment(mac,ip):     
            ipInLan = list(filter(lambda x: ip.startswith(x), fullLanSeg))    

            if ((not (ipInLan is None )) and (len(ipInLan) > 0)) :
                lanSegs.update(dict(zip(ipInLan, [True]*len(ipInLan))))
                return True
            
            return False;

        frame["lanFlag"]= frame.apply(lambda x: CheckLanSegment(x.MAC, x.IP), axis=1)
        frame=frame[frame.lanFlag == False]
        frame=frame[['MAC']]  
        frame=frame.drop_duplicates()
        routers = frame['MAC'].tolist()

        self.jsonObj['LAN_SEGMENT_MASKS'] = '|'.join(routers)
        self.jsonObj['LAN_ROUTERS_TO_SKIP'] = '|'.join(list(lanSegs.keys()))
        self.lanSegMasks = f"{self.jsonObj['LAN_SEGMENT_MASKS']}"
        self.lanRouters = f"{self.jsonObj['LAN_ROUTERS_TO_SKIP']}"

        f = open(f"{self.configFolder}/WhiteStatConfig.json", "w")
        json.dump(self.jsonObj, f, indent = 6) 
        f.close()

        
