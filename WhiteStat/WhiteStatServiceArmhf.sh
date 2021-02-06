#!/bin/sh -e
#

/usr/bin/python3.7 ./WhiteStatServer.py &
/usr/bin/python3.7 ./WhiteStatAnalyzer.py
fg
