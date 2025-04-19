#include <WiFi.h>
#include <PubSubClient.h>
#include "time.h"
#include "esp_sntp.h"
#include "parameters.h"

const int switchPins[] = { 15, // printer
                            2, // enclosure light
                            4, // enclosure fan
                            16 // room light
                            };
const int numSwitches = sizeof(switchPins) / sizeof(switchPins[0]);
volatile bool switchStates[numSwitches] = { false };

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);  // MQTT

void printLocalTime() {
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo)) {
    Serial.println("No time available (yet)");
    return;
  }
  Serial.println(&timeinfo, "%A, %B %d %Y %H:%M:%S");
}

// Callback function (gets called when time adjusts via NTP)
void timeavailable(struct timeval *t) {
  Serial.println("Got time adjustment from NTP!");
  printLocalTime();
}

void updateSwitches() {
  for (int i = 0; i < numSwitches; i++) {
    if (switchStates[i]) {
      digitalWrite(switchPins[i], HIGH);
    } else {
      digitalWrite(switchPins[i], LOW);
    }
  }
}

const char* getSwitchType(int index) {
  switch(index) {
    case 0: return "printer";
    case 1: return "enclosureLight";
    case 2: return "enclosureFan";
    case 3: return "roomLight";
    default: return "unknown";
  }
}

void changeSwitch(const char *type) {
  int pinIndex = -1;

  // Find which switch in the array corresponds to the type
  for (int index = 0; index < numSwitches; index++) {
    if (strcmp(type, getSwitchType(index)) == 0) {
      pinIndex = index;
      break;
    }
  }

  if (pinIndex >= 0) {
    switchStates[pinIndex] = !switchStates[pinIndex];
    char mqttMessage[50];

    if (switchStates[pinIndex]) {
      digitalWrite(switchPins[pinIndex], HIGH);
      snprintf(mqttMessage, sizeof(mqttMessage), "%s: on", type);
      mqttClient.publish("prusashelf/switchStateChanged", mqttMessage);
      Serial.printf("Published %s to topic prusashelf/switchStateChanged\n", mqttMessage);
    } else {
      digitalWrite(switchPins[pinIndex], LOW);
      snprintf(mqttMessage, sizeof(mqttMessage), "%s: off", type);
      mqttClient.publish("prusashelf/switchStateChanged", mqttMessage);
      Serial.printf("Published %s to topic prusashelf/switchStateChanged\n", mqttMessage);
    }
  } else {
    Serial.printf("Invalid switch type %s\n", type);
  }
}

void reportDeviceStatus() {
  Serial.println("Reporting device status as MQTT messages. The next switchStateChanged message will not be real changes, just an update of the current status.");

  for (int i = 0; i < numSwitches; i++) {
    char mqttMessage[50];
    const char* type = getSwitchType(i);
    
    if (switchStates[i]) {
      snprintf(mqttMessage, sizeof(mqttMessage), "%s: on", type);
    } else {
      snprintf(mqttMessage, sizeof(mqttMessage), "%s: off", type);
    }
    
    mqttClient.publish("prusashelf/switchStateChanged", mqttMessage);
    Serial.printf("Published %s to topic prusashelf/switchStateChanged\n", mqttMessage);
  }
}

void incomingMqttMessage(char *topic, uint8_t *message, unsigned int length) {
  Serial.print("Message received on topic: ");
  Serial.println(topic);

  Serial.print("Message: ");

  String value = "";

  for (int i = 0; i < length; i++) {
    Serial.print((char)message[i]);
    value += (char)message[i];
  }

  Serial.println();

  if (strcmp(topic, "prusashelf/buttonPressed") == 0) {
    changeSwitch(value.c_str());
  } else if (strcmp(topic, "prusashelf/queryDeviceStatus") == 0) {
    reportDeviceStatus();
  }
}

void reconnectMqttBroker() {
  while (!mqttClient.connected()) {
    Serial.printf("Connecting to %s...\n", mqttServer);

    if (mqttClient.connect("PrusaShelfSwitchBox", mqtt_user, mqtt_password)) {
      Serial.printf("connected to %s\n", mqttServer);
    } else {
      Serial.print("Failed, rc=");
      Serial.println(mqttClient.state());
      delay(2000);
    }
  }

  subscribeToMqttTopics();
}

void subscribeToMqttTopics() {
  if (mqttClient.subscribe("prusashelf/buttonPressed")) {
    Serial.println("Subscribed to topic: prusashelf/buttonPressed");
  } else {
    Serial.println("Failed to subscribe to topic!");
  }

  if (mqttClient.subscribe("prusashelf/queryDeviceStatus")) {
    Serial.println("Subscribed to topic: prusashelf/queryDeviceStatus");
  } else {
    Serial.println("Failed to subscribe to topipc!");
  }
}

void setup() {
  Serial.begin(115200);

  // Setup IO pins for LEDs
  for (int i = 0; i < numSwitches; i++) {
    pinMode(switchPins[i], OUTPUT);
  }

  // First step is to configure WiFi STA and connect in order to get the current time and date.
  Serial.printf("Connecting to %s ", wifi_ssid);
  WiFi.begin(wifi_ssid, wifi_password);

  /**
   * NTP server address could be acquired via DHCP,
   *
   * NOTE: This call should be made BEFORE esp32 acquires IP address via DHCP,
   * otherwise SNTP option 42 would be rejected by default.
   * NOTE: configTime() function call if made AFTER DHCP-client run
   * will OVERRIDE acquired NTP server address
   */
  esp_sntp_servermode_dhcp(1);  // (optional)

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(" CONNECTED");

  // set notification call-back function
  sntp_set_time_sync_notification_cb(timeavailable);

  /**
   * This will set configured ntp servers and constant TimeZone/daylightOffset
   * should be OK if your time zone does not need to adjust daylightOffset twice a year,
   * in such a case time adjustment won't be handled automagically.
   */
  configTime(gmtOffset_sec, daylightOffset_sec, ntpServer1, ntpServer2);

  /**
   * A more convenient approach to handle TimeZones with daylightOffset
   * would be to specify a environment variable with TimeZone definition including daylight adjustmnet rules.
   * A list of rules for your zone could be obtained from https://github.com/esp8266/Arduino/blob/master/cores/esp8266/TZ.h
   */
  //configTzTime(time_zone, ntpServer1, ntpServer2);

  // Connect to MQTT broker
  mqttClient.setServer(mqttServer, 1883);
  mqttClient.setCallback(incomingMqttMessage);

  if (!mqttClient.connected()) {
    reconnectMqttBroker();
  }  
}

void loop() {
  if (!mqttClient.connected()) {
    reconnectMqttBroker();
  }

  mqttClient.loop();  // Process incoming MQTT messages

  updateSwitches();
  delay(100);
  //printLocalTime();  // it will take some time to sync time :)
}
