#include <Arduino.h>
#include <Adafruit_MCP23X17.h>
#include "M5Dial.h"
#include <M5GFX.h>
 /* @Hardwares: M5Dial
 * @Platform Version: Arduino M5Stack Board Manager v2.0.7
 * @Dependent Library:
 * M5GFX: https://github.com/m5stack/M5GFX
 * M5Unified: https://github.com/m5stack/M5Unified
 */

#define LED_PIN 0     // MCP23XXX pin LED is attached to
#define BLINKING_LED 8
#define BUTTON_PIN 15  // MCP23XXX pin button is attached to
Adafruit_MCP23X17 mcp;
M5GFX display;
M5Canvas canvas(&display);
int flag;

void setup() {
  Serial.println("Initializing M5 display...");
  // Initialize M5Dial display
  display.begin();

  if (display.isEPD())
  {
    display.setEpdMode(epd_mode_t::epd_fastest);
    display.invertDisplay(true);
    display.clear(TFT_BLACK);
  }
  if (display.width() < display.height())
  {
    display.setRotation(display.getRotation() ^ 1);
  }

  canvas.setColorDepth(1); // mono color
  canvas.createSprite(display.width(), display.height());
  canvas.setTextSize((float)canvas.width() / 160);

  // Initialize MCP23017 I2C communication for two devices
  Serial.println("MCP23xxx Blink test");

  bool initialized = false;

  while (!initialized) {
    if (!mcp.begin_I2C(0x21)) {
      Serial.println("Error");
      canvas.printf("%s\r\n", "Error");
      canvas.pushSprite(0, 0);
      sleep(1000);
    } else {
      initialized = true;
    }
  }

  flag = 0;
  mcp.pinMode(LED_PIN, OUTPUT);
  mcp.pinMode(BUTTON_PIN, INPUT_PULLUP);
  Serial.println("Looping...");
}

void loop() { 
  // Display something to debug the communication over I2C
  int x = display.width() / 2;
  int y = display.height() / 2;
  canvas.printf("%s\r\n", "Test");
  canvas.pushSprite(0, 0);

  mcp.digitalWrite(BLINKING_LED, HIGH);

  //if (mcp.digitalRead(BUTTON_PIN)) {
  if (flag == 0) {
    flag = 1;
    mcp.digitalWrite(LED_PIN, HIGH);
    Serial.println("LED is on");
  } else {
    flag = 0;
    mcp.digitalWrite(LED_PIN, LOW);
    Serial.println("LED is off");
  }

  delay(500);
  mcp.digitalWrite(BLINKING_LED, LOW);
  delay(500);
}