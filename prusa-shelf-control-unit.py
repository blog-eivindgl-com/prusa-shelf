#!/usr/bin/env python

#import RPi.GPIO as GPIO
import time, datetime, os, subprocess
from gpiozero import Button, MotionSensor, LED
from signal import pause

#GPIO.setmode(GPIO.BCM)
#GPIO.setup(3, GPIO.IN, pull_up_down=GPIO.PUD_UP)
#GPIO.wait_for_edge(3, GPIO.FALLING)

# Define LED lights GPIO
printer_light_led = LED(23)
printer_cam_led = LED(22)
printer_filter_led = LED(27)
room_exhaust_fan_led = LED(17)
power_off_led = LED(4)

# Define buttons GPIO
pi_power_button = Button(3, hold_time=3)
printer_light_button = Button(21)
printer_cam_button = Button(20)
printer_filter_button = Button(16)
room_exhaust_fan_button = Button(12)
room_motion_sensor = MotionSensor(18)

# Define switches GPIO
room_led_strips_switch = LED(26)
printer_light_switch = LED(19)
printer_filter_switch = LED(13)

# Raspberry Pi power button
def shutdown():
  power_off_led.on()
  #subprocess.call(['shutdown', '-h', 'now'], shell=True)
  os.system("sudo shutdown -h now")
pi_power_button.when_held = shutdown

# Printer light for camera
def switch_printer_light():
  if printer_light_led.is_lit:
    printer_light_switch.off()
    printer_light_led.off()
  else:
    printer_light_switch.on()
    printer_light_led.on()
printer_light_button.when_pressed = switch_printer_light

# Printer camera snapshots
def switch_printer_cam():
  if printer_cam_led.is_lit:
    os.system("pkill -f /usr/local/bin/send-snapshot-to-prusaconnect.sh")
    printer_cam_led.off()
  else:
    os.system("/usr/local/bin/send-snapshot-to-prusaconnect.sh")
    printer_cam_led.on()
printer_cam_button.when_pressed = switch_printer_cam
# Initialize a time variable to use when blinking LED for an active camera
printer_cam_stopped_at = time.time()
printer_cam_led_toggled_at = time.time()

# Prusa Enclosure Advanced Filtering System
def switch_printer_filter():
  if printer_filter_led.is_lit:
    printer_filter_switch.off()
    printer_filter_led.off()
  else:
    printer_filter_switch.on()
    printer_filter_led.on()
printer_filter_button.when_pressed = switch_printer_filter

# Room exhaust fan
def switch_room_exhaust_fan():
  if room_exhaust_fan_led.is_lit:
    # TODO: Decide how to turn fan on and off
    room_exhaust_fan_led.off()
  else:
    # TODO: Decide how to turn fan on and off
    room_exhaust_fan_led.on()
room_exhaust_fan_button.when_pressed = switch_room_exhaust_fan

def test_camera_snapshot_status():
  try:
    # Blink printer cam LED if camera is running
    cam_image_file_age_in_seconds = time.time() - os.stat("/home/gidverksted/Pictures/upload.jpg").st_mtime
    cam_stopped_age_in_seconds = time.time() - printer_cam_stopped_at
    # TODO: Can't remember the purpose of this
    cam_led_toggle_age = time.time() - printer_cam_led_toggled_at
    
    if cam_image_file_age_in_seconds < 10 and cam_stopped_age_in_seconds > 10:
      printer_cam_led.toggle()
      printer_cam_led_toggled_at = time.time()
    else:
      # Turn cam led off to indicate camera service not running
      printer_cam_led.off()
  except:
    print("unable to detect camera status")

def keep_room_led_strips_on_while_someone_present():
  try:
    if room_led_strips_switch.is_lit:
      led_on_duration = datetime.datetime.now() - led_turned_on_at
      # "LED strip has been on for %s seconds"%led_on_duration.total_seconds()
      if room_motion_sensor.motion_detected:
        last_motion_detected_at = datetime.datetime.now()
      if led_on_duration.total_seconds() > 90 and (datetime.datetime.now() - last_motion_detected_at).total_seconds() > 60:
        # No motion detected the last 60s. Turn off LED
        room_led_strips_switch.off()
    else:
        room_motion_sensor.wait_for_motion()
        # Turn on LED strip
        room_led_strips_switch.on()
        led_turned_on_at = datetime.datetime.now()
  except:
    print("unable to control room led strips")

while True:
  keep_room_led_strips_on_while_someone_present()
  test_camera_snapshot_status()

  # Run loop two times a second  
  time.sleep(0.5)