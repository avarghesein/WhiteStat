#!/bin/bash

docker container stop whitestatpi
docker container stop whitestatpi.A
docker container rm whitestatpi
docker container rm whitestatpi.A
docker image rm $(docker image list | grep "avarghesein/whitestat" | grep v9 |  tr -s " " | cut -d " " -f 3)

docker run --name whitestatpi --restart always \
--network host --privileged \
--env TZ="Asia/Calcutta" \
--env ROLE="MONITOR" \
--env HOST_INTERFACE="eth0" \
--env MONITOR_URL=":888" \
--env ANALYZER_PORT=777 \
--env DATA_STORE="/mnt/whitestat/" \
--mount type=bind,source="/home/pi/whitestat/",target="/mnt/whitestat/"  \
-d avarghesein/whitestat:v9_armhf


docker run --name whitestatpi.A --restart always \
--network host --privileged \
--env TZ="Asia/Calcutta" \
--env ROLE="ANALYZER" \
--env HOST_INTERFACE="eth0" \
--env MONITOR_URL="192.168.1.5:888" \
--env ANALYZER_PORT=777 \
--env DATA_STORE="/mnt/whitestat/" \
--mount type=bind,source="/home/pi/whitestat.A/",target="/mnt/whitestat/"  \
-d avarghesein/whitestat:v9_armhf
