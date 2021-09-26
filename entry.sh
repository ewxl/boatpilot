#!/bin/bash

echo start control
while true; do nice 10 python3 control.py; sleep 5;date;done &

while ! test -e /tmp/com;do sleep 0.1;done

echo start main
exec python3 main.py

