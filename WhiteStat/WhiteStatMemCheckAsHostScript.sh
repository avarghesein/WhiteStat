#!/bin/bash
##Add below to /etc/rc.local
##bash /home/pi/WhiteStatMemUsage.sh >> /home/pi/WhiteStatMemUsage.log &

echo "Starting Memory Check for WhiteStatPi...$(date)"

while true
do

    x=$(docker stats --no-stream | grep -P ' whitestatpi ' | tr -s " " | cut -d " " -f 4 | grep -Po '\K([\d\.]+)(?=MiB)')

    if (( $(echo "$x > 250" |bc -l) )); then
       docker container restart whitestatpi 
       echo "Whitestatpi restarted due to memory usage $x Mib...$(date)"
    fi 

    x=$(docker stats --no-stream | grep -P ' whitestatpi.A ' | tr -s " " | cut -d " " -f 4 | grep -Po '\K([\d\.]+)(?=MiB)')

    if (( $(echo "$x > 250" |bc -l) )); then
       docker container restart whitestatpi.A 
       echo "Whitestatpi.A restarted due to memory usage $x Mib...$(date)"
    fi 

    sleep 60

done
