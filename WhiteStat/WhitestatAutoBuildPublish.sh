#!/bin/bash

docker run --rm --privileged fkrull/qemu-user-static enable
cd ./Analyzer/UX/
npm run build
cd ../..

docker image rm $(docker image list | grep "avarghesein/whitestat" | grep v9 |  tr -s " " | cut -d " " -f 3)
docker image rm $(docker image list | grep none |  tr -s " " | cut -d " " -f 3)

docker build -f Dockerfile.armhf -t avarghesein/whitestat:v9_armhf .
docker build -f Dockerfile -t avarghesein/whitestat:v9 .
docker push avarghesein/whitestat:v9_armhf
docker push avarghesein/whitestat:v9