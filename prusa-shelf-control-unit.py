#!/usr/bin/env python

import time, datetime, os, logging, paho.mqtt.client as mqtt
import parameters # Secrets and other environment specific constants
from gpiozero.pins.pigpio import PiGPIOFactory
from gpiozero import Button, LED

logging.basicConfig(filename="/var/log/prusa-shelf-control-unit.log", format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.info("Prusa Shelf Control Unit started")
factory = PiGPIOFactory()

# Variables to log some statuses once in a while
printer_cam_running = False
printer_cam_error_status_logged_at = datetime.datetime.now()
last_led_on_duration_logged_at = datetime.datetime.now()
printer_cam_running_last_reported = datetime.datetime.now()

# Define LED lights GPIO
power_off_led = LED(4, pin_factory=factory)

# Define buttons GPIO
pi_power_button = Button(3, hold_time=3, pin_factory=factory)

# Subscribe to topic for camera button
def on_mqtt_connect(client, userdata, flags, rc):
  logging.info("Connected to MQTT broker with result code " + str(rc))
  mqttClient.subscribe("prusashelf/buttonPressed")
  mqttClient.subscribe("prusashelf/queryDeviceStatus")

def reportDeviceStatus():
  logging.info("Reporting device status as MQTT messages. The next switchStateChanged message will not be real changes, just an update of the current status.")
  if printer_cam_running:
    mqttClient.publish("prusashelf/switchStateChanged", "camera: on")
  else:
    mqttClient.publish("prusashelf/switchStateChanged", "camera: off")

# Callback for incoming messages on MQTT topic
def on_mqtt_message(client, userdata, msg):
  logging.info(f"Message received on topic {msg.topic}: {msg.payload.decode()}")
  if msg.topic == "prusashelf/buttonPressed":
    button = msg.payload.decode()
    if button == "camera":
      switch_printer_cam()
  if (msg.topic == "prusashelf/queryDeviceStatus"):
    reportDeviceStatus()

# Log events from MQTT library
def on_mqtt_log(client, userdata, paho_log_level, message):
  if paho_log_level == mqtt.LogLevel.MQTT_LOG_ERR:
    logging.error(message)
  elif paho_log_level == mqtt.LogLevel.MQTT_LOG_WARNING:
    logging.warning(message)
  elif paho_log_level == mqtt.LogLevel.MQTT_LOG_INFO or paho_log_level == mqtt.LogLevel.MQTT_LOG_NOTICE:
    logging.info(message)
  elif paho_log_level == mqtt.LogLevel.MQTT_LOG_DEBUG:
    logging.debug(message)

# Raspberry Pi power button
def shutdown():
  logging.debug("Shutdown triggered")
  
  # Shutdown camera process and update button panel before shutting down the RPi
  os.system("sudo pkill -f /home/gidverksted/send-snapshot-to-prusaconnect.sh &")
  mqttClient.publish("prusashelf/switchStateChanged", "camera: off")

  # Start shutting down the RPi
  power_off_led.on()
  os.system("sudo shutdown -h now")
  logging.info("Shutdown")
pi_power_button.when_held = shutdown

# Printer camera snapshots
def switch_printer_cam():
  global printer_cam_running
  global printer_cam_led_toggled_at
  logging.debug("Switch printer cam triggered")
  if printer_cam_running:
    os.system("sudo pkill -f /home/gidverksted/send-snapshot-to-prusaconnect.sh &")
    printer_cam_running = False
    mqttClient.publish("prusashelf/switchStateChanged", "camera: off")
    logging.info("Printer cam turned off")
  else:
    printer_cam_led_toggled_at = time.time()
    os.system("sudo /home/gidverksted/send-snapshot-to-prusaconnect.sh &")
    printer_cam_running = True
    mqttClient.publish("prusashelf/switchStateChanged", "camera: on")
    logging.info("Printer cam turned on")

# Initialize a time variable to watch status of printer cam
printer_cam_led_toggled_at = time.time()

def test_camera_snapshot_status():
  global printer_cam_running
  global printer_cam_led_toggled_at
  global printer_cam_error_status_logged_at
  global printer_cam_running_last_reported
  cam_image_file_age_in_seconds = None
  try:
    try:
      with open("/home/gidverksted/snapshot-timestamp.txt", "r") as f:
        uploaded_at = f.read().strip()
    except:
      logging.warning("No timestamp file at /home/gidverksted/snapshot-timestamp.txt")

    if uploaded_at:
      try:
        uploaded_time = datetime.datetime.strptime(uploaded_at, r"%Y-%m-%d %H:%M:%S").timestamp()
        cam_image_file_age_in_seconds = time.time() - uploaded_time

        # Report camera running every 5s if the image uploaded was less than 10s ago
        if (cam_image_file_age_in_seconds < 10) and (datetime.datetime.now() - printer_cam_running_last_reported).total_seconds() >= 5:
          msg_info = mqttClient.publish("prusashelf/cameraRunning", "true")
          msg_info.wait_for_publish()
          printer_cam_running_last_reported = datetime.datetime.now()
          return
      except ValueError:
        logging.warning("Invalid timestamp format in environment variable")

    if printer_cam_running and cam_image_file_age_in_seconds > 10 and (datetime.datetime.now() - printer_cam_error_status_logged_at).total_seconds() > 60:
      logging.warning("Printer cam is not running")
      printer_cam_error_status_logged_at = datetime.datetime.now()
  except Exception as Argument:
    logging.exception("Unable to detect camera status")

# Connect to MQTT broker
mqttClient = mqtt.Client()
mqttClient.username_pw_set(parameters.mqtt_username, parameters.mqtt_password)
mqttClient.on_connect = on_mqtt_connect
mqttClient.on_message = on_mqtt_message
mqttClient.connect(parameters.mqtt_server, 1883, 60)
mqttClient.loop_start()

# Make sure to update the button panel with the correct status of the camera button if this process restarts
os.system("sudo pkill -f /home/gidverksted/send-snapshot-to-prusaconnect.sh &")
mqttClient.publish("prusashelf/switchStateChanged", "camera: off")

while True:
  test_camera_snapshot_status()

  # Run loop two times a second  
  time.sleep(0.5)
