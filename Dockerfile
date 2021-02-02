FROM python:3.9-slim-buster

RUN apt-get update -y && pip install pandas && pip install lxml && pip install flask && pip install requests

RUN mkdir -p /app/WhiteStat/
WORKDIR /app/WhiteStat/
COPY WhiteStatService.sh ./WhiteStatService.sh
COPY WhiteStat.py ./WhiteStat.py
COPY WhiteStatAnalyzer.py ./WhiteStatAnalyzer.py
COPY WhiteStatServer.py ./WhiteStatServer.py
COPY WhiteStatUtils.py ./WhiteStatUtils.py
ADD  Config ./Config
RUN  chmod a+x /app/WhiteStat/WhiteStatService.sh

EXPOSE 777
EXPOSE 888
EXPOSE 999

#ENV TZ="Asia/Calcutta"

CMD ["/app/WhiteStat/WhiteStatService.sh"]

#Docker Build Sample:
#docker build -f Dockerfile -t avarghesein/whitestat:v1 .
#docker tag avarghesein/whitestat:v1 avarghesein/whitestat:v1
#docker login
#docker push avarghesein/whitestat:v1

#Running Container Sample
#docker run --name whitestat \
#--env TZ="Asia/Calcutta" \
#--env DATA_STORE="/mnt/whitestat/config/" \
#--env DARKSTAT_URL="http://192.168.1.5:777" \
#--env SERVER_PORT=777 \
#--env LAN_SEGMENT_MASKS="192.168.1|192.168.0" \
#--mount type=bind,source="/media/TMP-DSK/Python/WhiteStat/TestDockerConfig/",target="/mnt/whitestat/config/"  \
#-p 5000:777 \
#-it avarghese.in/whitestat:v1 /bin/bash
#
# For Daemon/Service mode:
#-d avarghese.in/whitestat:v1
#
#Now Access Whitestat at http://localhost:5000