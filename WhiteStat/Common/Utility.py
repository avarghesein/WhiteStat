import os
import sys
from shutil import copyfile
import json 
from datetime import datetime
import socket
from socket import AF_INET6
import threading

def GetEnv(key, defaultVal=""):
    try:
        return os.environ[key] if key in os.environ else defaultVal
    except Exception as e:
        print(e)
        return  defaultVal

def get_script_path():
    return os.path.dirname(os.path.realpath(sys.argv[0]))

def Initialize(role, configFolder, url, serverPort=777,hostIface = "eth0"):
    try:
        scriptPath = get_script_path() + "/Common/Config/"
        if not os.path.exists(f"{configFolder}/WhiteStatConfig.json"):
            copyfile(f"{scriptPath}/WhiteStatConfig.json", f"{configFolder}/WhiteStatConfig.json")
            copyfile(f"{scriptPath}/WhiteStat.db", f"{configFolder}/WhiteStat.db")
            #copyfile(f"{scriptPath}/MAC_HOST.txt", f"{configFolder}/MAC_HOST.txt")

            jsonObj = json.loads(open(f"{configFolder}/WhiteStatConfig.json", 'r').read())
            jsonObj["ROLE"] = role
            jsonObj["MONITOR_URL"] = url
            jsonObj["ANALYZER_PORT"] = int(serverPort)
            jsonObj["DATA_STORE"] = configFolder
            jsonObj["HOST_INTERFACE"] = hostIface
            
            f = open(f"{configFolder}/WhiteStatConfig.json", "w")
            json.dump(jsonObj, f, indent = 6) 
            f.close()
        
        jsonObj = json.loads(open(f"{configFolder}/WhiteStatConfig.json", 'r').read())
        utl = Utility.getInstance(jsonObj)

    except Exception as e:
        print(e)  


class Utility:
    __instance = None

    @staticmethod 
    def getInstance(jsonObj=None):
        """ Static access method. """
        if Utility.__instance == None:
            Utility(jsonObj)
        return Utility.__instance

    def __init__(self,jsonObj=None):
        """ Virtually private constructor. """
        if Utility.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            Utility.__instance = self

        self._lock = threading.Lock()        

        self.ipTypeLocal = {}
        self.ipHashTypeLocal = {}
        self.macStrings = {}
        self.ipStrings = {}

        self._hashLock = threading.Lock()
        self.ipHashMap = {}
        self.hashIPMap = {}
        self.ipHashIdx = 0

        self.macHashMap = {}
        self.hashMacMap = {}
        self.macHashIdx = 0

        self.jsonObj = jsonObj

        self.role = jsonObj["ROLE"]
        self.configFolder = jsonObj["DATA_STORE"]

        self.hostInterfaces = jsonObj["HOST_INTERFACE"]
        self.url = jsonObj["MONITOR_URL"]
        self.updateDBSeconds = int(jsonObj["UpdateDBSeconds"])
        self.idleSeconds = int(jsonObj["IdleSeconds"])
        self.memoryLimitInMB = int(jsonObj["MemoryLimitInMB"])

        self.ServerPort = int(jsonObj["ANALYZER_PORT"])

        #self.macmac = f"{self.configFolder}/{jsonObj['MAC_MAC_REWRITE']}"
        #self.macmacDict = self.__ToDictionary(f"{self.macmac}",self.PackMacToInt, self.PackMacToInt)
        self.macmacDict = {}

        #self.ipmac = f"{self.configFolder}/{jsonObj['IP_MAC_REWRITE']}"
        #self.ipmacDict = self.__ToDictionary(f"{self.ipmac}", self.PackIpToInt, self.PackMacToInt)
        self.ipmacDict = {}

        #self.macHost = f"{self.configFolder}/{jsonObj['MAC_HOST_MAP']}"
        #self.macHostDict = self.__ToDictionary(f"{self.macHost}")
        self.macHostDict = {}

        self.db = f"{self.configFolder}/{jsonObj['DBFile']}"
        self.log = f"{self.configFolder}/{jsonObj['LOGFile']}"
        self.trace = f"{self.configFolder}/{jsonObj['TRACEFile']}"
        self.lanSegMasks = f"{jsonObj['LAN_SEGMENT_V4_MASKS']}"
        self.lanSegV6Masks = f"{jsonObj['LAN_SEGMENT_V6_MASKS']}"

        self.lanRouters = f"{jsonObj['LAN_ROUTERS_TO_SKIP'].strip()}"

        if(self.lanRouters != ""):
            self.lanRouters = [self.MacToHash(self.PackMacToInt(router.strip())) for router in self.lanRouters.split('|')]
        else:
            self.lanRouters = []

        self.extraPcapFilter = f"{jsonObj['EXTRA_PCAP_FILTER']}"       
        

    def IpToHash(self, ipInt):
        if ipInt in self.ipHashMap:
            return self.ipHashMap[ipInt]
        
        ipHash = 0
        with self._hashLock:
            self.ipHashIdx += 1
            ipHash = self.ipHashIdx
            self.ipHashMap[ipInt] = ipHash
            self.hashIPMap[ipHash] = ipInt
        
        return ipHash

    def HashToIp(self, hashInt):
        if hashInt in self.hashIPMap:
            return self.hashIPMap[hashInt]

        return 0

    def HashToMac(self, hashInt):
        if hashInt in self.hashMacMap:
            return self.hashMacMap[hashInt]

        return 0

    def MacToHash(self, macInt):
        if macInt in self.macHashMap:
            return self.macHashMap[macInt]
        
        macHash = 0
        with self._hashLock:
            self.macHashIdx += 1
            macHash = self.macHashIdx
            self.macHashMap[macInt] = macHash
            self.hashMacMap[macHash] = macInt
        
        return macHash


    def __ToDictionary(self,file, keyConverter = None, valueConverter = None):
        try:
            d = {}
            with open(file) as f:
                for line in f:
                    (key, val) = line.split('|')
                    key = key.strip()
                    val = val.strip()

                    if (not (key is None) and key != "") and (not (val is None) and val != "") :
                        if not(keyConverter is None):
                            key = keyConverter(key)

                        if not(valueConverter is None):
                            val = valueConverter(val)

                        d[key] = val
            return d
        except Exception as e:
            self.Log(e)   

        return {}

    def IsWindows(self):
        platform = GetEnv("PLATFORM","LINUX")
        return platform == "WIN64"

    def GetLANSegments(self):
        return self.lanSegMasks.split('|')
    
    def GetLANRouters(self):
        return self.lanRouters

    def GetMacHostDict(self):
        return self.macHostDict

    def GetMacMacDict(self):
        return self.macmacDict

    def GetIpMacDict(self):
        return self.ipmacDict

    def GetRoles(self):
        return self.role.split('|')
    
    def IsMonitor(self):
        roles = self.GetRoles()
        if(roles == []): 
            return True
        return "MONITOR" in self.GetRoles()
    
    def IsAnalyzer(self):
        roles = self.GetRoles()
        if(roles == []): 
            return True
        return "ANALYZER" in self.GetRoles()

    def GetUrl(self):
        return self.url

    def GetUpdateDBSeconds(self):
        return self.updateDBSeconds

    def GetMemoryLimitInMB(self):
        return self.memoryLimitInMB

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

    def GetLog(self):
        return self.log

    def GetTrace(self):
        return self.trace

    def Trace(self, message):
        try:
            print(message)
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with self._lock:
                with open(self.trace, "a") as logFile:
                    logFile.write(date + ":" +message +"\n")
                    logFile.close()
        except Exception as e:
           self.Log(e) 

    def Log(self, exception):
        try:
            print(exception)
            import sys
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            msg=f"{exc_type},{fname},{exc_tb.tb_lineno}"
            print(exc_type, fname, exc_tb.tb_lineno)
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with self._lock:
                with open(self.log, "a") as logFile:
                    logFile.write(date + ":" + str(exception) + ":" + msg +"\n")
                    logFile.close()
        except Exception as e:
            print(e)  


    def PackHexToInt(self, hexString):
        return self.PackBytesToInt(bytearray.fromhex(hexString.strip()))

    def PackMacToInt(self, macString):
        return self.PackBytesToInt(bytearray.fromhex(macString.strip().replace(':','')))

    def PackIpToInt(self, ipString):
        ipBytes = None

        if ":" in ipString:
            #ipBytes = bytearray.fromhex(ipString.strip().replace(':',''))
            ipBytes = socket.inet_pton(socket.AF_INET6,ipString)
        else:
            ipBytes = socket.inet_pton(socket.AF_INET,ipString)
            #ipBytes = bytearray([int(byte) for byte in ipString.split(".")]) 

        return self.PackBytesToInt(ipBytes)


    def PackBytesToInt(self, listOfBytes):
        packedBytesInt = 0  

        for index, byte in enumerate(listOfBytes, start=0):
            packedBytesInt = (packedBytesInt << 8) | byte 
        #x_int = int.from_bytes(x_bytes, byteorder='big')
        return packedBytesInt

    def UnpackIntToBytes(self,packedBytesInt):
        import math
        number_of_bytes = int(math.ceil(int(packedBytesInt).bit_length() / 8))

        return bytearray([(((255 << (index * 8)) & packedBytesInt) >> (index * 8)) for 
                index in range(number_of_bytes - 1,-1,-1)])

        # import math
        # number_of_bytes = int(math.ceil(packedBytesInt.bit_length() / 8))
        # byteList = packedBytesInt.to_bytes(number_of_bytes, byteorder='big')
        # return ":".join(['%02x' % byte for byte in byteList])

    def UnPackPackedIntToString(self, packedBytesInt,sep = ":"):
        if packedBytesInt in self.macStrings.keys():
            return self.macStrings[packedBytesInt]

        #Add support for IPas well, change sep and formatter
        byteList = self.UnpackIntToBytes(packedBytesInt)
        byteList = bytearray( [0 for idx in range(0,6-len(byteList))] ) + byteList

        macString = sep.join(['%02x' % byte for byte in byteList])

        with self._lock:
            if not( packedBytesInt in self.macStrings.keys()):
                self.macStrings[packedBytesInt] = macString

        return macString

    def UnPackIPPackedIntToString(self, packedBytesInt):
        if packedBytesInt in self.ipStrings.keys():
            return self.ipStrings[packedBytesInt]

        if packedBytesInt <= 0:
            return "0.0.0.0"
            
        ipBytes = bytes(self.UnpackIntToBytes(packedBytesInt))

        if len(ipBytes) > 4:
            ipBytes = bytearray( [0 for idx in range(0, 16-len(ipBytes))] ) + ipBytes
        else:
            ipBytes = bytearray( [0 for idx in range(0, 4-len(ipBytes))] ) + ipBytes

        ipString = ""

        if(len(ipBytes) > 4):
            ipString = socket.inet_ntop(AF_INET6,ipBytes)
        else:
              ipString = socket.inet_ntoa(ipBytes)

        with self._lock:
            if not( packedBytesInt in self.ipStrings.keys()):
                self.ipStrings[packedBytesInt] = ipString

        return ipString


    def GetAllV4LANMasks(self):
        return "0.0.0.0|10|192.168|172.16|172.17".split("|")
    
    def GetExtraPcapFilter(self):
        return self.extraPcapFilter

    def GetHostInterfaces(self):
        return self.hostInterfaces.split("|")

    def GetV4LANMasks(self):
        lanMasks = self.lanSegMasks.split("|")

        if lanMasks == None or len(lanMasks) <= 0:
            lanMasks = self.GetAllV4LANMasks()
        
        return lanMasks
    
    def GetV6LANMasks(self):
        lanMasks = self.lanSegV6Masks.split("|")

        if lanMasks == None or len(lanMasks) <= 0:
            lanMasks = "fe80|fec0|fd".split("|")
        
        return lanMasks

    
    def IsLANIPHash(self,ipHash:int):
        if ipHash in self.ipHashTypeLocal.keys():
            return self.ipHashTypeLocal[ipHash]
        
        fnHashToIp = lambda ipHash : self.HashToIp(ipHash)
        flag = self.IsLANIPBytes(fnHashToIp(ipHash))

        with self._lock:
            if not( ipHash in self.ipHashTypeLocal.keys()):
                self.ipHashTypeLocal[ipHash] = flag

        return flag


    def IsLANIPBytes(self,packedBytesInt:int):

        if packedBytesInt in self.ipTypeLocal.keys():
            return self.ipTypeLocal[packedBytesInt]

        lanV4Nets = [bytearray([int(byte) for byte in lan.split(".")]) for lan in self.GetV4LANMasks()]
        lanV6Nets = [bytearray.fromhex(lan.strip().replace(':','')) for lan in self.GetV6LANMasks()]

        ipBytes = self.UnpackIntToBytes(packedBytesInt)
        lanNets = lanV4Nets if len(ipBytes) <= 4 else lanV6Nets

        ipInLan = list(filter(lambda lanNet: lanNet == ipBytes[0:len(lanNet)], lanNets)) 

        flag = ((not (ipInLan is None )) and (len(ipInLan) > 0))

        with self._lock:
            if not( packedBytesInt in self.ipTypeLocal.keys()):
                self.ipTypeLocal[packedBytesInt] = flag

        return flag        
 
    def AssignRouters(self, routerList):
        if len(self.GetLANRouters()) > 0:
            return
        
        routers = [self.UnPackPackedIntToString(self.HashToMac(router)) for router in routerList]

        self.jsonObj['LAN_ROUTERS_TO_SKIP'] = '|'.join(list(routers))
        self.lanRouters = routerList

        f = open(f"{self.configFolder}/WhiteStatConfig.json", "w")
        json.dump(self.jsonObj, f, indent = 6) 
        f.close()
    
    def SetHostNames(self, hostNames):
        self.macHostDict = {**self.macHostDict, **hostNames}
        return self.macHostDict
    
        
