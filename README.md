# WhiteStat
An entire Network (Internet) Bandwidth Daily Usage Analyser, in a Docker Container
with Historic Data Persistence. Supports both IPV4 and V6 captures.

Platforms Supported: RaspberryPi2/armv7l and X64 architectures.

No other dependency or installs required other than Docker CE available in Host System.

![alt UX](https://github.com/avarghesein/WhiteStat/blob/main/Docs/UX3.png)

Pull & Run: [avarghesein/whitestat](https://hub.docker.com/r/avarghesein/whitestat) in your Linux Device.
Below sample shows running "WhiteStat" on RaspberryPi 2B (armv7l), which is the default gateway for the network, and host interface named as "eth0". 

The Bind Directory should be writable.
Open ports 777, 888 in firewall

      docker run --name whitestatpi --restart always \
    --network host --privileged \
    --env TZ="Asia/Calcutta" \
    --env ROLE="MONITOR|ANALYZER" \
    --env HOST_INTERFACE="eth0" \
    --env MONITOR_URL=":888" \
    --env ANALYZER_PORT=777 \
    --env DATA_STORE="/mnt/whitestat/" \
    --mount type=bind,source="/home/pi/whitestat/",target="/mnt/whitestat/"  \
    -d avarghesein/whitestat:v9_armhf

Now Access the Usage Reports at 

    http://IP:777

# Why WhiteStat? 

I have been looking for a Network (Internet) Bandwidth Analyzer, which could easily run on my RaspberryPi hardware with minimal footprint and provides daily statistics (per device level, not IP as any device can have multiple IP's under a DHCP environment) which is easy to comprehend in a glance. 

Most of the tools, I came across are much heavier for the purpose and the information shown in the UI is pretty difficult grasp for an average user.
Mostly these tools also store the flow data in every minutes, and your storage could be piled up with Gig(s) of data in a matter of days.

What about a utility, which is minimal enough to smoothly run on a Pi hardware, efficiently uses the storage and yet provide features similar to aformentioned tools with live statistics 

## Features

#### 1. Entire Network Usage Analyzer is in a Docker Image and minimal enough to run on a Pi Hardware

#### 2. Provides Daily Usage Levels per individual Host in the Network, Considering DHCP and the same Host could have different IP's on the same day

#### 3. Single Responsive Dashboard (UX) to view all the daily/historic statistics. Supports searching/sorting on all usage record fields.

#### 4. Survival of Usage Data, in case of a System Crash (Router/Pi at which WhiteStat is running)

   WhiteStat keeps checkpoints on data usage in every 30 Seconds by default, and use the same as the starting level, when the system comes up.
 
#### 5. Provides Historic Data, in SQL lite Database

#### 6. JSON end points are given, so that it could be integrated with other Analytics tools for detailed data analysis (like PowerBI, excel)

![alt UX2](https://github.com/avarghesein/WhiteStat/blob/main/Docs/UX1.png)


## Prerequisites : 

Other than Docker CE, No other external library or package dependency.

Only ensure the below;

    1. Your Linux Device as the Default Gateway (X64 or armhf)

If not, make it as the default gateway: Making a raspberryPi2 as the Default Gateway has been [explained here](https://github.com/avarghesein/WhiteStat/blob/main/Docs/LinuxDeviceAsGateway.md).

    2. Docker available in the Linux Device

    3. You're okay with running "WhiteStat", in privilaged mode with directly interacting HOST network

 

## Usage: (Both Packet Capturing and Analyzing in a single container)

“WhiteStat” is built to run as a Docker Container, and the image has been [uploaded in DockerHub](https://hub.docker.com/r/avarghesein/whitestat). 


For RaspberryPi2 (ARMV7 or armhf) Hardware: e.g.

    docker run --name whitestatpi --restart always \
    --network host --privileged \
    --env TZ="Asia/Calcutta" \
    --env ROLE="MONITOR|ANALYZER" \
    --env HOST_INTERFACE="eth0" \
    --env MONITOR_URL=":888" \
    --env ANALYZER_PORT=777 \
    --env DATA_STORE="/mnt/whitestat/" \
    --mount type=bind,source="/home/pi/whitestat/",target="/mnt/whitestat/"  \
    -d avarghesein/whitestat:v9_armhf

For X64 Hardware:

    -d avarghesein/whitestat:v9

Need to Capture from multiple Network Interfaces?

    --env HOST_INTERFACE="eth0|eth1" \


## Advanced Usage: (Packet Capturing and Analyzing features in seperate containers and in seperate hosts)

See **[Architecture Page here](https://github.com/avarghesein/WhiteStat/blob/main/Docs/Architecture.MD)**, for more details:

If you would like to confine individual roles (Monitor/Analyzer Roles) to seperate machines;
Say you only require Packet Capturing role in Default Gateway, device for minimal footprint, and 
Analyzer role to be running in a seperate Device in the Network;

Run WhiteStat as Monitor only in default gateway sample: (say in 192.168.1.5)

    docker run --name whitestatpi --restart always \
    --network host --privileged \
    --env TZ="Asia/Calcutta" \
    --env ROLE="MONITOR" \
    --env HOST_INTERFACE="eth0" \
    --env MONITOR_URL=":888" \
    --env DATA_STORE="/mnt/whitestat/" \
    --mount type=bind,source="/home/pi/whitestat/",target="/mnt/whitestat/"  \
    -d avarghesein/whitestat:v9_armhf

Now Run Analyzer role in another machine (192.168.1.6) which does most of the heavy duty, pointing it to
the Monitor instance:

    docker run --name whitestatpi --restart always \
    --env TZ="Asia/Calcutta" \
    --env ROLE="ANALYZER" \
    --env MONITOR_URL="192.168.1.5:888" \
    --env ANALYZER_PORT=777 \
    --env DATA_STORE="/mnt/whitestat/" \
    --mount type=bind,source="/home/pi/whitestat/",target="/mnt/whitestat/"  \
    -d avarghesein/whitestat:v9_armhf


You could view Daily Bandwidth Usage using

    UI: http://192.168.1.6:777/
    JSON: http://192.168.1.6:777/json/

Bandwidth Usage History couldbe viewed through

    UI: http://192.168.1.6:777/
    JSON: http://192.168.1.6:777/json/history?start=2021-01-30 00:00:00&end=2021-01-31 00:00:00
    JSON including Public IPs: http://192.168.1.6:777/json/history?start=2021-01-30 00:00:00&end=2021-01-31 00:00:00&includePublicIP=yes


We could feed these URLs to other Data Analysis systems (e.g. An excel with PowerQuery, PowerBI), using the above end points.

![alt UX2](https://github.com/avarghesein/WhiteStat/blob/main/Docs/UX2.png)

## Easily Tag a Friendly Name, to any LAN Device or to an External IP, with the "Inplace Edit" feature in UX

The UX supports inplace editing of Device/Host Names by double clicking on the Host Name Grid Cell, so that a friendlier name could be assigned to any LAN Device or to an External IP.

The name will be saved, once you change and navigate away from the host name cell in the Grid.

![alt UX4](https://github.com/avarghesein/WhiteStat/blob/main/Docs/UX4.png)

## Key Configuration Options:

"WhiteStatConfig.json", contains the key configuration parameters, which controls WhiteStat.

A sample instance has been given below;

    {
      "ROLE": "MONITOR|ANALYZER",

      "DATA_STORE": "./WhiteStat/RunConfig",

      "DBFile": "WhiteStat.db",
      
      "HOST_INTERFACE":"eth0",
      "MONITOR_URL": ":888",
      "ANALYZER_PORT":777,
      
      "IdleSeconds": 150,
      "UpdateDBSeconds": 300,
      "MemoryLimitInMB": 250,

      "EXTRA_PCAP_FILTER": "",
      "LAN_SEGMENT_V4_MASKS":"0.0.0.0|10|192.168|172.16|172.17",
      "LAN_SEGMENT_V6_MASKS":"fe80|fec0|fd",
      "LAN_ROUTERS_TO_SKIP":"",
      "LOGFile": "WhiteStatLog.txt",
      "TRACEFile": "WhiteStatTrace.txt"
    }

This file will be automatically created, when you start the container for the first time. The only requirement would be, provide a writable path on the  Host machine as the bind mount through DATA-STORE, environment variable.

Parameters have been explained below; 
The default values for all parameters will be filled by WhiteStat. You've to edit the values for advanced configuration for your network, if needed.

    {
        "ROLE": "MONITOR|ANALYZER",

        "DATA_STORE": "{Host Path provided in the DATA_STORE param docker command line}",
        
        "DBFile": "{Name of the SQLite File, Default: WhiteStat.db. Usage data will be stored here}",

        "HOST_INTERFACE":"Network Interfaces to Watch on Host Device",

        "MONITOR_URL": "IP:Port, of the monitor instance of whitestat. Default include both and at port 888",

        "ANALYZER_PORT":The port at which WhiteStat will be available. Default 777,        

        "IdleSeconds": "Sleep interval for whitestat, after each data extraction from Monitor",
        
        "UpdateDBSeconds": "How Often the DB should be updated. i.e in every 40 seconds",
        
        "MemoryLimitInMB": "Max RAM usage allowed for WhiteStat, Restart if the limit exceeds. Useful for low memory devices like RaspberryPI",

        "EXTRA_PCAP_FILTER": "any additional pcap filter you prefer, say (tcp and port 80)",

        "LAN_SEGMENT_V4_MASKS":"LAN segments used inside your private network. Auto populated",

        "LAN_SEGMENT_V6_MASKS":"LAN segments used inside your private network. Auto populated",

        "LAN_ROUTERS_TO_SKIP":"Router MAC's in the LAN to skip while reporting usage. Auto populated",

        "LOGFile": "{Log File: Default name: WhiteStatLog.txt}",

        "TRACEFile": "{Trace File: Default name: WhiteStatTrace.txt}"
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
 
    docker build -f Dockerfile -t avarghesein/whitestat:v9 .
  
(Cross Platform Build) For arm/armhf/armv7 (or RaspberryPi2) machines

    docker run --rm --privileged fkrull/qemu-user-static enable
    docker build -f Dockerfile.armhf -t avarghesein/whitestat:v9_armhf .

 Note: The first docker command (for arm platform only) is to enable arm to X64 translations through [Qemu-User-Static](https://ownyourbits.com/2018/06/13/transparently-running-binaries-from-any-architecture-in-linux-with-qemu-and-binfmt_misc/)
 
 Earlier I was trying to build Qemu Virtual machines for ARMV7 architectures, which is painstaking and much slower. By using qemu-User-Static, build your ARM Container images at least 2x faster (when compared to building the same in the original armv7 devices like RaspberryPi)

 #### Tools Used 

Front End(UX): Python Flask, BootStrap, JQuery, SASS

Middle Ware: Python, Pcap System Library, Python Numpy/Pandas, Python Threads

BackEnd: SQLite

The entire components are built and packaged as Docker Images, and run as Containers in the Host System.
Supports both X64 and arm/Armhf (ArmV7) architectures. 
Docker Images are available in Docker Hub.

### References

##### Network Interface TCP/IP Data Capture Reference:

[PCappy, No Build Required.Through Python CTypes](https://github.com/allfro/pcappy)

[Original PCapy, Need to build for each platform](https://github.com/helpsystems/pcapy)

[Abount PCap System Library Filter Reference](https://www.tcpdump.org/manpages/pcap-filter.7.html)

[Packet Capture Reference](https://www.binarytides.com/code-a-packet-sniffer-in-python-with-pcapy-extension/)

[Sniff Packets, ref1](https://github.com/Arturogv15/sniffer/blob/master/main.py)

[Sniff Packets, ref2](https://github.com/danicuestasuarez/packet-sniffer/blob/master/sniffer.py)


##### Cross Platform Build Reference

[Run Arm Arch Container in X64, through Qemu UserMode and binfmt_misc](https://github.com/avarghesein/docker-qemu-user-static) 

[Qemu User Static](https://github.com/multiarch/qemu-user-static)

