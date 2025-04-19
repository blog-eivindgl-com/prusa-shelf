#!/bin/bash
while true; do
	libcamera-still --output - | curl -X PUT --header "Token: <secret>" --header "Fingerprint: <secret>" --header "Content-Type: image/jpg" https://connect.prusa3d.com/c/snapshot --data-binary @-
	echo $(date +"%Y-%m-%d %H:%M:%S") > /home/gidverksted/snapshot-timestamp.txt
	sleep 5
done
