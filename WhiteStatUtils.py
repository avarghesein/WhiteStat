import os
import sys
from shutil import copyfile
import json 


def GetEnv(key, defaultVal=""):
    try:
        return os.environ[key] if key in os.environ else defaultVal
    except Exception as e:
        print(e)
        return  defaultVal

def get_script_path():
    return os.path.dirname(os.path.realpath(sys.argv[0]))

def Initialize(configFolder, url, serverPort=777):
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

    def GetServerPort(self):
        return self.ServerPort

    def GetDB(self):
        return self.db

    def GeLog(self):
        return self.log

    def GetIPFilter(self):
        return self.ipfilter

    def Log(self, exception):
        try:
            print(exception)
            import sys
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            msg=f"{exc_type},{fname},{exc_tb.tb_lineno}"
            print(exc_type, fname, exc_tb.tb_lineno)
              
            with open(self.log, "a") as logFile:
                logFile.write(str(exception)+ msg )
                logFile.close()
        except Exception as e:
            print(e)  



