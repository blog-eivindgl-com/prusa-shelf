#!/usr/bin/env python

import time, datetime, os, subprocess, logging
from gpiozero.pins.pigpio import PiGPIOFactory
from gpiozero import Button, MotionSensor, LED, Servo
from signal import pause

logging.basicConfig(filename="/var/log/prusa-shelf-control-unit.log", format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.info("Prusa Shelf Control Unit started")

try:
  f = PiGPIOFactory()
  global printer_power_servo 
  printer_power_servo = Servo(6, pin_factory=f)
  logging.info("Changed to PiGPIOFactory for servo")
except Exception as Argument:
  logging.error("Unable to change to PiGPIOFactory for servo")

# Variables to log some statuses once in a while
printer_cam_error_status_logged_at = datetime.datetime.now()
last_led_on_duration_logged_at = datetime.datetime.now()

# Define LED lights GPIO
printer_light_led = LED(23)
printer_cam_led = LED(22)
printer_filter_led = LED(27)
room_exhaust_fan_led = LED(17)
power_off_led = LED(4)

# Define buttons GPIO
pi_power_button = Button(3, hold_time=3)
printer_power_button = Button(5, hold_time=3)
printer_light_button = Button(21)
printer_cam_button = Button(20)
printer_filter_button = Button(16)
room_exhaust_fan_button = Button(12)
room_motion_sensor = MotionSensor(18, threshold=.99)

# Define switches GPIO
room_led_strips_switch = LED(26)
printer_light_switch = LED(19)
printer_filter_switch = LED(13)

# Raspberry Pi power button
def shutdown():
  logging.debug("Shutdown triggered")
  power_off_led.on()
  #subprocess.call(['shutdown', '-h', 'now'], shell=True)
  os.system("sudo shutdown -h now")
  logging.info("Shutdown")
pi_power_button.when_held = shutdown

# Printer power button
def printer_power_off():
  global printer_power_servo
  logging.debug("Switch printer off triggered")
  if printer_power_servo:
    printer_power_servo.max()
    logging.info("Printer turned off")
  else:
    logging.warning("Printer power servo is not active")
printer_power_button.when_held = printer_power_off
def printer_power_on():
  global printer_power_servo
  logging.debug("Switch printer on triggered")
  if printer_power_servo:
    printer_power_servo.mid()
    logging.info("Printer turned on")
  else:
    logging.warning("Printer power servo is not active")
printer_power_button.when_pressed = printer_power_on

# Printer light for camera
def switch_printer_light():
  logging.debug("Switch printer light triggered")
  if printer_light_led.is_lit:
    printer_light_switch.off()
    printer_light_led.off()
    logging.info("Printer light turned off")
  else:
    printer_light_switch.on()
    printer_light_led.on()
    logging.info("Printer light turned on")
printer_light_button.when_pressed = switch_printer_light

# Printer camera snapshots
def switch_printer_cam():
  global printer_cam_led_toggled_at
  logging.debug("Switch printer cam triggered")
  if printer_cam_led.is_lit:
    os.system("sudo pkill -f /etc/init.d/send-snapshot-to-prusaconnect.sh &")
    printer_cam_led.off()
    logging.info("Printer cam turned off")
  else:
    printer_cam_led_toggled_at = time.time()
    os.system("sudo /etc/init.d/send-snapshot-to-prusaconnect.sh &")
    printer_cam_led.on()
    logging.info("Printer cam turned on")
printer_cam_button.when_pressed = switch_printer_cam
# Initialize a time variable to watch status of printer cam
printer_cam_led_toggled_at = time.time()

# Prusa Enclosure Advanced Filtering System
def switch_printer_filter():
  logging.debug("Switch printer filter triggered")
  if printer_filter_led.is_lit:
    printer_filter_switch.off()
    printer_filter_led.off()
    logging.info("Printer filter turned off")
  else:
    printer_filter_switch.on()
    printer_filter_led.on()
    logging.info("Printer filter turned on")
printer_filter_button.when_pressed = switch_printer_filter

# Room exhaust fan
def switch_room_exhaust_fan():
  logging.debug("Switch room exhaust fan triggered")
  if room_exhaust_fan_led.is_lit:
    # TODO: Decide how to turn fan on and off
    room_exhaust_fan_led.off()
    logging.info("Room exhaust fan turned off")
  else:
    # TODO: Decide how to turn fan on and off
    room_exhaust_fan_led.on()
    logging.info("Room exhaust fan turned on")
room_exhaust_fan_button.when_pressed = switch_room_exhaust_fan

def test_camera_snapshot_status():
  global printer_cam_led_toggled_at
  global printer_cam_error_status_logged_at
  try:
    cam_image_file_age_in_seconds = time.time() - os.stat("/home/gidverksted/Pictures/upload.jpg").st_mtime
    
    if time.time() - printer_cam_led_toggled_at < 10:
      return

    if printer_cam_led.is_lit and cam_image_file_age_in_seconds > 10 and (datetime.datetime.now() - printer_cam_error_status_logged_at).total_seconds() > 60:
      logging.warning("Printer cam is not running")
      printer_cam_error_status_logged_at = datetime.datetime.now()
  except Exception as Argument:
    logging.exception("Unable to detect camera status")

def keep_room_led_strips_on_while_someone_present():
  global led_turned_on_at
  global last_motion_detected_at
  global last_led_on_duration_logged_at
  try:
    if room_led_strips_switch.is_lit:
      led_on_duration = datetime.datetime.now() - led_turned_on_at

      if (datetime.datetime.now() - last_led_on_duration_logged_at).total_seconds() > 60:
        logging.info("Room led strips has been on for %s seconds"%led_on_duration.total_seconds())
        logging.info("Last motion detected at %s"%last_motion_detected_at)
        last_led_on_duration_logged_at = datetime.datetime.now()
      
      if room_motion_sensor.motion_detected:
        last_motion_detected_at = datetime.datetime.now()
      
      if led_on_duration.total_seconds() > 90 and (datetime.datetime.now() - last_motion_detected_at).total_seconds() > 60:
        # No motion detected the last 60s. Turn off LED
        logging.debug("Switch room led strips triggered")
        room_led_strips_switch.off()
        logging.info("Room led strips turned off")
    elif room_motion_sensor.motion_detected:
        # Turn on LED strip
        logging.debug("Switch room led strips triggered")
        room_led_strips_switch.on()
        logging.info("Room led strips turned on")
        led_turned_on_at = datetime.datetime.now()
  except Exception as Argument:
    logging.exception("Unable to control room led strips")

while True:
  keep_room_led_strips_on_while_someone_present()
  test_camera_snapshot_status()

  # Run loop two times a second  
  time.sleep(0.5)
