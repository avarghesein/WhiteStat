# WhiteStat
Internet/Network Bandwidth Daily Usage Analyser with Historic Data Persistence, in a Docker Container, with added support for RaspberryPi2.

# The Purpose... 

I have been looking for a Network (Internet) Bandwidth Analyzer, which could easily run in a RaspberryPi hardware with minimal footprint. Most of the tools I came across (like ‘ntopng’), are much heavier and flood the storage with data in every minutes/hour, though those tools provide a hourly statistics. It could held up the PI’s resocues and makes the entire network slower (as Pi serves as the Default Gateway for my Private Network) 

I have been looking for much leaner utility, and could provide a daily statistics for all the devices in my Private Network.  

## Extending DarkStat ! 

While I came across “DarkStat”, I thought to extend the same, as it is much leaner (the entire source is in raw C, even the minimal HTTP Server built in) compared to other tools and with high performance. However It does not provide a daily statistics, and probably a friendlier way of configuring and listing my devices (used IP’s instead of Host Name) in the Network. But that’s just fine, and that’s why “WhiteStat” 
 

## Tools Used 

The Utility has been built using Python3 (Flask , Pandas and SQLite for persistance), and packaged as a Docker Container. As of now it supports both X64 and arm/Armhf (ArmV7) architectures, and container image for both has been available in Docker Hub. 

## Prerequisites : 

As “WhiteStat” built on top of “DarkStat”, you’ve to configure “DarkStat” properly in your environment. A possible scenario has been mentioned here. 

 

## Usage: 

“WhiteStat” is built to run as a Docker Container, and the image has been [uploaded in DockerHub](https://hub.docker.com/r/avarghesein/whitestat). 

For X64 Hardware: e.g.

    docker run --name whitestat \
    --env DATA_STORE="/mnt/whitestat/config/" \
    --env DARKSTAT_URL="http://192.168.1.5:777" \
    --env SERVER_PORT=777 \
    --mount type=bind,source="/media/TMP-DSK/Python/WhiteStat/TestDockerConfig/",target="/mnt/whitestat/config/"  \
    -p 5000:777 \
    -d avarghesein/whitestat:v3

For RaspberryPi2 (ARMV7 or armhf) Hardware: e.g.

    docker run --name whitestatpi \
    --env DATA_STORE="/mnt/whitestat/config/" \
    --env DARKSTAT_URL="http://192.168.1.5:777" \
    --env SERVER_PORT=777 \
    --mount type=bind,source="/media/TMP-DSK/Python/WhiteStat/TestDockerConfig/",target="/mnt/whitestat/config/"  \
    -p 5000:777 \
    -d avarghesein/whitestat:v3_armhf
    
