import requests
import numpy as np
from datetime import datetime, timedelta
import WhiteStat.Common.Utility as UTL
import WhiteStat.NetMonitor.RemoteServer as RS

LOCAL_IP_SET = 0
REMOTE_IP_SET = 1

class Analyzer:

    def __init__(self):

        self.utl = UTL.Utility.getInstance()
        self.remoteManager = RS.RemoteManager()
        self.IpMacDic = self.utl.GetIpMacDict()
        self.MacMacDic = self.utl.GetMacMacDict()
        self.MacHostDic = self.utl.GetMacHostDict()


    def ReplaceMACs(self, mac, ip):
        new_mac = self.IpMacDic.get(ip, mac)
        new_mac = self.MacMacDic.get(new_mac, new_mac)

        return new_mac


    def GetNowUtc(self):
        #return (datetime.utcnow().date()+ timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        return datetime.now().date().strftime("%Y-%m-%d %H:%M:%S")
        
    def ConvertToKB(self, bytes):
        try:
            return round(float(str(bytes).replace(",","")) / (1024),2)
        except Exception as e:
            print(bytes)
            raise

    def DiscardRoutersForLocalIP(self, frame):

        def CheckRouterIP(mac,ip):     
            ipInLan = list(filter(lambda x: ip.startswith(x), self.utl.GetLANSegments()))    
            macOfRouter = list(filter(lambda x: mac.startswith(x), self.utl.GetLANRouters()))

            if ((not (ipInLan is None )) and 
                (len(ipInLan) > 0) and 
                (not (macOfRouter is None )) and 
                (len(macOfRouter) > 0)) :
                return True
            
            return False;

        #frame.loc[frame.IP == "192.168.1.21", 'MAC'] = "f8:c4:f3:50:53:68"
        frame["routerFlag"]= frame.apply(lambda x: CheckRouterIP(x.MAC, x.IP), axis=1)
        frame.drop(frame[frame.routerFlag == True].index, inplace = True) 
        frame.drop(["routerFlag"], axis=1, inplace=True)

    def GetUsageFrame(self,date):
        try:
            self.remoteManager.connect()
            curFrame = self.remoteManager.RemoteUsageFrame()
            usageFrame = curFrame.GetFrame()

            if usageFrame is None:
                    return None
            
            usageBytes =  [[key] + value + [True] for key, value in usageFrame[LOCAL_IP_SET].items()]  
            usageBytes += [[key] + value + [False] for key, value in usageFrame[REMOTE_IP_SET].items()]

            usageBytes = np.array(usageBytes)

            if usageBytes is None or len(usageBytes) <= 0:
                    return None

 

            #filterV4 = usageBytes['IP'].str.contains("([\d]+\.){3,3}\d+")    
            filterV4 = usageBytes['IP'].str.contains(self.utl.GetIPFilter())    
            usageBytes.drop(usageBytes[~filterV4].index, inplace = True) 


            updMac= usageBytes.apply(lambda x: self.ReplaceMACs(x.MAC, x.IP), axis=1)

            now = datetime.now()
            lastSeen = usageBytes["Last seen"].apply(lambda x: self.ConvertLastSeen(now, x))

            kbIn = usageBytes["In"].apply(lambda x: self.ConvertToKB(x))
            kbOut = usageBytes["Out"].apply(lambda x: self.ConvertToKB(x))

            usageBytes.drop(usageBytes.columns[[2,3,4,5,6]], axis=1, inplace=True)
            usageBytes.insert(2, "MAC", updMac, True)
            usageBytes.insert(3,"LastSeen",lastSeen,True)
            usageBytes.insert(4,"KBIn",kbIn,True)
            usageBytes.insert(5,"KBOut",kbOut,True)

            utcDate=self.GetNowUtc()
            usageBytes.insert(6, "DATE", utcDate, allow_duplicates=True)

            usageBytes.drop(usageBytes[(usageBytes.LastSeen == 0)].index, inplace = True)
            usageBytes.drop(usageBytes[(usageBytes.LastSeen.str.strip() == "0")].index, inplace = True)

            usageBytes['DT_LastSeen'] = pd.to_datetime(usageBytes['LastSeen'], format='%Y-%m-%d %H:%M:%S')

            curDate = (date - timedelta(seconds=24 * 60 * 60))

            usageBytes.drop(usageBytes[usageBytes.DT_LastSeen < curDate].index, inplace = True) 

            usageBytes.drop(["DT_LastSeen"], axis=1, inplace=True)

            self.utl.AssignRouterLanSegments(usageBytes[['IP','MAC']])

            self.DiscardRoutersForLocalIP(usageBytes)

            return usageBytes
        except Exception as e:
            self.utl.Log(e)
            return None

    def GetDayFirstFrame(self, date, prevDateUsageFrame):
        try:

            startUsageFrame = self.GetUsageFrame(date)    

            if startUsageFrame is None:
                return (None,None, prevDateUsageFrame)    

            ##Get last day LSTDAY values from PrevDataUsageFrame
            if not (prevDateUsageFrame is None) and not (prevDateUsageFrame.empty):

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
                startUsageFrame.insert(0, "LSTDAY_KBIn", 0, allow_duplicates=True) 
                startUsageFrame.insert(1, "LSTDAY_KBOut", 0, allow_duplicates=True) 
                startUsageFrame["LSTDAY_KBIn"] = startUsageFrame["KBIn"]
                startUsageFrame["LSTDAY_KBOut"] = startUsageFrame["KBOut"]
                startUsageFrame["KBOut"] -= startUsageFrame["LSTDAY_KBOut"] 
                startUsageFrame["KBIn"] -= startUsageFrame["LSTDAY_KBIn"]
        
            return (startTimeFrame,startUsageFrame, prevDateUsageFrame)
        except Exception as e:
            self.utl.Log(e)
            return (None,None, prevDateUsageFrame)

    def StabilizeIP(self, date, prevFrame, frame):
        def CheckLanSegment(mac,ip):     
            ipInLan = list(filter(lambda x: ip.startswith(x), self.utl.GetLANSegments()))    

            if ((not (ipInLan is None )) and (len(ipInLan) > 0)) :
                return True
            
            return False;

        #frame.loc[frame.IP == "192.168.1.21", 'MAC'] = "f8:c4:f3:50:53:68"
        oldFrame = prevFrame
        prevFrame = prevFrame[["IP","MAC", "LSTDAY_KBIn","LastSeen"]]     
        prevFrame["lanFlag"]= prevFrame.apply(lambda x: CheckLanSegment(x.MAC, x.IP), axis=1)  
        prevFrame = prevFrame[prevFrame.lanFlag == True] 
        prevFrame.rename(columns = {'IP':'IP_OLD',"LastSeen":"LastSeen_OLD"}, inplace = True)
        
        frame = frame[["IP","MAC","KBIn","LastSeen"]]
        frame["lanFlag"]= frame.apply(lambda x: CheckLanSegment(x.MAC, x.IP), axis=1)
        frame = frame[frame.lanFlag == True]

        #frame.loc[frame.IP == "192.168.1.21", 'MAC'] = "f8:c4:f3:50:53:68"

        newFrame = prevFrame.merge(frame, on=['MAC'], how ="inner")

        prevFrame.rename(columns = {'IP_OLD':'IP', "LastSeen_OLD":"LastSeen"}, inplace = True)

        dic = {}
    
        def ReMapIpMac(mac,ip_old,new_ip):
            dic[f"{mac},{ip_old}"] = new_ip
            return None

        newFrame = newFrame[(newFrame.IP != newFrame.IP_OLD)]
        
        if not(newFrame is None or newFrame.empty):
            newFrame.apply(lambda x: ReMapIpMac(x.MAC,x.IP_OLD,x.IP),axis=1)

        updIP= oldFrame.apply(lambda x: dic.get(f"{x.MAC},{x.IP}",x.IP), axis=1)

        oldFrame.drop(["IP"], axis=1, inplace=True)
        oldFrame.insert(0, "IP", updIP, True)

        return self.EnsureIP_MAC_Combo(date, oldFrame,"From StabilizeIP",fix=True)

    
    def GetDayNextFrame(self, date, prevTimeFrame, prevUsageFrame):
        try:
            startTimeFrame = prevTimeFrame
            startUsageFrame = prevUsageFrame
            nextTimeFrame = self.RunningFor()

            if nextTimeFrame is None:
                return (None, None)

            nextUsageFrame = self.GetUsageFrame(date)  
            
            if nextUsageFrame is None:
                return (None, None)

            if startUsageFrame is None:
                return (nextTimeFrame,nextUsageFrame)
    

            startUsageFrame = self.StabilizeIP(date, startUsageFrame, nextUsageFrame)

            nextUsageFrame.rename(columns = {'LastSeen':'LastSeen_NXT'}, inplace = True)
            nextUsageFrame.rename(columns = {'KBIn':'KBIn_NXT'}, inplace = True)
            nextUsageFrame.rename(columns = {'KBOut':'KBOut_NXT'}, inplace = True)
            nextUsageFrame.rename(columns = {'Hostname':'Hostname_NXT'}, inplace = True)
            #nextUsageFrame.rename(columns = {'DATE':'DATE_NXT'}, inplace = True)

            newUsageFrame = nextUsageFrame.merge(startUsageFrame, on=['IP', 'MAC', 'DATE'], how ="outer")

            #self.EnsureIP_MAC_Combo(newUsageFrame,"From GetDayNextFrame, Just after Merge")
            
            #for new records from Server, Start the Meter as new with same returned bytes
            # (will happen below while adding the bytes)
            #records exists newly in server, and not in local
            newUsageFrame.fillna(value={'LSTDAY_KBIn': 0.0, 'LSTDAY_KBOut': 0.0, 'KBIn': 0.0, 'KBOut': 0.0}, inplace=True)
                       
            #If the records already existing, update last seen and date, to reflect recent
            #New Rows
            newUsageFrame['LastSeen'].fillna(newUsageFrame['LastSeen_NXT'],inplace=True)
            newUsageFrame['Hostname'].fillna(newUsageFrame['Hostname_NXT'],inplace=True)
   
            newUsageFrame.loc[(pd.notna(newUsageFrame.Hostname_NXT)) &
            (pd.notna(newUsageFrame.Hostname)), 'Hostname'] = newUsageFrame["Hostname_NXT"]

            #newUsageFrame.loc[(pd.notna(newUsageFrame.DATE_NXT)) &
            #(pd.notna(newUsageFrame.DATE)), 'DATE'] = newUsageFrame["DATE_NXT"] 
                        
            #for old records in local, retain the same value (will happen below while adding the bytes)
            #records exists only in local, and no more in server
            newUsageFrame.loc[pd.isna(newUsageFrame.KBIn_NXT), 'KBIn_NXT'] = newUsageFrame.LSTDAY_KBIn
            newUsageFrame.loc[pd.isna(newUsageFrame.KBOut_NXT), 'KBOut_NXT'] = newUsageFrame.LSTDAY_KBOut  
                        
            #if nextTimeFrame[1] >= startTimeFrame[1]:    
            #    newUsageFrame["KBIn"] += newUsageFrame["KBIn_NXT"] - newUsageFrame["LSTDAY_KBIn"]
            #    newUsageFrame["KBOut"] += newUsageFrame["KBOut_NXT"] - newUsageFrame["LSTDAY_KBOut"]
            #else:
            #    newUsageFrame["KBIn"] += newUsageFrame["KBIn_NXT"]
            #    newUsageFrame["KBOut"] += newUsageFrame["KBOut_NXT"]

            newUsageFrame.loc[
                    newUsageFrame.KBIn_NXT >= newUsageFrame.LSTDAY_KBIn  ,
                    'KBIn'] += newUsageFrame.KBIn_NXT - newUsageFrame.LSTDAY_KBIn
            newUsageFrame.loc[
                    newUsageFrame.KBOut_NXT >= newUsageFrame.LSTDAY_KBOut  ,
                    'KBOut'] += newUsageFrame.KBOut_NXT - newUsageFrame.LSTDAY_KBOut

            newUsageFrame.loc[
                    newUsageFrame.KBIn_NXT < newUsageFrame.LSTDAY_KBIn  ,
                    'KBIn'] += newUsageFrame.KBIn_NXT
            newUsageFrame.loc[
                    newUsageFrame.KBOut_NXT < newUsageFrame.LSTDAY_KBOut  ,
                    'KBOut'] += newUsageFrame.KBOut_NXT

            newUsageFrame["LSTDAY_KBIn"] = newUsageFrame["KBIn_NXT"]
            newUsageFrame["LSTDAY_KBOut"] = newUsageFrame["KBOut_NXT"]

            newUsageFrame.drop('KBIn_NXT', inplace=True, axis=1)
            newUsageFrame.drop('KBOut_NXT', inplace=True, axis=1)        
            
            newUsageFrame = self.EnsureIP_MAC_Combo(date, newUsageFrame,"From GetDayNextFrame, Just Before Return",fix=True)

            #New Rows, Existing Rows match. Inner Join, make the values recent
            newUsageFrame.loc[(pd.notna(newUsageFrame.LastSeen_NXT)) &
            (pd.notna(newUsageFrame.LastSeen)), 'LastSeen'] = newUsageFrame["LastSeen_NXT"]
      
            newUsageFrame.fillna(value={'Hostname': "(none)"}, inplace=True)

            newUsageFrame.drop('Hostname_NXT', inplace=True, axis=1)
            newUsageFrame.drop('LastSeen_NXT', inplace=True, axis=1)
            #newUsageFrame.drop('DATE_NXT', inplace=True, axis=1)                        

            return (nextTimeFrame,newUsageFrame)
        
        except Exception as e:
            self.utl.Log(e)
            return (None,None)
    
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