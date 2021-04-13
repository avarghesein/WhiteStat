
cd ./Analyzer/UX/
npm run build
cd ../..

docker image rm $($(docker image ls).Split([Environment]::NewLine) | %{ $_ -replace '\s+', ' '} | Select-String -Pattern "v10_win64"  | %{ $_.ToString().split(" ")[2] })
docker image rm $($(docker image ls).Split([Environment]::NewLine) | %{ $_ -replace '\s+', ' '} | Select-String -Pattern "none"  | %{ $_.ToString().split(" ")[2] })

docker build -f Dockerfile.WIN64 -t avarghesein/whitestat:v10_win64 .
docker push avarghesein/whitestat:v10_win64
