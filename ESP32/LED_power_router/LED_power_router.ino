#include <Arduino.h>
#include <FastLED.h>

#define LED_PIN    5
#define LED_COUNT  600  // enough for all runs
#define BRIGHTNESS 50

CRGB leds[LED_COUNT];

// ======================= RUN MAP ============================
const int NUM_RUNS = 19;
const int runLengths[NUM_RUNS] = {
  56, 2, 7, 44, 4, 11, 17, 61, 37, 29,
  38, 19, 21, 30, 5, 27, 21, 11, 20
};
int runStart[NUM_RUNS];

// ======================= HELPERS ============================
void setRunColor(int runIndex, const CRGB& color) {
  if (runIndex < 1 || runIndex > NUM_RUNS) return;
  int idx = runIndex - 1;
  for (int i = 0; i < runLengths[idx]; i++) {
    leds[runStart[idx] + i] = color;
  }
  FastLED.show();
}

void clearRun(int runIndex) {
  setRunColor(runIndex, CRGB::Black);
}

// ======================= SETUP ===============================
void setup() {
  Serial.begin(115200);
  FastLED.addLeds<WS2812B, LED_PIN, GRB>(leds, LED_COUNT);
  FastLED.setBrightness(BRIGHTNESS);

  // Compute run start indices
  int total = 0;
  for (int i = 0; i < NUM_RUNS; i++) {
    runStart[i] = total;
    total += runLengths[i];
  }

  Serial.printf("Total LEDs: %d\n", total);

  // Light each run briefly
  for (int i = 1; i <= NUM_RUNS; i++) {
    setRunColor(i, CRGB::Blue);
    delay(200);
    clearRun(i);
  }
}

// ======================= LOOP ================================
void loop() {
  // Example: pulse run 1 red
  setRunColor(1, CRGB::Red);
  delay(500);
  clearRun(1);
  delay(500);
}


// ============================================================================
// Main Program
// ============================================================================

//void setup() {
//  Serial.begin(115200);
//  Serial2.begin(9600, SERIAL_8N1, 16, 17); // UART2 on GPIO16=RX, GPIO17=TX
//
//  LEDMap subwayMap; 
//
//  FastLED.addLeds<WS2812B, LED_PIN, GRB>(leds, LED_COUNT);
//  FastLED.setBrightness(BRIGHTNESS);
//
//  Serial.println("ESP32 LED controller ready (UART mode, FastLED).");
//
//  // Example: Turn on all LEDs for route 1 in blue
//  subwayMap.routes[0].setAll(CRGB::Blue);
//  delay(1000);
//  subwayMap.routes[0].setAll(CRGB::Black);
//}
//
//void loop() {
//  // Example animation: walk a red dot through all LEDs
//  for (int i = 0; i < LED_COUNT; i++) {
//    leds[i] = CRGB::Red;
//    FastLED.show();
//    delay(50);
//    leds[i] = CRGB::Black;
//  }
//}
