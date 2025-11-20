//#include <Arduino.h>
//#include <FastLED.h>
//#include <map>
//#include <ArduinoJson.h>
//
//#define NUM_RUNS  20
//#define LEDS_PER_RUN 300
//#define BRIGHTNESS 5
//
//struct StationInfo {
//  int run;
//  int index;
//};
//
//std::map<String, StationInfo> stationMap;
//
//CRGB leds[NUM_RUNS][LEDS_PER_RUN];
//
//void setup() {
//  Serial.begin(115200);
//  FastLED.setBrightness(BRIGHTNESS);
//
//  // All your LED pins
//  FastLED.addLeds<WS2812B, 2,  GRB>(leds[0],  LEDS_PER_RUN);
//  FastLED.addLeds<WS2812B, 3,  GRB>(leds[1],  LEDS_PER_RUN);
//  FastLED.addLeds<WS2812B, 4,  GRB>(leds[2],  LEDS_PER_RUN);
//  FastLED.addLeds<WS2812B, 5,  GRB>(leds[3],  LEDS_PER_RUN);
//  FastLED.addLeds<WS2812B, 12, GRB>(leds[4],  LEDS_PER_RUN);
//  FastLED.addLeds<WS2812B, 13, GRB>(leds[5],  LEDS_PER_RUN);
//  FastLED.addLeds<WS2812B, 14, GRB>(leds[6],  LEDS_PER_RUN);
//  FastLED.addLeds<WS2812B, 15, GRB>(leds[7],  LEDS_PER_RUN);
//  FastLED.addLeds<WS2812B, 16, GRB>(leds[8],  LEDS_PER_RUN);
//  FastLED.addLeds<WS2812B, 17, GRB>(leds[9],  LEDS_PER_RUN);
//  FastLED.addLeds<WS2812B, 18, GRB>(leds[10], LEDS_PER_RUN);
//  FastLED.addLeds<WS2812B, 19, GRB>(leds[11], LEDS_PER_RUN);
//  FastLED.addLeds<WS2812B, 21, GRB>(leds[12], LEDS_PER_RUN);
//  FastLED.addLeds<WS2812B, 22, GRB>(leds[13], LEDS_PER_RUN);
//  FastLED.addLeds<WS2812B, 23, GRB>(leds[14], LEDS_PER_RUN);
//  FastLED.addLeds<WS2812B, 25, GRB>(leds[15], LEDS_PER_RUN);
//  FastLED.addLeds<WS2812B, 26, GRB>(leds[16], LEDS_PER_RUN);
//  FastLED.addLeds<WS2812B, 27, GRB>(leds[17], LEDS_PER_RUN);
//  FastLED.addLeds<WS2812B, 32, GRB>(leds[18], LEDS_PER_RUN);
//  FastLED.addLeds<WS2812B, 33, GRB>(leds[19], LEDS_PER_RUN);
//
//  // ------------------ Your JSON string ------------------
//  String input =
//    "{\"255S\":{\"run\":3,\"index\":2,\"name\":\"Pennsylvania Av (3)\"},"
//    "\"254N\":{\"run\":2,\"index\":3,\"name\":\"Junius St (3)\"},"
//    "\"254S\":{\"run\":3,\"index\":100,\"name\":\"Junius St (3)\"}}";
//
//  // ------------------ JSON Parsing ----------------------
//  StaticJsonDocument<4096> doc;
//  DeserializationError err = deserializeJson(doc, input);
//
//  if (err) {
//    Serial.println("JSON parse error!");
//    Serial.println(err.c_str());
//    return;
//  }
//
//  // Convert JSON to stationMap
//  for (JsonPair kv : doc.as<JsonObject>()) {
//    String stationID = kv.key().c_str();
//    JsonObject obj = kv.value();
//
//    int run   = obj["run"];
//    int index = obj["index"];
//
//    stationMap[stationID] = { run, index };
//
//    Serial.print("Loaded station: ");
//    Serial.print(stationID);
//    Serial.print(" → run=");
//    Serial.print(run);
//    Serial.print(" index=");
//    Serial.println(index);
//  }
//
//  // ------------------ Light LEDs ------------------
//  for (int r = 0; r < NUM_RUNS; r++) {
//    fill_solid(leds[r], LEDS_PER_RUN, CRGB::Black);
//  }
//
//  // Turn on LEDs based on parsed data
//  for (auto &p : stationMap) {
//    int run = p.second.run;
//    int idx = p.second.index;
//
//    if (run >= 0 && run < NUM_RUNS &&
//        idx >= 0 && idx < LEDS_PER_RUN) {
//      leds[run][idx] = CRGB::Red;
//    }
//  }
//
//  FastLED.show();
//}
//
//void loop() {}

#include <Arduino.h>
#include <FastLED.h>
#include <ArduinoJson.h>

#define LED_PIN     5        // change this to your LED data pin
#define LED_PIN_2   4
#define LED_COUNT   100       // number of LEDs you want to turn on
#define BRIGHTNESS  50       // brightness 0–255

CRGB leds[LED_COUNT];
CRGB leds_2[LED_COUNT];

String path = "";

void setup() {
  Serial.begin(115200); 
  Serial1.begin(115200, SERIAL_8N1, 18, 19);
  delay(500);
  Serial.println("ESP32 UART ready (RX=16, TX=17)");
  
  FastLED.addLeds<WS2812B, LED_PIN, GRB>(leds, LED_COUNT);
  FastLED.addLeds<WS2812B, LED_PIN_2, GRB>(leds_2, LED_COUNT);
  FastLED.setBrightness(BRIGHTNESS);

  fill_solid(leds, LED_COUNT, CRGB::Black);
  fill_solid(leds_2, LED_COUNT, CRGB::Black);

  for (int i = 56; i < 60; i++) {
    leds[i] = CRGB::Red; 
  }
  for (int i = 56; i < 60; i++) {
    leds_2[i] = CRGB::Blue; 
  }
  FastLED.show();
  
  // Serial
//  if (Serial1.available()) {
//    int b = Serial1.read();
//    Serial.print("Char: ");
//    Serial.println((char)b);
//  }
}

void loop() {
  // Read JSON text over Serial1
  while (Serial1.available()) {
    char c = Serial.read();

    if (c=='\n') {
      parseJson(path);
      path = "";
    }
    else {
      path += c;
    }
  } 
}

void parseJson(const String &json) {
  StaticJsonDocument<256> doc;
  DeserializationError err = deserialization(doc, json);

  if (err) {
    Serial.print("JSON Error: ");
    Serial.println(err.c_str());
    return;
  }

  for (JsonPair kv : doc.as<JsonObject>()) {
      const char* station_id = kv.key().c_str();  
      JsonObject info = kv.value().as<JsonObject>();
  
      int run = info["run"];
      int index = info["index"];
      const char* name = info["name"];
  
      Serial.println("----- Station -----");
      Serial.print("ID: ");    Serial.println(station_id);
      Serial.print("run: ");   Serial.println(run);
      Serial.print("index: "); Serial.println(index);
      Serial.print("name: ");  Serial.println(name);
  
      // Example: light LEDs based on run/index
      if (run == 0) {
        leds[index] = CRGB::Blue;
      } else {
        leds_2[index] = CRGB::Red;
      }
    }
  
    FastLED.show();
  }
}