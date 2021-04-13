FROM python:3.9-slim-buster

RUN apt-get update -y && pip install numpy && pip install lxml && pip install flask && pip install requests
RUN pip install psutil
RUN apt-get install libpcap0.8
RUN mkdir -p /app/WhiteStat/
WORKDIR /app/WhiteStat/
COPY WhiteStatService.sh ./WhiteStatService.sh
COPY main.py ./main.py
COPY startup.py ./startup.py
COPY setup.py ./setup.py
ADD  Analyzer ./Analyzer
ADD  Common ./Common
ADD  NetMonitor ./NetMonitor
RUN  chmod a+x /app/WhiteStat/WhiteStatService.sh

EXPOSE 777
EXPOSE 888
EXPOSE 999

ENV PLATFORM="LINUX"
#ENV TZ="Asia/Calcutta"

#CMD ["/app/WhiteStat/WhiteStatService.sh"]
CMD PYTHONPATH=/app/ python /app/WhiteStat/startup.py /app/WhiteStat/WhiteStatService.sh

#Docker Build Sample:
#docker build -f Dockerfile -t avarghesein/whitestat:v7.
#docker tag avarghesein/whitestat:v7 avarghesein/whitestat:v7
#docker login
#docker push avarghesein/whitestat:v7

#Running Container Sample
#docker run --name whitestat \
#--name hostnet --network host --privileged \
#--env TZ="Asia/Calcutta" \
#--env ROLE="MONITOR|ANALYZER" \
#--env HOST_INTERFACE="eth0" \
#--env MONITOR_URL=":888" \
#--env ANALYZER_PORT=777 \
#--env DATA_STORE="/mnt/whitestat/" \
#--mount type=bind,source="/media/TMP-DSK/Python/WhiteStat/TestDockerConfig/",target="/mnt/whitestat/"  \
#-it avarghese.in/whitestat:v7 /bin/bash
#
# For Daemon/Service mode:
#-d avarghese.in/whitestat:v7
#
#Now Access Whitestat at http://localhost:777