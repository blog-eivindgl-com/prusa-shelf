#!/usr/bin/env python

#import RPi.GPIO as GPIO
import subprocess
import os
from gpiozero import Button

#GPIO.setmode(GPIO.BCM)
#GPIO.setup(3, GPIO.IN, pull_up_down=GPIO.PUD_UP)
#GPIO.wait_for_edge(3, GPIO.FALLING)
button = Button(3)
button.wait_for_press()
#subprocess.call(['shutdown', '-h', 'now'], shell=True)
os.system("sudo shutdown -h now")

