#include <Arduino.h>
#include <Adafruit_MCP23X17.h>

#define BOARD_LED 2  // The onboard LED for detecting any issues. It should be blinking.
#define LED_PIN 0     // MCP23XXX pin LED is attached to
#define BUTTON_PIN 15  // MCP23XXX pin button is attached to
Adafruit_MCP23X17 mcp;

void setup() {  
  Serial.begin(9600);
  Serial.println("MCP23xxx Blink test");

  pinMode(BOARD_LED, OUTPUT);
  bool initialized = false;

  while (!initialized) {
    if (!mcp.begin_I2C(0x20)) {
      digitalWrite(BOARD_LED, HIGH);
      Serial.println("Error");
      sleep(1000);
    } else {
      initialized = true;
    }
  }

  digitalWrite(BOARD_LED, LOW);
  mcp.pinMode(LED_PIN, OUTPUT);
  mcp.pinMode(BUTTON_PIN, INPUT_PULLUP);
  Serial.println("Looping...");
}

void loop() {
  digitalWrite(BOARD_LED, HIGH);
  
  if (mcp.digitalRead(BUTTON_PIN)) {
    mcp.digitalWrite(LED_PIN, HIGH);
    Serial.println("LED is on");
  } else {
    mcp.digitalWrite(LED_PIN, LOW);
    Serial.println("LED is off");
  }

  delay(500);
  digitalWrite(BOARD_LED, LOW);
  delay(500);
}