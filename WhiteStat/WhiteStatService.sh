#!/bin/sh -e
#

python ./WhiteStatServer.py &
python ./WhiteStatAnalyzer.py
fg