import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import WhiteStat.Common.Utility as UTL
import WhiteStat.NetMonitor.RemoteServer as RS
import numpy.lib.recfunctions as NF

LOCAL_IP_SET = 0
REMOTE_IP_SET = 1

class Analyzer:

    def __init__(self):

        self.utl = UTL.Utility.getInstance()
        self.remoteManager = RS.RemoteManager()
        self.IpMacDic = self.utl.GetIpMacDict()
        self.MacMacDic = self.utl.GetMacMacDict()
        self.MacHostDic = self.utl.GetMacHostDict()


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

        frame = self.AddField(frame, "routerFlag","i8",False)
        #frame.loc[frame.IP == "192.168.1.21", 'MAC'] = "f8:c4:f3:50:53:68"

        fnCheckRouterFlg = np.vectorize(CheckRouterIP)
        frame["routerFlag"] = fnCheckRouterFlg(frame["MAC"])
        frame = frame[ (frame["routerFlag"] == False) | (frame["LOCAL"] == False) ]
        frame = NF.drop_fields(frame, ['routerFlag'])
        return frame

    def BuildFrame(self, usageList):
        
        dtypes =[
                    ('IP', 'i8'),
                    ('MAC', 'i8'),
                    ('IN', 'f8'),
                    ('OUT', 'f8'),
                    ('SEEN', 'M8[ms]'),
                    ('LOCAL', 'i8')
                    ]            
        return np.array(usageList, dtype=dtypes)


    def GetUsageFrame(self,date):
        try:
            self.remoteManager.connect()
            curFrame = self.remoteManager.RemoteUsageFrame()
            usageFrame = curFrame.GetFrame()

            if usageFrame is None:
                    return None            
            
            localIPs =  [tuple([self.utl.IpToHash(value[0])] + [key] + value[1:] + [True]) for key, value in usageFrame[LOCAL_IP_SET].items()]  

            localUsageBytes = self.BuildFrame(localIPs)

            remoteIps = [tuple([self.utl.IpToHash(key)] + value + [False]) for key, value in usageFrame[REMOTE_IP_SET].items()]

            remoteUsageBytes = self.BuildFrame(remoteIps)

            usageFrame = np.concatenate((localUsageBytes, remoteUsageBytes), axis=0)

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
            if not (prevUsageFrame is None) and not (prevUsageFrame.empty):

                prevDateUsageFrame = self.StabilizeIP(date, prevDateUsageFrame, startUsageFrame)

                prevSubFrame = prevDateUsageFrame[["IP", "MAC", "LSTDAY_KBIn","LSTDAY_KBOut"]]
                startUsageFrame = startUsageFrame.merge(prevSubFrame, on=['IP', 'MAC'], how ="left")

                startUsageFrame = self.EnsureIP_MAC_Combo(date, startUsageFrame,"From GetDayFirstFrame",fix=True)

                startUsageFrame.fillna(value={'LSTDAY_KBIn': 0.0, 'LSTDAY_KBOut': 0.0}, inplace=True)
                
                startUsageFrame.loc[
                    startUsageFrame.KBIn < startUsageFrame.LSTDAY_KBIn  ,
                    'LSTDAY_KBIn'] = startUsageFrame.KBIn

                startUsageFrame.loc[
                    startUsageFrame.KBOut < startUsageFrame.LSTDAY_KBOut  ,
                    'LSTDAY_KBOut'] = startUsageFrame.KBOut

                kbIn = startUsageFrame["KBIn"].apply(lambda x: x)
                kbOut = startUsageFrame["KBOut"].apply(lambda x: x)

                startUsageFrame.loc[
                    startUsageFrame.KBIn >= startUsageFrame.LSTDAY_KBIn  ,
                    'KBIn'] = startUsageFrame["KBIn"] - startUsageFrame["LSTDAY_KBIn"]

                startUsageFrame.loc[
                    startUsageFrame.KBOut >= startUsageFrame.LSTDAY_KBOut  ,
                    'KBOut'] = startUsageFrame["KBOut"] - startUsageFrame["LSTDAY_KBOut"]

                startUsageFrame.loc[
                    kbIn > startUsageFrame.LSTDAY_KBIn  ,
                    'LSTDAY_KBIn'] = kbIn

                startUsageFrame.loc[
                    kbOut > startUsageFrame.LSTDAY_KBOut  ,
                    'LSTDAY_KBOut'] = kbOut

                prevDateUsageFrame = None
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
                    ('MAC', 'i8'),
                    ('DATE', 'M8[ms]'),
                    ('IP1', 'i8'),
                    ('IP', 'i8'),
                    ('IN', 'f8'),
                    ('IN2', 'f8'),
                    ('OUT', 'f8'),
                    ('OUT2', 'f8'),
                    ('SEEN1', 'M8[ms]'),
                    ('SEEN', 'M8[ms]'),
                    ('LOCAL1', 'i8'),
                    ('LOCAL', 'i8'),
                    ('LSTDAY_IN', 'f8'),
                    ('LSTDAY_OUT', 'f8')
                    ]
        else:
            dtypes =[
                    ('IP', 'i8'),
                    ('DATE', 'M8[ms]'),
                    ('MAC1', 'i8'),
                    ('MAC', 'i8'),
                    ('IN', 'f8'),
                    ('IN2', 'f8'),
                    ('OUT', 'f8'),
                    ('OUT2', 'f8'),
                    ('SEEN1', 'M8[ms]'),
                    ('SEEN', 'M8[ms]'),
                    ('LOCAL1', 'i8'),
                    ('LOCAL', 'i8'),
                    ('LSTDAY_IN', 'f8'),
                    ('LSTDAY_OUT', 'f8')
                    ]
        return np.array(usageList, dtype=dtypes)

    def ProcessMergedFrame(self, frame, isLocal = True):
        mask = frame.mask
        data = frame.data

        isNull = True
        #2 is New, 1 is Old. i.e. IP1 is old IP2 is new
        bothInOldNew = ( (mask["SEEN2"] != isNull) & (mask["SEEN1"] != isNull) )
        OnlyInOld = ( (mask["SEEN2"] == isNull) )
        OnlyInNew = ( (mask["SEEN1"] == isNull) )


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

        higherInCond = ( data["IN2"] >= data["LSTDAY_IN"] )
        data["IN1"][higherInCond] += (data["IN2"][higherInCond] - data["LSTDAY_IN"][higherInCond])

        higherOutCond = ( data["OUT2"] >= data["LSTDAY_OUT"] )
        data["OUT1"][higherOutCond] += (data["OUT2"][higherOutCond] - data["LSTDAY_OUT"][higherOutCond])

        lowerInCond = ( data["IN2"] < data["LSTDAY_IN"] )
        data["IN1"][lowerInCond] += data["IN2"][lowerInCond]

        lowerOutCond = ( data["OUT2"] < data["LSTDAY_OUT"] )
        data["OUT1"][lowerOutCond] += data["OUT2"][lowerOutCond]

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

        def ConvertToIPString(ipInt):
            return self.utl.UnPackIPPackedIntToString(ipInt)
        
        def ConvertToMACString(macInt):
            return self.utl.UnPackPackedIntToString(macInt)

        fnIPString = np.vectorize(ConvertToIPString)
        fnMACString = np.vectorize(ConvertToMACString)
        fnHashToIp = np.vectorize(self.utl.HashToIp)

        newFrame = self.AddField(newFrame, "MAC1","U100","")
        newFrame = self.AddField(newFrame, "IP1","U100","")
        newFrame["MAC1"]=fnMACString(newFrame["MAC"])
        newFrame["IP1"]=fnIPString(fnHashToIp(newFrame["IP"]))
        newFrame = NF.drop_fields(newFrame, ['IP','MAC'])
        np.set_printoptions(suppress=True)
        return newFrame

    def EnsureIP_MAC_Combo(self,date, frame, msg=None,fix=False):

        self.DiscardRoutersForLocalIP(frame)

        frame.drop(frame[(frame.LastSeen == 0)].index, inplace = True)
        frame.drop(frame[(frame.LastSeen.str.strip() == "0")].index, inplace = True)
        frame['DT_LastSeen'] = pd.to_datetime(frame['LastSeen'], format='%Y-%m-%d %H:%M:%S')
        curDate = (date - timedelta(seconds=24 * 60 * 60))
        frame.drop(frame[frame.DT_LastSeen < curDate].index, inplace = True) 

        group=frame[['IP','MAC','DATE', 'LastSeen']].groupby(['IP','MAC','DATE'])
        duplicates = group.count()
        duplicates=duplicates[duplicates.LastSeen > 1]

        if (not (duplicates is None)) and (not (duplicates.empty)) and  duplicates.shape[0] > 0:
            if not fix:                
                raise Exception(f'Multiple Same IP/MAC combination, Critical error:{msg}')
            else:
                self.utl.Trace(msg)

                group=frame[['IP','MAC','DATE', 'DT_LastSeen']].groupby(['IP','MAC','DATE'])                
                maxDate=group["DT_LastSeen"].max().to_frame(name = 'DT_LastSeen_Max').reset_index()               

                newFrame = maxDate.merge(frame, on=['IP','MAC','DATE'], how ="left")

                newFrame.drop(newFrame[newFrame.DT_LastSeen < newFrame.DT_LastSeen_Max].index, inplace = True) 
                newFrame.drop_duplicates(subset=['IP','MAC','DATE'], keep='last',inplace=True)

                newFrame.drop('DT_LastSeen_Max', inplace=True, axis=1)
                newFrame.drop('DT_LastSeen', inplace=True, axis=1)
                return newFrame
        else:
            return frame;


    def PersistToDailyDB(self, timeframe, frame, utcDate):
        connection = None
        try:            
            import sqlite3
            connection = sqlite3.connect(self.utl.GetDB())

            connection.execute(f"DELETE FROM timeframe WHERE date([DATE]) >= date('{utcDate}')")
            connection.execute(f"DELETE FROM dailyusage WHERE date([DATE]) >= date('{utcDate}')")

            connection.execute(f"INSERT INTO timeframe(DATE,LastSeen) VALUES('{timeframe[0]}',{timeframe[1]})")
            frame[['IP', 'MAC','Hostname', 'LastSeen','KBIn', 'KBOut', 'DATE',
            'LSTDAY_KBIn', 'LSTDAY_KBOut']].to_sql('dailyusage', con=connection, if_exists='append',index=False)
            connection.commit()
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

            connection.execute("DELETE FROM usagehistory WHERE (IP,MAC,DATE) IN "
                               "(SELECT IP,MAC,[DATE] "
                               "FROM dailyusage "
                               f"WHERE date([DATE]) < date('{utcDate}'))"
                               )
            
            connection.execute(
                "INSERT INTO usagehistory(IP,MAC,Hostname,LastSeen,KBIn,KBOut,[DATE],LSTDAY_KBIn,LSTDAY_KBOut) "
                "SELECT IP,MAC,Hostname,LastSeen,KBIn,KBOut,[DATE],LSTDAY_KBIn,LSTDAY_KBOut "
                f"FROM dailyusage WHERE date([DATE]) < date('{utcDate}') AND "
                "(IP,MAC,DATE) NOT IN (SELECT IP,MAC,DATE FROM usagehistory)")

            connection.execute(f"DELETE FROM dailyusage WHERE date([DATE]) < date('{utcDate}')")            
            connection.execute(f"DELETE FROM timeframe WHERE date([DATE]) < date('{utcDate}')")

            connection.commit()
            connection.close()
        except Exception as e:
            if connection != None:
                connection.rollback()
                connection.close()

            self.utl.Log(e)


    def ValidateDate(self, date_text):
        try:
            datetime.strptime(date_text, '%Y-%m-%d %H:%M:%S')
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

            if not (prevTimeframe is None) and self.ValidateDate(str(prevTimeframe[0])):
                prevDate = prevTimeframe[0]

                cursor = connection.execute(f"SELECT IP, MAC, Hostname, LastSeen, KBIn, KBOut, DATE, LSTDAY_KBIn, LSTDAY_KBOut, IS_LOCAL "
                " FROM dailyusage WHERE date(DATE)=date('{prevDate}')")

                results = cursor.fetchall()                
                prevFrame = np.array(list(results))

            cursor = connection.execute(f"SELECT COUNT(*) AS CNT FROM dailyusage WHERE date(DATE)=date('{today}')")            
            #cursor = connection.execute(f"SELECT COUNT(*) AS CNT FROM dailyusage") 
            count=int(cursor.fetchone()[0])
            cursor.close()



            if count > 0:
                cursor = connection.execute(f"SELECT IP, MAC, Hostname, LastSeen, KBIn, KBOut, DATE, LSTDAY_KBIn, LSTDAY_KBOut, IS_LOCAL "
                f" FROM dailyusage WHERE date(DATE)=date('{today}')")

                results = cursor.fetchall()                
                frame = np.array(list(results))

            connection.close()

        except Exception as e:
            if connection != None:
                connection.close()

            self.utl.Log(e)
        
        return (frame,prevFrame)


    def ReplaceHostName(self, frame):

        def LookupHost(mac,hostname):
            return self.MacHostDic.get(mac,hostname)        

        updHost= frame.apply(lambda x: LookupHost(x.MAC,x.Hostname), axis=1)
        frame.drop(["Hostname"], axis=1, inplace=True)
        frame.insert(2, "Hostname", updHost, True)

    def GetDailyUsageRecords(self):
        connection = None
        frame = None
        timeframe = None
        try:            
            import sqlite3
            connection = sqlite3.connect(self.utl.GetDB())  

            utcDate=self.GetNowUtc()

            cursor = connection.execute(f"SELECT DATE,LastSeen AS CNT FROM timeframe WHERE date(DATE)=date('{utcDate}')")
            #cursor = connection.execute(f"SELECT DATE,LastSeen AS CNT FROM timeframe")
            timeframe = cursor.fetchone()
            cursor.close()

            cursor = connection.execute(f"SELECT COUNT(*) AS CNT FROM dailyusage WHERE date(DATE)=date('{utcDate}')")            
            #cursor = connection.execute(f"SELECT COUNT(*) AS CNT FROM dailyusage") 
            count=int(cursor.fetchone()[0])
            cursor.close()

            if count > 0:
                fields="IP,MAC,Hostname,LastSeen,KBIn,KBOut,[DATE],LSTDAY_KBIn,LSTDAY_KBOut"
                frame=pd.read_sql_query(f"SELECT {fields} FROM dailyusage WHERE date(DATE)=date('{utcDate}') ORDER BY KBIn DESC", con=connection)
                frame.fillna(value={'LSTDAY_KBIn': 0.0, 'LSTDAY_KBOut': 0.0},inplace=True)
                #frame=pd.read_sql_query(f"SELECT * FROM dailyusage", con=connection)
                self.ReplaceHostName(frame)

            connection.close()

        except Exception as e:
            if connection != None:
                connection.close()

            self.utl.Log(e)
        
        return (timeframe,frame)
            
    def GetHistoricRecords(self, startDate, endDate):
        connection = None
        frame = None
        try:            
            import sqlite3
            connection = sqlite3.connect(self.utl.GetDB())  

            dateCondition = f"(date(DATE) >= date('{startDate}') AND date(DATE) <= date('{endDate}'))"
            fields="IP,MAC,Hostname,LastSeen,KBIn,KBOut,[DATE],LSTDAY_KBIn,LSTDAY_KBOut"
            selectQuery = (f"SELECT {fields} FROM (SELECT {fields} FROM dailyusage WHERE {dateCondition} UNION "
                           f"SELECT {fields} FROM usagehistory WHERE ({dateCondition} AND (IP,MAC,DATE) NOT IN "
                           f"(SELECT IP,MAC,DATE FROM dailyusage))) ORDER BY DATE DESC, KBIn DESC")

  
            frame=pd.read_sql_query(selectQuery, con=connection)

            if not (frame is None) and not frame.empty:
                frame.fillna(value={'LSTDAY_KBIn': 0.0, 'LSTDAY_KBOut': 0.0},inplace=True)
                self.ReplaceHostName(frame)
                
            connection.close()

        except Exception as e:
            if connection != None:
                connection.close()

            self.utl.Log(e)
        
        return frame