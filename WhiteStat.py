import requests
import pandas as pd
from datetime import datetime, timedelta
import WhiteStatUtils as UTL

class WhiteStat:

    def __init__(self):

        self.utl = UTL.WhiteStatUtils.getInstance()
        self.url = self.utl.GetUrl()
        self.IpMacDic = self.utl.GetIpMacDict()
        self.MacMacDic = self.utl.GetMacMacDict()
        self.MacHostDic = self.utl.GetMacHostDict()

    def GetTotalSeconds(self, match_object):
        try:
            totalSecs = 0         
            
            if not (match_object.group('DAY') is None):
                totalSecs += 24 * 60 * 60 * int(match_object.group('DAY'))
            if not (match_object.group('HRS')  is None):
                totalSecs += 60 * 60 * int(match_object.group('HRS'))
            if not (match_object.group('MIN')  is None):
                totalSecs += 60 * int(match_object.group('MIN'))
            if not (match_object.group('SEC') is None):
                totalSecs += int(match_object.group('SEC'))

            return totalSecs
        except Exception as e:
            self.utl.Log(e)
            return 0

    def RunningFor(self):

        import re 
        try:

            page = requests.get(self.url)
            x=page.text

            if x == '(never)':
                return (None,None)
            
            match_object = re.search(
                (r"((?P<DAY>\d+) days?, )?((?P<HRS>\d+) hrs?, )?((?P<MIN>\d+) mins?, )?" 
                r"((?P<SEC>\d+) secs?).*since[^\d]*(?P<DTE>\d+\-\d+\-\d+ \d+:\d+:\d+)"),
                x)     
                
            totalSecs = self.GetTotalSeconds(match_object)
            dateSince = match_object.group('DTE')

            dateSince=self.GetNowUtc()

            return (dateSince, totalSecs)
        
        except Exception as e:
            self.utl.Log(e)
            return (None,None)


    def ConvertLastSeen(self, date, x):
        import re 
        try:
            if x == '(never)':
                return 0
            
            match_object = re.match(r'((?P<DAY>\d+) days?, )?((?P<HRS>\d+) hrs?, )?((?P<MIN>\d+) mins?, )?((?P<SEC>\d+) secs?)', x)     

            totalSecs = self.GetTotalSeconds(match_object)
            
            return  (date + timedelta(seconds=totalSecs)).strftime("%Y-%m-%d %H:%M:%S")
        
        except Exception as e:
            self.utl.Log(e)
            return 0

    def ReplaceMACs(self, mac, ip):
        new_mac = self.IpMacDic.get(ip, mac)
        new_mac = self.MacMacDic.get(new_mac, new_mac)

        return new_mac

    #def CustomIPMACProcess(self, df):        
        
        #df["MAC"].replace(self.MacMacDic, inplace=True)
        #df["MAC"].where(df.IP in self.IpMacDic,self.IpMacDic.get(df.IP),inplace=True)
        #df.loc[df.IP  in  self.IpMacDic, 'MAC'] =  self.IpMacDic[df['IP']]

        #df.loc[df['MAC'] == "b8:27:eb:8c:dc:bb", 'MAC'] = "f8:c4:f3:50:53:68"
        #df.loc[df.IP == "192.168.1.54", 'MAC'] = "52:54:00:f3:a3:2b"

    def GetNowUtc(self):
        #return (datetime.utcnow().date()+ timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        return datetime.utcnow().date().strftime("%Y-%m-%d %H:%M:%S")
        
    def ConvertToKB(self, bytes):
        try:
            return round(float(str(bytes).replace(",","")) / (1024),2)
        except Exception as e:
            print(bytes)
            raise

    def GetUsageFrame(self):
        try:
            usage_data = pd.read_html(f'{self.url}/hosts/?full=yes&sort=in', header=None)

            if usage_data is None:
                    return None

            usageBytes = usage_data[0]
            #usageBytes.columns.values

            if usage_data is None or usageBytes.empty:
                    return None

            if usageBytes.columns[0] != "IP":
                usageBytes.columns = [
                    "IP",
                    "Hostname",
                    "MAC Address",
                    "In",
                    "Out",
                    "Total",
                    "Last seen"]


            usageBytes.rename(columns={"MAC Address": "MAC"},inplace=True) 

            usageBytes.drop(usageBytes[usageBytes.IP == "IP"].index, inplace = True) 

            #filterV4 = usageBytes['IP'].str.contains("([\d]+\.){3,3}\d+")    
            filterV4 = usageBytes['IP'].str.contains(self.utl.GetIPFilter())    
            usageBytes.drop(usageBytes[~filterV4].index, inplace = True) 


            updMac= usageBytes.apply(lambda x: self.ReplaceMACs(x.MAC, x.IP), axis=1)

            now = datetime.utcnow()
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

            return usageBytes
        except Exception as e:
            self.utl.Log(e)
            return None

    def GetDayFirstFrame(self, prevDateUsageFrame):
        try:
            startTimeFrame = self.RunningFor()

            if startTimeFrame is None:
                return (None,None, prevDateUsageFrame)

            startUsageFrame = self.GetUsageFrame()    

            if startUsageFrame is None:
                return (None,None, prevDateUsageFrame)    

            ##Get last day LSTDAY values from PrevDataUsageFrame
            if not (prevDateUsageFrame is None) and not (prevDateUsageFrame.empty):
                prevSubFrame = prevDateUsageFrame[["IP", "MAC","LSTDAY_KBIn","LSTDAY_KBOut"]]
                startUsageFrame = startUsageFrame.merge(prevSubFrame, on=['IP', 'MAC'], how ="left")
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
                    startUsageFrame.KBIn > startUsageFrame.LSTDAY_KBIn  ,
                    'KBIn'] = startUsageFrame["KBIn"] - startUsageFrame["LSTDAY_KBIn"]

                startUsageFrame.loc[
                    startUsageFrame.KBOut > startUsageFrame.LSTDAY_KBOut  ,
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

    def StabilizeIP(self, prevFrame, frame):
        oldFrame = prevFrame
        prevFrame = prevFrame[["IP","MAC", "LSTDAY_KBIn"]]
        prevFrame.rename(columns = {'MAC':'MAC_OLD'}, inplace = True)

        frame = frame[["IP","MAC", "KBIn"]]

        #frame.loc[frame.IP == "192.168.1.21", 'MAC'] = "f8:c4:f3:50:53:68"

        newFrame = prevFrame.merge(frame, on=['IP'], how ="inner")

        prevFrame.rename(columns = {'MAC_OLD':'MAC'}, inplace = True)

        dic = {}
    
        def ReMapIpMac(ip,mac):
            dic[ip] = mac
            return None

        newFrame = newFrame[
            (newFrame.MAC != newFrame.MAC_OLD) &
            (newFrame.KBIn >= newFrame.LSTDAY_KBIn)]
        
        if not(newFrame is None or newFrame.empty):
            newFrame.apply(lambda x: ReMapIpMac(x.IP, x.MAC),axis=1)

        updMac= oldFrame.apply(lambda x: dic.get(x.IP,x.MAC), axis=1)

        oldFrame.drop(["MAC"], axis=1, inplace=True)
        oldFrame.insert(2, "MAC", updMac, True)
        return
    
    def GetDayNextFrame(self, prevTimeFrame, prevUsageFrame):
        try:
            startTimeFrame = prevTimeFrame
            startUsageFrame = prevUsageFrame
            nextTimeFrame = self.RunningFor()

            if nextTimeFrame is None:
                return (None, None)

            nextUsageFrame = self.GetUsageFrame()  
            
            if nextUsageFrame is None:
                return (None, None)

            if startUsageFrame is None:
                return (nextTimeFrame,nextUsageFrame)
    

            self.StabilizeIP(startUsageFrame, nextUsageFrame)

            nextUsageFrame.rename(columns = {'LastSeen':'LastSeen_NXT'}, inplace = True)
            nextUsageFrame.rename(columns = {'KBIn':'KBIn_NXT'}, inplace = True)
            nextUsageFrame.rename(columns = {'KBOut':'KBOut_NXT'}, inplace = True)
            nextUsageFrame.rename(columns = {'Hostname':'Hostname_NXT'}, inplace = True)
            nextUsageFrame.rename(columns = {'DATE':'DATE_NXT'}, inplace = True)

            newUsageFrame = nextUsageFrame.merge(startUsageFrame, on=['IP', 'MAC'], how ="outer")

            #for new records from Server, Start the Meter as new with same returned bytes
            # (will happen below while adding the bytes)
            #records exists newly in server, and not in local
            newUsageFrame.fillna(value={'LSTDAY_KBIn': 0.0, 'LSTDAY_KBOut': 0.0, 'KBIn': 0.0, 'KBOut': 0.0}, inplace=True)
            newUsageFrame['LastSeen'].fillna(newUsageFrame['LastSeen_NXT'],inplace=True)
            newUsageFrame['Hostname'].fillna(newUsageFrame['Hostname_NXT'],inplace=True)

            newUsageFrame.loc[pd.isna(newUsageFrame.Hostname), 'Hostname'] = newUsageFrame["Hostname_NXT"]
            newUsageFrame.loc[pd.isna(newUsageFrame.LastSeen), 'LastSeen'] = newUsageFrame["LastSeen_NXT"]
            newUsageFrame.loc[pd.isna(newUsageFrame.DATE), 'DATE'] = newUsageFrame["DATE_NXT"]

            newUsageFrame.drop('Hostname_NXT', inplace=True, axis=1)
            newUsageFrame.drop('LastSeen_NXT', inplace=True, axis=1)
            newUsageFrame.drop('DATE_NXT', inplace=True, axis=1)

            #for old records in local, retain the same value (will happen below while adding the bytes)
            #records exists only in local, and no more in server
            newUsageFrame.loc[pd.isna(newUsageFrame.KBIn_NXT), 'KBIn_NXT'] = newUsageFrame.LSTDAY_KBIn
            newUsageFrame.loc[pd.isna(newUsageFrame.KBOut_NXT), 'KBOut_NXT'] = newUsageFrame.LSTDAY_KBOut   
            
            newUsageFrame.fillna(value={'Hostname': "(none)"}, inplace=True)


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
            
            return (nextTimeFrame,newUsageFrame)
        
        except Exception as e:
            self.utl.Log(e)
            return (None,None)
    

    def PersistToDailyDB(self, timeframe, frame):
        connection = None
        try:            
            import sqlite3
            connection = sqlite3.connect(self.utl.GetDB())

            connection.execute("DELETE FROM timeframe")
            connection.execute("DELETE FROM dailyusage")

            connection.execute(f"INSERT INTO timeframe(DATE,LastSeen) VALUES('{timeframe[0]}',{timeframe[1]})")
            frame[['IP', 'MAC','Hostname', 'LastSeen','KBIn', 'KBOut', 'DATE',
            'LSTDAY_KBIn', 'LSTDAY_KBOut']].to_sql('dailyusage', con=connection, if_exists='replace',index=False)
            connection.commit()
            connection.close()
        except Exception as e:
            if connection != None:
                connection.rollback()
                connection.close()

            self.utl.Log(e)


    def ArchivePrevFrameToDB(self):
        connection = None
        try:            
            import sqlite3
            connection = sqlite3.connect(self.utl.GetDB())  

            utcDate=self.GetNowUtc()

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

            connection.commit()
            connection.close()
        except Exception as e:
            if connection != None:
                connection.rollback()
                connection.close()

            self.utl.Log(e)


    def RestoreFromDailyDB(self):
        connection = None
        frame = None
        prevFrame = None
        timeframe = None
        try:            
            import sqlite3
            connection = sqlite3.connect(self.utl.GetDB())  

            utcDate=self.GetNowUtc()

            prevFrame=pd.read_sql_query(f"SELECT * FROM dailyusage WHERE date(DATE)<date('{utcDate}')", con=connection)

            filterV4 = prevFrame['IP'].str.contains(self.utl.GetIPFilter())    
            prevFrame.drop(prevFrame[~filterV4].index, inplace = True) 

            cursor = connection.execute(f"SELECT DATE,LastSeen AS CNT FROM timeframe WHERE date(DATE)=date('{utcDate}')")
            #cursor = connection.execute(f"SELECT DATE,LastSeen AS CNT FROM timeframe")
            timeframe = cursor.fetchone()
            cursor.close()

            cursor = connection.execute(f"SELECT COUNT(*) AS CNT FROM dailyusage WHERE date(DATE)=date('{utcDate}')")            
            #cursor = connection.execute(f"SELECT COUNT(*) AS CNT FROM dailyusage") 
            count=int(cursor.fetchone()[0])
            cursor.close()

            if count > 0:
                frame=pd.read_sql_query(f"SELECT * FROM dailyusage WHERE date(DATE)=date('{utcDate}')", con=connection)
                frame.fillna(value={'LSTDAY_KBIn': 0.0, 'LSTDAY_KBOut': 0.0},inplace=True)
                filterV4 = frame['IP'].str.contains(self.utl.GetIPFilter())    
                frame.drop(frame[~filterV4].index, inplace = True) 
                #frame=pd.read_sql_query(f"SELECT * FROM dailyusage", con=connection)
                
                #filterV4 = usageBytes['IP'].str.contains("([\d]+\.){3,3}\d+")             

            connection.close()

        except Exception as e:
            if connection != None:
                connection.close()

            self.utl.Log(e)
        
        return (timeframe,frame,prevFrame)


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