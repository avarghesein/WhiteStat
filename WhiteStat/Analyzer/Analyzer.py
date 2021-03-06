import requests
import numpy as np
from datetime import datetime, timedelta
import WhiteStat.Common.Utility as UTL
import WhiteStat.NetMonitor.RemoteServerEx as RS
import numpy.lib.recfunctions as NF
import copy

LOCAL_IP_SET = 0
REMOTE_IP_SET = 1
TIME_STAMP = 2

class Analyzer(object):
    __slots__ = ['__weakref__', 'utl', 'remoteManager', 'IpMacDic','MacMacDic','MacHostDic', 'serverTimeStamp', 'serverRestarted']

    def __init__(self):

        self.utl = UTL.Utility.getInstance()
        self.remoteManager = RS.RemoteManager()
        self.IpMacDic = self.utl.GetIpMacDict()
        self.MacMacDic = self.utl.GetMacMacDict()
        self.MacHostDic = self.LoadLocalHostNames()
        self.serverTimeStamp = None
        self.serverRestarted = None

    def ReplaceMACs(self, ip, mac):
        new_mac = self.IpMacDic.get(ip, mac)
        new_mac = self.MacMacDic.get(new_mac, new_mac)
        return new_mac


    def GetNowUtc(self):
        #return (datetime.utcnow().date()+ timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        return datetime.now().date().strftime("%Y-%m-%d %H:%M:%S")
        
    def ConvertToKB(self, bytes):
        try:
            return round(bytes / 1024,2)
        except Exception as e:
            print(bytes)
            raise

    def DiscardRoutersForLocalIP(self, frame):

        routers = self.utl.GetLANRouters()

        def CheckRouterIP(macInt):     
            return macInt in routers

        frame = self.AddField(frame, "routerFlag","i1",False)
        #frame.loc[frame.IP == "192.168.1.21", 'MAC'] = "f8:c4:f3:50:53:68"

        fnCheckRouterFlg = np.vectorize(CheckRouterIP)
        frame["routerFlag"] = fnCheckRouterFlg(frame["MAC"])
        frame = frame[ (frame["routerFlag"] == False) | (frame["LOCAL"] == False) ]
        frame = NF.drop_fields(frame, ['routerFlag'])
        return frame

    def BuildFrame(self, usageList, fromDB = False):
        
        dtypes =[
                    ('IP', 'i4'),
                    ('MAC', 'i4'),
                    ('IN', 'f8'),
                    ('OUT', 'f8'),
                    ('SEEN', 'M8[ms]'),
                    ('LOCAL', 'i1')
                    ]            
        
        if fromDB:
            dtypes += [
                ('DATE', 'M8[ms]'),
                ('LSTDAY_IN', 'f8'),
                ('LSTDAY_OUT', 'f8'),
            ]

        return np.array(usageList, dtype=dtypes)


    def DeSerializeFrame(self, usageFrame):
        DATE_OFFSET = 0
        LOCAL_IP_OFFSET = 1
        REMOTE_IP_OFFSET = 2
        TIME_STAMP_OFFSET = 3

        if ((usageFrame is None) or 
            (usageFrame[DATE_OFFSET] is None) or 
            (usageFrame[LOCAL_IP_OFFSET] is None) or
            (usageFrame[REMOTE_IP_OFFSET] is None) or
            (usageFrame[TIME_STAMP_OFFSET] is None)):

            return None
        
        date = usageFrame[DATE_OFFSET] + " "

        utl = self.utl

        localIPs = { utl.PackHexToInt(rec[0]) : [ utl.PackHexToInt(rec[1]), rec[2], rec[3], date + rec[4] ] 
                        for rec in [ rec.split("|") 
                        for rec in 
                        [frame for frame in usageFrame[LOCAL_IP_OFFSET].splitlines()]]
                    }

        remoteIPs = { utl.PackHexToInt(rec[0]) : [ utl.PackHexToInt(rec[1]), rec[2], rec[3], date + rec[4] ] 
                        for rec in [ rec.split("|") 
                        for rec in 
                        [frame for frame in usageFrame[REMOTE_IP_OFFSET].splitlines()]]
                    }

        timeStamp = usageFrame[TIME_STAMP_OFFSET]

        return (localIPs,remoteIPs,timeStamp)


    def GetUsageFrame(self,date):
        try:
            usageFrame = None

            if not self.utl.IsMonitor():
                usageFrame = self.remoteManager.FetchFrame()
            else:
                usageFrame = RS.RemoteUsageFrame.getInstance().GetFrame()

            usageFrame = self.DeSerializeFrame(usageFrame)

            if (usageFrame is None) or (usageFrame[LOCAL_IP_SET] is None) or (usageFrame[REMOTE_IP_SET] is None):
                return None

            newTimeStamp = usageFrame[TIME_STAMP]

            if self.serverTimeStamp is None:
                self.serverTimeStamp = newTimeStamp
                self.serverRestarted = None
            else:
                self.serverRestarted = newTimeStamp > self.serverTimeStamp
                self.serverTimeStamp = newTimeStamp  

            localIPs =  [tuple([self.utl.IpToHash(value[0])] + 
            [self.utl.MacToHash(key)] + value[1:] + [True]) 
            for key, value in usageFrame[LOCAL_IP_SET].items()]  

            localUsageBytes = self.BuildFrame(localIPs)

            remoteIps = [tuple([self.utl.IpToHash(key)] + 
            [self.utl.MacToHash(value[0])] + value[1:] + [False]) 
            for key, value in usageFrame[REMOTE_IP_SET].items()]

            remoteUsageBytes = self.BuildFrame(remoteIps)

            usageFrame = np.concatenate((localUsageBytes, remoteUsageBytes), axis=0)

            if(len(usageFrame) <= 0):
                self.utl.Trace("No records from Monitor. May not be initialized the first frame")
                return None

            fnReplaceMacs = np.vectorize(self.ReplaceMACs)
            usageFrame["MAC"]=fnReplaceMacs(usageFrame["IP"],usageFrame["MAC"])
            
            fnConvertToKB = np.vectorize(self.ConvertToKB)
            usageFrame["IN"]=fnConvertToKB(usageFrame["IN"])
            usageFrame["OUT"]=fnConvertToKB(usageFrame["OUT"])

            #utcDate=self.GetNowUtc()
            usageFrame = self.AddField(usageFrame, "DATE","M8[ms]",date)

            #Max get records for last 2 days
            curDate = (date - timedelta(seconds=24 * 60 * 60))
            usageFrame = usageFrame[usageFrame["SEEN"] >= curDate]

            routerMacs = np.unique(usageFrame["MAC"][usageFrame["LOCAL"] == False])

            self.utl.AssignRouters(routerMacs)

            usageFrame = self.DiscardRoutersForLocalIP(usageFrame)

            return usageFrame
        except Exception as e:
            self.utl.Log(e)
            return None

    def AddField(self, frame, name, dataType, defaultVal = None):
        frame = NF.append_fields(frame, name, [], dtypes=[(dataType)], fill_value=defaultVal)
        frame[name] = defaultVal
        return frame

    def GetDayFirstFrame(self, date, prevUsageFrame):
        try:

            usageFrame = self.GetUsageFrame(date)    

            if (usageFrame is None) :
                return (None, prevUsageFrame)    

            ##Get last day LSTDAY values from PrevDataUsageFrame
            if not (prevUsageFrame is None):

                prevFrame = prevUsageFrame.copy()
                prevFrame['DATE'] = date

                localNewFrame = usageFrame[usageFrame["LOCAL"] == True]
                remoteNewFrame = usageFrame[usageFrame["LOCAL"] == False]

                localOldFrame = prevFrame[prevFrame["LOCAL"] == True]
                remoteOldFrame = prevFrame[prevFrame["LOCAL"] == False]

                isNull = True

                localMergedFrame = NF.join_by(["MAC","DATE"],localOldFrame, localNewFrame, jointype="outer")                
                mask = localMergedFrame.mask
                #data = localMergedFrame.data
                newRecordsOnly = ( (mask["SEEN2"] != isNull) )
                localMergedFrame = localMergedFrame[newRecordsOnly]
                localMergedFrame["IN1"] = 0.0
                localMergedFrame["OUT1"] = 0.0
                localMergedFrame = self.ProcessMergedFrame(localMergedFrame)

                remoteMergedFrame = NF.join_by(["IP","DATE"],remoteOldFrame, remoteNewFrame, jointype="outer")
                mask = remoteMergedFrame.mask
                #data = remoteMergedFrame.data
                newRecordsOnly = ( (mask["SEEN2"] != isNull) )
                remoteMergedFrame = remoteMergedFrame[newRecordsOnly]
                remoteMergedFrame["IN1"] = 0.0
                remoteMergedFrame["OUT1"] = 0.0
                remoteMergedFrame = self.ProcessMergedFrame(remoteMergedFrame,False) 

                mergedFrame = np.concatenate((localMergedFrame, remoteMergedFrame), axis=0)
                usageFrame = mergedFrame
                prevUsageFrame = None
            else:
                usageFrame = self.AddField(usageFrame, "LSTDAY_IN","f8",0.0)
                usageFrame = self.AddField(usageFrame, "LSTDAY_OUT","f8",0.0)

                usageFrame["LSTDAY_IN"] = usageFrame["IN"]
                usageFrame["LSTDAY_OUT"] = usageFrame["OUT"]

                usageFrame["IN"] -= usageFrame["LSTDAY_IN"]
                usageFrame["OUT"] -= usageFrame["LSTDAY_OUT"]
        
            return (usageFrame, None)

        except Exception as e:
            self.utl.Log(e)
            return (None, prevUsageFrame)  

    def BuildMergedFrame(self, usageList, isLocal = True):
        dtypes = None
        if isLocal:
            dtypes =[
                    ('MAC', 'i4'),
                    ('DATE', 'M8[ms]'),
                    ('IP1', 'i4'),
                    ('IP', 'i4'),
                    ('IN', 'f8'),
                    ('IN2', 'f8'),
                    ('OUT', 'f8'),
                    ('OUT2', 'f8'),
                    ('SEEN1', 'M8[ms]'),
                    ('SEEN', 'M8[ms]'),
                    ('LOCAL1', 'i1'),
                    ('LOCAL', 'i1'),
                    ('LSTDAY_IN', 'f8'),
                    ('LSTDAY_OUT', 'f8')
                    ]
        else:
            dtypes =[
                    ('IP', 'i4'),
                    ('DATE', 'M8[ms]'),
                    ('MAC1', 'i4'),
                    ('MAC', 'i4'),
                    ('IN', 'f8'),
                    ('IN2', 'f8'),
                    ('OUT', 'f8'),
                    ('OUT2', 'f8'),
                    ('SEEN1', 'M8[ms]'),
                    ('SEEN', 'M8[ms]'),
                    ('LOCAL1', 'i1'),
                    ('LOCAL', 'i1'),
                    ('LSTDAY_IN', 'f8'),
                    ('LSTDAY_OUT', 'f8')
                    ]
        return np.array(usageList, dtype=dtypes)

    def ProcessMergedFrame(self, frame, isLocal = True):
        mask = frame.mask
        data = frame.data

        isNull = True
        #2 is New, 1 is Old. i.e. IP1 is old IP2 is new
        #bothInOldNew = ( (mask["SEEN2"] != isNull) & (mask["SEEN1"] != isNull) )
        OnlyInOld = ( (mask["SEEN2"] == isNull) )
        #OnlyInNew = ( (mask["SEEN1"] == isNull) )


        if(isLocal):
            data["IP2"][OnlyInOld] = data["IP1"][OnlyInOld]
        else:
            data["MAC2"][OnlyInOld] = data["MAC1"][OnlyInOld]


        data["LSTDAY_IN"][mask["LSTDAY_IN"] == isNull] = 0.0
        data["LSTDAY_OUT"][mask["LSTDAY_OUT"] == isNull] = 0.0

        data["IN1"][mask["IN1"] == isNull] = 0.0
        data["OUT1"][mask["OUT1"] == isNull] = 0.0
        data["IN2"][mask["IN2"] == isNull] = 0.0
        data["OUT2"][mask["OUT2"] == isNull] = 0.0

        #for old records in local, retain the same value (will happen below while adding the bytes)
        #records exists only in local, and no more in server
        data["IN2"][OnlyInOld] = data["LSTDAY_IN"][OnlyInOld]
        data["OUT2"][OnlyInOld] = data["LSTDAY_OUT"][OnlyInOld]

        if (self.serverRestarted is None) or (self.serverRestarted == False):                

            higherInCond = ( data["IN2"] >= data["LSTDAY_IN"] )
            data["IN1"][higherInCond] += (data["IN2"][higherInCond] - data["LSTDAY_IN"][higherInCond])

            higherOutCond = ( data["OUT2"] >= data["LSTDAY_OUT"] )
            data["OUT1"][higherOutCond] += (data["OUT2"][higherOutCond] - data["LSTDAY_OUT"][higherOutCond])

            lowerInCond = ( data["IN2"] < data["LSTDAY_IN"] )
            data["IN1"][lowerInCond] += data["IN2"][lowerInCond]

            lowerOutCond = ( data["OUT2"] < data["LSTDAY_OUT"] )
            data["OUT1"][lowerOutCond] += data["OUT2"][lowerOutCond]

        else:
            data["IN1"] += data["IN2"]
            data["OUT1"] += data["OUT2"]


        data["LSTDAY_IN"] = data["IN2"]
        data["LSTDAY_OUT"] = data["OUT2"]

        data["LOCAL2"][OnlyInOld] = data["LOCAL1"][OnlyInOld]
        data["SEEN2"][OnlyInOld] = data["SEEN1"][OnlyInOld]

        frame = self.BuildMergedFrame(data,isLocal)

        frame = NF.drop_fields(frame, ['IN2','OUT2','SEEN1','LOCAL1'])

        if isLocal:
            frame = NF.drop_fields(frame, ['IP1'])
        else:
            frame = NF.drop_fields(frame, ['MAC1'])

        fnRound = np.vectorize(round)
        frame['IN'] = fnRound(frame['IN'],2)
        frame['OUT'] = fnRound(frame['OUT'],2)
        frame['LSTDAY_IN'] = fnRound(frame['LSTDAY_IN'],2)
        frame['LSTDAY_OUT'] = fnRound(frame['LSTDAY_OUT'],2)

        return frame [[ 'IP','MAC','DATE','IN','OUT', 'SEEN','LOCAL', 'LSTDAY_IN' , 'LSTDAY_OUT' ]].copy()

    def GetDayNextFrame(self, date, prevUsageFrame):
        try:
            startUsageFrame = prevUsageFrame
            nextUsageFrame = self.GetUsageFrame(date)  
            
            if nextUsageFrame is None:
                return None

            if startUsageFrame is None:
                return nextUsageFrame
            
            localNewFrame = nextUsageFrame[nextUsageFrame["LOCAL"] == True]
            remoteNewFrame = nextUsageFrame[nextUsageFrame["LOCAL"] == False]

            localOldFrame = startUsageFrame[startUsageFrame["LOCAL"] == True]
            remoteOldFrame = startUsageFrame[startUsageFrame["LOCAL"] == False]

            localMergedFrame = NF.join_by(["MAC", "DATE"],localOldFrame,localNewFrame,jointype="outer")
            localMergedFrame = self.ProcessMergedFrame(localMergedFrame)

            remoteMergedFrame = NF.join_by(["IP", "DATE"],remoteOldFrame,remoteNewFrame,jointype="outer")
            remoteMergedFrame = self.ProcessMergedFrame(remoteMergedFrame,False) 

            mergedFrame = np.concatenate((localMergedFrame, remoteMergedFrame), axis=0)
  
            return mergedFrame
        except Exception as e:
            self.utl.Log(e)
            return None
    
    def PrintableFrame(self, frame):
        if frame is None:
            return None

        newFrame = frame.copy()

        def ConvertToIPString(ipHash):
            ipInt = self.utl.HashToIp(ipHash)
            return self.utl.UnPackIPPackedIntToString(ipInt)
        
        def ConvertToMACString(macHash):
            macInt = self.utl.HashToMac(macHash)            
            return self.utl.UnPackPackedIntToString(macInt)

        fnIPString = np.vectorize(ConvertToIPString)
        fnMACString = np.vectorize(ConvertToMACString)

        newFrame = self.AddField(newFrame, "MAC_STR","U17","")
        newFrame = self.AddField(newFrame, "IP_STR","U39","")
        newFrame = self.AddField(newFrame, "DATE_STR","U25","")
        newFrame = self.AddField(newFrame, "SEEN_STR","U25","")
        newFrame = self.AddField(newFrame, "LOCAL_STR","U1","")

        newFrame["MAC_STR"]=fnMACString(newFrame["MAC"])
        newFrame["IP_STR"]=fnIPString(newFrame["IP"])

        # lanV6masks = self.utl.GetV6LANMasks()

        # def FilterIPV6Local(ipv6Str):
        #     for lan in lanV6masks:
        #         if ipv6Str.startswith(lan):
        #             return True

        #     return False
        
        # fnIPV6Local = np.vectorize(FilterIPV6Local)
        # newFrame = newFrame[fnIPV6Local(newFrame["IP_STR"]) == False]

        newFrame["DATE_STR"]=(newFrame["DATE"])
        newFrame["SEEN_STR"]=(newFrame["SEEN"])
        newFrame["LOCAL_STR"]=(newFrame["LOCAL"])
 
        newFrame = NF.drop_fields(newFrame, ['IP','MAC','DATE','SEEN','LOCAL'])
        np.set_printoptions(suppress=True)
        return newFrame

    def PersistToDailyDB(self, frame, utcDate):
        connection = None
        try:  
            pFrame = self.PrintableFrame(frame)

            import sqlite3
            connection = sqlite3.connect(self.utl.GetDB())

            connection.execute(f"DELETE FROM DailyUsage WHERE date([DATE]) >= date('{utcDate}')")

            sql = "INSERT INTO DailyUsage (DATE,IP,MAC,SEEN,[IN],OUT,LSTDAY_IN,LSTDAY_OUT,LOCAL) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
 
            cursor = connection.cursor()
            
            cursor.executemany(sql, pFrame[["DATE_STR","IP_STR","MAC_STR","SEEN_STR","IN","OUT","LSTDAY_IN","LSTDAY_OUT","LOCAL_STR"]])

            # Trigger Included in SQL DBFile
            # CREATE TRIGGER trigger_update_dns_recs 
            # AFTER INSERT ON DailyUsage
            # WHEN NEW.IP NOT IN (SELECT IP FROM DNAME)
            # BEGIN

            #     INSERT INTO DNAME(IP,NAME) VALUES (NEW.IP,NULL);
                
            # END;

            connection.commit()
            del pFrame
            connection.close()
        except Exception as e:
            if connection != None:
                connection.rollback()
                connection.close()

            self.utl.Log(e)


    def ArchivePrevFrameToDB(self, utcDate):
        connection = None
        try:            
            import sqlite3
            connection = sqlite3.connect(self.utl.GetDB())  

            connection.execute("DELETE FROM UsageHistory WHERE (IP,MAC,DATE) IN "
                               "(SELECT IP,MAC,[DATE] "
                               "FROM DailyUsage "
                               f"WHERE date([DATE]) < date('{utcDate}'))"
                               )
            
            connection.execute(
                "INSERT INTO UsageHistory(IP, MAC, [IN], OUT, SEEN, LOCAL, DATE, LSTDAY_IN, LSTDAY_OUT) "
                "SELECT IP, MAC, [IN], OUT, SEEN, LOCAL, DATE, LSTDAY_IN, LSTDAY_OUT "
                f"FROM DailyUsage WHERE date([DATE]) < date('{utcDate}') AND "
                "(IP,MAC,DATE) NOT IN (SELECT IP,MAC,DATE FROM UsageHistory)")

            connection.execute(f"DELETE FROM DailyUsage WHERE date([DATE]) < date('{utcDate}')")            

            connection.commit()
            connection.close()
        except Exception as e:
            if connection != None:
                connection.rollback()
                connection.close()

            self.utl.Log(e)


    def ValidateDate(self, date_text):
        try:
            date_text = date_text.replace("T", " ")
            datetime.strptime(date_text, '%Y-%m-%d %H:%M:%S.%f')
            return True
        except ValueError:
            return False

    def RestoreFromDailyDB(self, today):
        connection = None
        frame = None
        prevFrame = None

        try:            
            import sqlite3
            connection = sqlite3.connect(self.utl.GetDB())  

            cursor = connection.execute(f"SELECT MAX(DTE) FROM (SELECT DATE AS DTE FROM DailyUsage WHERE date(DATE) < date('{today}'))")
            #cursor = connection.execute(f"SELECT DATE,LastSeen AS CNT FROM timeframe")
            prevTimeframe = cursor.fetchone()
            cursor.close()

            def IpStrToHash(ipStr):
                return self.utl.IpToHash(self.utl.PackIpToInt(ipStr))
            
            def MacStrToHash(macStr):
                return self.utl.MacToHash(self.utl.PackMacToInt(macStr))

            if not (prevTimeframe is None) and self.ValidateDate(str(prevTimeframe[0])):
                prevDate = prevTimeframe[0]

                cursor = connection.execute(f"SELECT IP, MAC, [IN], OUT, SEEN, LOCAL, DATE, LSTDAY_IN, LSTDAY_OUT " +
                f" FROM DailyUsage WHERE date(DATE)=date('{prevDate}')")

                results = cursor.fetchall()                 

                records = [ (IpStrToHash(r[0]), MacStrToHash(r[1]),r[2], r[3], r[4], r[5], r[6], r[7], r[8]) for r in list(results)]    

                prevFrame = self.BuildFrame(records,True)

            cursor = connection.execute(f"SELECT COUNT(*) AS CNT FROM dailyusage WHERE date(DATE)=date('{today}')")            
            #cursor = connection.execute(f"SELECT COUNT(*) AS CNT FROM dailyusage") 
            count=int(cursor.fetchone()[0])
            cursor.close()

            if count > 0:
                cursor = connection.execute(f"SELECT IP, MAC, [IN], OUT, SEEN, LOCAL, DATE, LSTDAY_IN, LSTDAY_OUT " +
                f" FROM dailyusage WHERE date(DATE)=date('{today}')")

                results = cursor.fetchall()  

                records = [ (IpStrToHash(r[0]), MacStrToHash(r[1]),r[2], r[3], r[4], r[5], r[6], r[7], r[8]) for r in list(results)]    

                frame = self.BuildFrame(records,True)

            connection.close()

        except Exception as e:
            if connection != None:
                connection.close()

            self.utl.Log(e)
        
        return (frame,prevFrame)


    def ReplaceHostName(self,record):
        mac = record[1]
        hostname = record[2]

        seen = record[3]
        seen = seen[seen.find("T")+1 : ].replace(".000","")
        record[3] = seen

        hostname = self.MacHostDic.get(mac,hostname)   

        if hostname is None or hostname == "(None)":
            hostname =  record[0]

        return [record[0], mac, hostname] + record[3:]

    def GetDailyUsageRecords(self):
        connection = None
        frame = None

        try:            
            import sqlite3
            connection = sqlite3.connect(self.utl.GetDB())  

            utcDate=self.GetNowUtc()

            cursor = connection.execute(f"SELECT COUNT(*) AS CNT FROM DailyUsage WHERE date(DATE)=date('{utcDate}')")            
            #cursor = connection.execute(f"SELECT COUNT(*) AS CNT FROM dailyusage") 
            count=int(cursor.fetchone()[0])
            cursor.close()

            if count > 0:

                fields="DU.IP,MAC,DN.NAME AS HOST,SEEN,[IN],OUT,DATE,LSTDAY_IN,LSTDAY_OUT,LOCAL"
                query=f"SELECT {fields} FROM DailyUsage DU LEFT JOIN DNAME DN ON DU.IP = DN.IP WHERE date(DATE)=date('{utcDate}') ORDER BY [IN] DESC"

                records = connection.execute(query).fetchall()
                records = [list(r) for r in records]

                records = list(map(self.ReplaceHostName, records))

                frame = {}
                frame["columns"] = ["IP", "MAC", "Hostname", "LastSeen", "KBIn", "KBOut", "DATE", "LSTDAY_KBIn", "LSTDAY_KBOut","LOCAL"]
                frame["data"] = records      

            connection.close()

        except Exception as e:
            if connection != None:
                connection.close()

            self.utl.Log(e)
        
        return frame
            
    def GetHistoricRecords(self, startDate, endDate, includePublicIPs = False):
        connection = None
        frame = None
        try:            
            import sqlite3
            connection = sqlite3.connect(self.utl.GetDB()) 

  
            fields="DU.IP,MAC,DN.NAME AS HOST,SEEN,[IN],OUT,DATE,LSTDAY_IN,LSTDAY_OUT,LOCAL"
            innerfields="IP,MAC,SEEN,[IN],OUT,DATE,LSTDAY_IN,LSTDAY_OUT,LOCAL"
            publicIps = "" if includePublicIPs else "AND LOCAL=1"
            dateCondition = f"(date(DATE) >= date('{startDate}') AND date(DATE) <= date('{endDate}') {publicIps} )"

            selectQuery = f"SELECT {fields} FROM  (((SELECT {innerfields}  FROM DailyUsage WHERE {dateCondition} UNION " 
            selectQuery += f"SELECT {innerfields}  FROM UsageHistory WHERE ( {dateCondition} AND (IP,MAC,DATE) NOT IN " 
            selectQuery += f"(SELECT IP,MAC,DATE FROM DailyUsage))) ) DU LEFT JOIN DNAME DN ON DU.IP = DN.IP) " 
            selectQuery += f"ORDER BY DATE DESC, [IN] DESC"

            records = connection.execute(selectQuery).fetchall()
            records = [list(r) for r in records]

            records = list(map(self.ReplaceHostName, records))

            frame = {}
            frame["columns"] = ["IP", "MAC", "Hostname", "LastSeen", "KBIn", "KBOut", "DATE", "LSTDAY_KBIn", "LSTDAY_KBOut","LOCAL"]
            frame["data"] = records
                
            connection.close()

        except Exception as e:
            if connection != None:
                connection.close()

            self.utl.Log(e)
        
        return frame
    

    def GetEmptyDnsRecords(self):
        connection = None
        records = None

        try:            
            import sqlite3
            connection = sqlite3.connect(self.utl.GetDB())  

            query="SELECT IP FROM DNAME WHERE NAME IS NULL LIMIT 15"

            records = connection.execute(query).fetchall()
            records = [list(r) for r in records]

            connection.close()

        except Exception as e:
            if connection != None:
                connection.close()

            self.utl.Log(e)
        
        return records
    
    def SetHostName(self, ip, mac, hostName, isLocal):
        try:

            if not isLocal:
                self.SetDnsRecords([[ hostName, ip]])
            else:
                self.SetDnsRecords([[ hostName, mac]],True)
                self.MacHostDic = self.utl.SetHostNames( {mac:hostName} )

        except Exception as e:
            self.utl.Log(e)

    def LoadLocalHostNames(self):
        connection = None
        hostNames = {}

        try:            
            import sqlite3
            connection = sqlite3.connect(self.utl.GetDB())  

            fields="MAC,NAME"
            query=f"SELECT {fields} FROM MNAME"

            records = connection.execute(query).fetchall()
            hostNames = { r[0] : r[1] for r in records}

            if len(hostNames) > 0:
                hostNames = self.utl.SetHostNames(hostNames)

            connection.close()

        except Exception as e:
            if connection != None:
                connection.close()

            self.utl.Log(e)
        
        return hostNames


    def SetDnsRecords(self, dnsEntries, isLocal = False):
        connection = None
        records = None

        try:            
            import sqlite3
            connection = sqlite3.connect(self.utl.GetDB())  

            tableName = "MName" if isLocal else "DName"
            fieldName = "MAC" if isLocal else "IP"

            sql = f"INSERT OR REPLACE INTO {tableName}(NAME, {fieldName}) VALUES(?,?)"
 
            cursor = connection.cursor()
            
            cursor.executemany(sql, dnsEntries)

            connection.commit()
            connection.close()

        except Exception as e:
            if connection != None:
                connection.rollback()
                connection.close()

            self.utl.Log(e)
        
        return records

