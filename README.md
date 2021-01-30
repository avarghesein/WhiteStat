# WhiteStat
Internet/Network Bandwidth Daily Usage Analyser with Historic Data Persistence, in a Docker Container, with added support for RaspberryPi2.

# The Purpose... 

I have been looking for a Network (Internet) Bandwidth Analyzer, which could easily run in a RaspberryPi hardware with minimal footprint. Most of the tools I came across (like ‘ntopng’), are much heavier and flood the storage with data in every minutes/hour, though those tools provide a hourly statistics. It could held up the PI’s resocues and makes the entire network slower (as Pi serves as the Default Gateway for my Private Network).

What about a utility, which is minimal enough to smoothly run on Pi hardware, and yet provide featuers similar to aformentioned tools? 

## Extending DarkStat ! 

[“DarkStat”](https://github.com/TomMichel/darkstat) seems to be the obvious choice, and I've tried to extend the same, as it is much leaner (the entire source is in raw C, even the minimal HTTP Server built in) compared to other tools and with high performance. However It does not provide a daily statistics, and probably a friendlier way of configuring and listing my devices (used IP’s instead of Host Name) in the Network. But that’s just fine, and that’s why “WhiteStat” 
 

## Tools Used 

The Utility has been built using Python3 (Flask , Pandas and SQLite for persistance), and packaged as a Docker Container. As of now it supports both X64 and arm/Armhf (ArmV7) architectures, and container image for both has been available in Docker Hub. 

## Prerequisites : 

As “WhiteStat” built on top of “DarkStat”, you’ve to configure “DarkStat” properly in your environment. A possible scenario has been [mentioned here](https://github.com/avarghesein/-NIX/blob/main/Raspberry%20Pi%20II%20(Buster)/MinimalNetworkBandwidthMonitor.md). 

 

## Usage: 

“WhiteStat” is built to run as a Docker Container, and the image has been [uploaded in DockerHub](https://hub.docker.com/r/avarghesein/whitestat). 

For X64 Hardware: e.g.

    docker run --name whitestat \
    --env DATA_STORE="/mnt/whitestat/" \
    --env DARKSTAT_URL="http://192.168.1.5:777" \
    --env SERVER_PORT=777 \
    --mount type=bind,source="/home/ubuntuuser/whitestat",target="/mnt/whitestat/"  \
    -p 888:777 \
    -d avarghesein/whitestat:v3

For RaspberryPi2 (ARMV7 or armhf) Hardware: e.g.

    docker run --name whitestatpi \
    --env DATA_STORE="/mnt/whitestat/config/" \
    --env DARKSTAT_URL="http://192.168.1.5:777" \
    --env SERVER_PORT=777 \
    --mount type=bind,source="/home/pi/whitestat/",target="/mnt/whitestat/"  \
    -p 888:777 \
    -d avarghesein/whitestat:v3_armhf
    
Now You could view Daily Bandwidth Usage using

    http://IP:888/

Bandwidth Usage History couldbe viewed through

    http://IP:888/history?start=2021-01-30 00:00:00&end=2021-01-31 00:00:00

