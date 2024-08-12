#!/usr/bin/env python

#import RPi.GPIO as GPIO
import sys
from gpiozero import LED

# Define LED lights GPIO
printer_cam_indicator_led = LED(10)

if sys.argv[1] == "ON":
    printer_cam_indicator_led.on()
else:
    printer_cam_indicator_led.off()