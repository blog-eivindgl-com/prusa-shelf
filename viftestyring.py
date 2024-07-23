#!/usr/bin/env python
from gpiozero import Button, LED
from time import sleep

enclosure_fan = LED(12)
button = Button(16)
enclosure_fan_is_on = False

while True:
  try:
    button.wait_for_press()
    if enclosure_fan_is_on:
      print("Turn fan off")
      enclosure_fan.off()
      enclosure_fan_is_on = False
    else:
      print("Turn fan on")
      enclosure_fan.on()
      enclosure_fan_is_on = True
    sleep(3)
  except KeyboardInterrupt:
    break
  except:
    print("Some error occured")

