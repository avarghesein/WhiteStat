#!/bin/bash

docker container stop whitestatpi
docker container rm whitestatpi
docker image rm $(docker image list | grep "avarghesein/whitestat" | grep v5 |  tr -s " " | cut -d " " -f 3)

docker run --name whitestatpi --restart always \
--env TZ="Asia/Calcutta" \
--env DATA_STORE="/mnt/whitestat/" \
--env DARKSTAT_URL="http://192.168.1.5:777" \
--env SERVER_PORT=777 \
--mount type=bind,source="/home/pi/whitestat/",target="/mnt/whitestat/"  \
-p 888:777 \
-d avarghesein/whitestat:v5_armhf
