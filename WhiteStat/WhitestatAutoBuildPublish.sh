#!/bin/bash

docker run --rm --privileged fkrull/qemu-user-static enable

cd ./Analyzer/UX/
npm run build
cd ../..

mkdir -p ./NetMonitor/CLIB/build/
cd ./NetMonitor/CLIB/build/
cmake ..
make

cd ../../..

docker stop "PiBuilder"
docker rm "PiBuilder"

cbuildPath=`echo "$(pwd)/NetMonitor/CLIB/"`

#NB:Build the PiBuilder Image from (C++BuilderDockerfile.armhf), if not already done

docker run --name "PiBuilder" -d \
--privileged \
--mount type=bind,source=$cbuildPath,target="/mnt/cpp_source/"  \
-it avarghesein/armhf_cpp_builder:v7_armhf

docker exec PiBuilder bash -c "mkdir -p /mnt/cpp_source/build_arm;cd /mnt/cpp_source/build_arm;cmake ..;make"

docker image rm $(docker image list | grep "avarghesein/whitestat" | grep v10 |  tr -s " " | cut -d " " -f 3)
docker image rm $(docker image list | grep none |  tr -s " " | cut -d " " -f 3)

docker build -f Dockerfile_v10+.armhf -t avarghesein/whitestat:v10_armhf .
docker build -f Dockerfile_v10+ -t avarghesein/whitestat:v10 .

docker login
docker push avarghesein/whitestat:v10_armhf
docker push avarghesein/whitestat:v10