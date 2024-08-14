#!/usr/bin/env python

#import RPi.GPIO as GPIO
import sys, logging
from gpiozero import LED

logging.basicConfig(filename="/var/log/prusa-shelf-control-unit.log", format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

try:
    # Define LED lights GPIO
    printer_cam_indicator_led = LED(10)

    if sys.argv[1] == "ON":
        printer_cam_indicator_led.on()
        logging.debug("Turned printer cam indicator LED on")
    else:
        printer_cam_indicator_led.off()
        logging.debug("Turned printer cam indicator LED off")
except Exception as Argument:
    logging.error("Unable to toggle printer cam indicator LED")