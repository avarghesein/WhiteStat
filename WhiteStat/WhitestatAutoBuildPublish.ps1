
cd ./Analyzer/UX/
npm run build
cd ../..

docker image rm $(docker image list | grep "avarghesein/whitestat" | grep v9 |  tr -s " " | cut -d " " -f 3)
docker image rm $(docker image list | grep none |  tr -s " " | cut -d " " -f 3)

docker build -f Dockerfile.WIN64 -t avarghesein/whitestat:v10_win64 .
docker push avarghesein/whitestat:v10_win64
