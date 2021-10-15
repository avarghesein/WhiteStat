
cd ./Analyzer/UX/
npm run build
cd ../..

docker image rm $($(docker image ls).Split([Environment]::NewLine) | %{ $_ -replace '\s+', ' '} | Select-String -Pattern "v11_win64"  | %{ $_.ToString().split(" ")[2] })
docker image rm $($(docker image ls).Split([Environment]::NewLine) | %{ $_ -replace '\s+', ' '} | Select-String -Pattern "none"  | %{ $_.ToString().split(" ")[2] })

docker build -f Dockerfile_v10+.WIN64 -t avarghesein/whitestat:v11_win64 .
docker push avarghesein/whitestat:v11_win64
