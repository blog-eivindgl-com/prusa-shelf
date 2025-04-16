#include <WiFi.h>
#include <PubSubClient.h>
#include "time.h"
#include "esp_sntp.h"
#include "parameters.h"

const int buttonPrinterPin = 15;
volatile bool isButtonPrinterPressed = false;
unsigned long buttonPrinterPressStartTime = 0;

/*
const int buttonEnclosureLightPin = 2;
const int buttonCameraPin = 4;
const int buttonEnclosureFanPin = 16;
const int buttonFreePin = 17;
*/

const int buttonPins[] = { 2, 4, 16, 17 };
const int numButtons = sizeof(buttonPins) / sizeof(buttonPins[0]);
volatile bool buttonStates[numButtons] = { false };
volatile bool buttonStateChanged[numButtons] = { false };

const int ledPins[] = { 13, 12, 14, 27, 26, 25 };
const int numLeds = sizeof(ledPins) / sizeof(ledPins[0]);
volatile bool ledStates[numLeds] = { false };

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

void checkButtonsHeld() {
  int buttonPrinter = digitalRead(buttonPrinterPin);

  if (buttonPrinter == LOW) {
    if (!isButtonPrinterPressed) {
      buttonPrinterPressStartTime = millis();  // Time when button was first pressed
      isButtonPrinterPressed = true;
    } else if (millis() - buttonPrinterPressStartTime >= 3000) {
      Serial.println("Printer power button is held for more than 3 seconds!");
      isButtonPrinterPressed = false;
      mqttClient.publish("prusashelf/buttonPressed", "printer");
      Serial.println("Published printer to topic prusashelf/buttonPressed");
    }
  } else {
    isButtonPrinterPressed = false;  // Button is released
  }
}

void checkButtonStates() {
  for (int i = 0; i < numButtons; i++) {
    if (buttonStateChanged[i]) {
      buttonStateChanged[i] = false;

      if (buttonStates[i]) {
        Serial.printf("Button %d was pressed!\n", buttonPins[i]);
        char* value = "";

        switch(i) {
          case 0:
            value = "enclosureLight";
            break;
          case 1:
            value = "camera";
            break;
          case 2:
            value = "enclosureFan";
            break;
        }

        if (value != "") {
          mqttClient.publish("prusashelf/buttonPressed", value);
          Serial.printf("Published %s to topic prusashelf/buttonPressed\n", value);
        }
      } else {
        Serial.printf("Button %d was released!\n", buttonPins[i]);
      }
    }
  }
}

void setLedState(const char *switchState) {
  int ledIndex = -1;

  // Expect switchState to contain values like "<switch>: on/off"
  const char *delimiter = strchr(switchState, ':');

  if (delimiter == nullptr) {
    Serial.println("Invalid structure of message. Expected <switch>: on/off");
    return;
  }

  // Extract the part before the colon which is the name of the switch
  int keyLength = delimiter - switchState;
  char switchName[keyLength + 1];
  strncpy(switchName, switchState, keyLength);
  switchName[keyLength] = '\0';  // Null-terminate the string

  // Extract the part after the colon, which is the on/off state of the switch
  const char *stateValue = delimiter + 1;
  while (*stateValue == ' ') stateValue++; // Skip spaces

  if (strcmp(switchName, "printer") == 0) {
    ledIndex = 0;
  } else if (strcmp(switchName, "enclosureLight") == 0) {
    ledIndex = 1;
  } else if (strcmp(switchName, "camera") == 0) {
    ledIndex = 2;
  } else if (strcmp(switchName, "enclosureFan") == 0) {
    ledIndex = 4; // 3 is yellow led to indicate running camera
  } else {
    Serial.printf("Invalid switch %s\n", switchName);
  }

  if (strcmp(stateValue, "on") == 0) {
    Serial.printf("%s is turned ON\n", switchName);
    ledStates[ledIndex] = true;
  } else if (strcmp(stateValue, "off") == 0) {
    Serial.printf("%s is turned OFF\n", switchName);
    ledStates[ledIndex] = false;
  } else {
    Serial.printf("Invalid state for %s: %s\n", switchName, stateValue);
  }
}

void updateLeds() {
  for (int i = 0; i < numLeds; i++) {
    if (ledStates[i]) {
      digitalWrite(ledPins[i], HIGH);
    } else {
      digitalWrite(ledPins[i], LOW);
    }
  }
}

void IRAM_ATTR handleButtonInterrupt() {
  for (int i = 0; i < numButtons; i++) {
    if (buttonStates[i] == false && digitalRead(buttonPins[i]) == LOW) {
      buttonStates[i] = true;
      buttonStateChanged[i] = true;
    } else if (buttonStates[i] == true && digitalRead(buttonPins[i]) == HIGH) {
      buttonStates[i] = false;
      buttonStateChanged[i] = true;
    }
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

  if (strcmp(topic, "prusashelf/switchStateChanged") == 0) {
    setLedState(value.c_str());
  }
}

void reconnectMqttBroker() {
  while (!mqttClient.connected()) {
    Serial.printf("Connecting to %s...\n", mqttServer);

    if (mqttClient.connect("PrusaShelfButtonPanel", mqtt_user, mqtt_password)) {
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
  if (mqttClient.subscribe("prusashelf/switchStateChanged")) {
    Serial.println("Subscribed to topic: prusashelf/switchStateChanged");
  } else {
    Serial.println("Failed to subscribe to topic!");
  }
}

void setup() {
  Serial.begin(115200);

  // Setup IO pins for buttons
  pinMode(buttonPrinterPin, INPUT_PULLUP);  // This button must be held before triggering an action
  
  for (int i = 0; i < numButtons; i++) {
    pinMode(buttonPins[i], INPUT_PULLUP);
    attachInterrupt(buttonPins[i], handleButtonInterrupt, CHANGE);
  }

  // Setup IO pins for LEDs
  for (int i = 0; i < numLeds; i++) {
    pinMode(ledPins[i], OUTPUT);
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

  mqttClient.loop(); // Process incoming MQTT messages

  checkButtonsHeld();
  checkButtonStates();
  updateLeds();
  delay(100);
  //printLocalTime();  // it will take some time to sync time :)
}
