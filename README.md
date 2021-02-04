# WhiteStat
Internet/Network Bandwidth Daily Usage Analyser with Historic Data Persistence in a Docker Container. Supports RaspberryPi2/armv7.

![alt UX](https://github.com/avarghesein/WhiteStat/blob/main/UX/UX3.png)

Pull & Run: [View in DockerHub](https://hub.docker.com/r/avarghesein/whitestat)

      docker run --name whitestat \
      --env DATA_STORE="/mnt/whitestat/" \
      --env DARKSTAT_URL="http://192.168.1.5:777" \
      --env SERVER_PORT=777 \
      --mount type=bind,source="/home/ubuntuuser/whitestat",target="/mnt/whitestat/"  \
      -p 888:777 \
      -d avarghesein/whitestat:v5

# Why Whitestat? 

I have been looking for a Network (Internet) Bandwidth Analyzer, which could easily run on my RaspberryPi hardware with minimal footprint and provides daily statistics which is easy to comprehend in a glance. 

Most of the tools, I came across are much heavier for the purpose and the information shown in the UI is pretty difficult grasp for an average user.
Mostly these tools also store the flow data in every minutes, and your storage could be piled up with Gig(s) of data in a matter of days.

What about a utility, which is minimal enough to smoothly run on a Pi hardware, efficiently uses the storage and yet provide features similar to aformentioned tools? 

## Leveraging DarkStat.

WhiteStat pulls the raw network usage data (per IP and MAC) as the source from [“DarkStat”](https://github.com/TomMichel/darkstat) and 
process for daily usage reporting in every 30 seconds by default, which is then refreshed to a SQLite DB.

## Features

#### 1. Entire Network Usage Analyzer is in a Docker Image and minimal enough to run on a Pi Hardware

#### 2. Provides Daily Usage Levels per individual Host in the Network, Considering DHCP and the same Host could have different IP's on the same day
   
   Note:
   DarkStat, provides cumulative usage levels only per Host/IP (from the day of install), not daily usage levels.

#### 3. Single Responsive Dashboard (UX) to view all the daily/historic statistics. Supports searching/sorting on all usage record fields.

#### 4. Survival of Usage Data, in case of a System Crash (Router/Pi at which DarkStat or WhiteStat is running)
   WhiteStat keeps checkpoints on data usage in every 30 Seconds by default, and use the same as the starting level, when the system comes up.
   DarkStat, though uses an internal DB, does not seems to survive system crashes, and data usage levels resets.

#### 5. Provides Historic Data, in SQL lite Database

#### 6. JSON/HTML end points are given, so that it could be integrated with other Analytics tools for detailed data analysis (like PowerBI, excel)

![alt UX2](https://github.com/avarghesein/WhiteStat/blob/main/UX/UX1.png)


#### Tools Used 

The Utility has been built using Python3 (Flask , Pandas and SQLite for persistance, Bootstrap/JQuery for UX), and packaged as a Docker Container. 
As of now it supports both X64 and arm/Armhf (ArmV7) architectures, and container image for both has been available in Docker Hub. 

## Prerequisites : 

As “WhiteStat” pulls the source network statistics from  “DarkStat”, you’ve to configure “DarkStat” properly in your environment. 
A possible configuration has been [mentioned here](https://github.com/avarghesein/-NIX/blob/main/Raspberry%20Pi%20II%20(Buster)/MinimalNetworkBandwidthMonitor.md). 

Find more more information on DarkStat below:

https://unix4lyfe.org/darkstat/

https://www.tecmint.com/darkstat-web-based-linux-network-traffic-analyzer/

 

## Usage: 

“WhiteStat” is built to run as a Docker Container, and the image has been [uploaded in DockerHub](https://hub.docker.com/r/avarghesein/whitestat). 

For X64 Hardware: e.g.

    docker run --name whitestat \
    --env DATA_STORE="/mnt/whitestat/" \
    --env DARKSTAT_URL="http://192.168.1.5:777" \
    --env SERVER_PORT=777 \
    --mount type=bind,source="/home/ubuntuuser/whitestat",target="/mnt/whitestat/"  \
    -p 888:777 \
    -d avarghesein/whitestat:v5

For RaspberryPi2 (ARMV7 or armhf) Hardware: e.g.

    docker run --name whitestatpi \
    --env DATA_STORE="/mnt/whitestat/" \
    --env DARKSTAT_URL="http://192.168.1.5:777" \
    --env SERVER_PORT=777 \
    --mount type=bind,source="/home/pi/whitestat/",target="/mnt/whitestat/"  \
    -p 888:777 \
    -d avarghesein/whitestat:v5_armhf
    
Now You could view Daily Bandwidth Usage using

    Default UI: http://IP:888/
    Plain HTML: http://IP:888/table/
    Plain JSON: http://IP:888/json/

Bandwidth Usage History couldbe viewed through

    Default UI: http://IP:888/history?start=2021-01-30 00:00:00&end=2021-01-31 00:00:00
    Plain HTML: http://IP:888/table/history?start=2021-01-30 00:00:00&end=2021-01-31 00:00:00
    Plain JSON: http://IP:888/json/history?start=2021-01-30 00:00:00&end=2021-01-31 00:00:00


We could feed these URLs to other Data Analysis systems (e.g. An excel with PowerQuery, which automatically refresh in every minute) for Intuitiveness. 

![alt UX2](https://github.com/avarghesein/WhiteStat/blob/main/UX/UX2.png)

## Key Configuration Options:

"Config/WhiteStatConfig.json", contains the key configuration parameters, which controls WhiteStat.
A sample instance has been given below;

     {
           "DATA_STORE": "./WhiteStat/RunConfig",
           "DBFile": "WhiteStat.db",
           "LOGFile": "WhiteStatLog.txt",
           "IP_MAC_REWRITE": "IP_MAC.txt",
           "MAC_MAC_REWRITE": "MAC_MAC.txt",
           "MAC_HOST_MAP": "MAC_HOST.txt",
           "DARKSTAT_URL": "http://192.168.1.5:777",
           "IPFilter": "([\\d]+\\.){3,3}\\d+",
           "IdleSeconds": 30,
           "UpdateDBSeconds": 40,
           "SERVER_PORT":777
     }

This file will be automatically created, when you start the container for the first time. The only requirement would be, provide a writable path on the  Host machine as the bind mount through DATA-STORE, environment variable.  Also provide the DarkStat URL, with DARKSTAT_URL environment parameter. 

Other parameters have been explained below; 
The default values for all parameters will be filled by WhiteStat. You've to edit the values for advanced configuration for your network, if needed.

     {
             "DATA_STORE": "{Host Path provided in the DATA_STORE param docker command line}",
             
             "DBFile": "{Name of the SQLite File, Default: WhiteStat.db. Usage data will be stored here}",
             
             "LOGFile": "{Log File: Default name: WhiteStatLog.txt}",
             
             # In Key value format seperated by |, multiple entries are seperated by new line             
             "IP_MAC_REWRITE": "{Default: IP_MAC.txt, Provide if you've to see a different MAC than original for an IP in daily usage reports}.",
             
             # In Key value format seperated by |, multiple entries are seperated by new line             
             "MAC_MAC_REWRITE": "{Default: MAC_MAC.txt, Provide if you would like to change a MAC address to a different one}",
             
             # In Key value format seperated by |, multiple entries are seperated by new line
             "MAC_HOST_MAP": "{Default: MAC_HOST.txt, maps a MAC to a user friendly Host Name, will be displayed in usage reports, for easy tracking}",
             
             "DARKSTAT_URL": "The Url of DarkStat",
             
             "IPFilter": "This filter define which all IP entries will be used for reporting. Default is only IPV4 addresses",
             
             "IdleSeconds": "Sleep interval for whitestat, after each data extraction from DarkStat",
             
             "UpdateDBSeconds": "How Often the DB should be updated. i.e in every 40 seconds",
             
             "SERVER_PORT":"The port at which WhiteStat will be available"
             
             "LAN_SEGMENT_MASKS":"LAN segments used inside your private network. Auto populated"
             
             "LAN_ROUTERS_TO_SKIP": "Router MAC's in the LAN to skip while reporting usage. Auto populated"
       }
       
 
 ###### NOTE: Once you update this configuration options and any of the related files, Restart the running Whitestat Container to get it applied. 
 
     e.g. > docker container restart whitestatpi
     
     
 ## How to Build
 
 ### Auto Build & Deploy
 
 Refer :
 
 WhitestatAutoBuildPublish.sh
 
 WhitestatAutoDockerDeploy.sh
 
 ### Build UX
 
 For Building UI, navigate to UX directory and run
 
    npm run build
 
 ### Build Docker Images
 
 Docker files have been given in the root directory of the source, running which will create docker images, ready to be deployed.
 
 For X64 machines
 
    docker build -f Dockerfile -t avarghesein/whitestat:v3 .
  
For arm/armhf/armv7 (or RaspberryPi2) machines

    docker run --rm --privileged fkrull/qemu-user-static enable
    docker build -f Dockerfile.armhf -t avarghesein/whitestat:v3_armhf .

 Note: The first docker command (for arm platform only) is to enable arm to X64 translations through [Qemu-User-Static](https://ownyourbits.com/2018/06/13/transparently-running-binaries-from-any-architecture-in-linux-with-qemu-and-binfmt_misc/)
 
 Earlier I was trying to build Qemu Virtual machines for ARMV7 architectures, which is painstaking and much slower. By using qemu-User-Static, build your ARM Container images at least 2x faster (when compared to building the same in the original armv7 devices like RaspberryPi)
 

