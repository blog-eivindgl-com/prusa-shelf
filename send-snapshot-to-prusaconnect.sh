#!/bin/bash
while true; do
	rpicam-still -o /home/gidverksted/Pictures/upload.jpg
	curl --header "Token: <secret>" --header "Fingerprint: <secret>" --header "Content-Type: image/jpg" https://connect.prusa3d.com/c/snapshot -T /home/gidverksted/Pictures/upload.jpg
	sleep 5
done
