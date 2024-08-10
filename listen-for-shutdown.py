#!/usr/bin/env python

#import RPi.GPIO as GPIO
import subprocess
import os
from gpiozero import Button, LED
from signal import pause

#GPIO.setmode(GPIO.BCM)
#GPIO.setup(3, GPIO.IN, pull_up_down=GPIO.PUD_UP)
#GPIO.wait_for_edge(3, GPIO.FALLING)
red_led = LED(4)
def shutdown():
  red_led.on()
  #subprocess.call(['shutdown', '-h', 'now'], shell=True)
  os.system("sudo shutdown -h now")

button = Button(3, hold_time=3)
button.when_held = shutdown
pause()
