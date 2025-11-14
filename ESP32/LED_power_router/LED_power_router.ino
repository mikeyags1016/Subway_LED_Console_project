#include <Arduino.h>
#include <FastLED.h>

#define LED_PIN_1   5
#define LED_PIN_2   4
#define LED_COUNT_1 300   // number of LEDs on pin 5
#define LED_COUNT_2 300   // number of LEDs on pin 4
#define BRIGHTNESS  5

CRGB leds1[LED_COUNT_1];
CRGB leds2[LED_COUNT_2];

// ======================= SETUP ===============================
void setup() {
  Serial.begin(115200);

  // Initialize both LED runs
  FastLED.addLeds<WS2812B, LED_PIN_1, GRB>(leds1, LED_COUNT_1);
  FastLED.addLeds<WS2812B, LED_PIN_2, GRB>(leds2, LED_COUNT_2);
  FastLED.setBrightness(BRIGHTNESS);

  // Turn first run (pin 5) red
  fill_solid(leds1, LED_COUNT_1, CRGB::Red);

  // Turn second run (pin 4) blue
  fill_solid(leds2, LED_COUNT_2, CRGB::Blue);

  FastLED.show();
}

// ======================= LOOP ================================
void loop() {
  // Keep colors constant — nothing needed here
}
