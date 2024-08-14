#!/bin/bash
while true; do
	/home/gidverksted/env/bin/python3 /usr/local/bin/send-snapshot-to-prusaconnect-led-indicator.py ON > /var/log/send-snapshot-to-prusaconnect-led-indicator.log 2>&1
	rpicam-still -o /home/gidverksted/Pictures/upload.jpg
	curl --header "Token: <secret>" --header "Fingerprint: <secret>" --header "Content-Type: image/jpg" https://connect.prusa3d.com/c/snapshot -T /home/gidverksted/Pictures/upload.jpg > /var/log/send-snapshot-to-prusaconnect.log 2>&1
	sleep 3
	/home/gidverksted/env/bin/python3 /usr/local/bin/send-snapshot-to-prusaconnect-led-indicator.py OFF > /var/log/send-snapshot-to-prusaconnect-led-indicator.log 2>&1
	sleep 2
done
