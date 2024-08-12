#!/bin/bash
while true; do
	/usr/local/bin/send-snapshot-to-prusaconnect-led-indicator.py ON
	rpicam-still -o /home/gidverksted/Pictures/upload.jpg
	curl --header "Token: <secret>" --header "Fingerprint: <secret>" --header "Content-Type: image/jpg" https://connect.prusa3d.com/c/snapshot -T /home/gidverksted/Pictures/upload.jpg
	sleep 3
	/usr/local/bin/send-snapshot-to-prusaconnect-led-indicator.py OFF
	sleep 2
done
