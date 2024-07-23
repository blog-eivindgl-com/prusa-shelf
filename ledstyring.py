#!/usr/bin/env python
from gpiozero import MotionSensor, LED
from time import sleep
import datetime

led_strip = LED(12)
motion_sensor = MotionSensor(16)
led_strip_is_on = False

while True:
  try:
    if led_strip_is_on:
      led_on_duration = datetime.datetime.now() - led_turned_on_at
      print("LED strip has been on for %s seconds"%led_on_duration.total_seconds())
      if motion_sensor.motion_detected:
        last_motion_detected_at = datetime.datetime.now()
      if led_on_duration.total_seconds() > 90 and (datetime.datetime.now() - last_motion_detected_at).total_seconds() > 60:
        print("No motion detected the last 60s. Turn off LED")
        led_strip.off()
        led_strip_is_on = False
    else:
       motion_sensor.wait_for_motion()
       print("Turn on LED strip")
       led_strip.on()
       led_turned_on_at = datetime.datetime.now()
       led_strip_is_on = True
    sleep(5)
  except KeyboardInterrupt:
    break
  except Exception as e:
    print("Error:%s"%e)
