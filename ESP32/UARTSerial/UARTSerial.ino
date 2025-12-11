////#include <Arduino.h>
////#include <FastLED.h>
////#include <map>
////#include <ArduinoJson.h>
////
////#define NUM_RUNS  20
////#define LEDS_PER_RUN 300
////#define BRIGHTNESS 5
////
////struct StationInfo {
////  int run;
////  int index;
////};
////
////std::map<String, StationInfo> stationMap;
////
////CRGB leds[NUM_RUNS][LEDS_PER_RUN];
////
////void setup() {
////  Serial.begin(115200);
////  FastLED.setBrightness(BRIGHTNESS);
////
////  // All your LED pins
////  FastLED.addLeds<WS2812B, 2,  GRB>(leds[0],  LEDS_PER_RUN);
////  FastLED.addLeds<WS2812B, 3,  GRB>(leds[1],  LEDS_PER_RUN);
////  FastLED.addLeds<WS2812B, 4,  GRB>(leds[2],  LEDS_PER_RUN);
////  FastLED.addLeds<WS2812B, 5,  GRB>(leds[3],  LEDS_PER_RUN);
////  FastLED.addLeds<WS2812B, 12, GRB>(leds[4],  LEDS_PER_RUN);
////  FastLED.addLeds<WS2812B, 13, GRB>(leds[5],  LEDS_PER_RUN);
////  FastLED.addLeds<WS2812B, 14, GRB>(leds[6],  LEDS_PER_RUN);
////  FastLED.addLeds<WS2812B, 15, GRB>(leds[7],  LEDS_PER_RUN);
////  FastLED.addLeds<WS2812B, 16, GRB>(leds[8],  LEDS_PER_RUN);
////  FastLED.addLeds<WS2812B, 17, GRB>(leds[9],  LEDS_PER_RUN);
////  FastLED.addLeds<WS2812B, 18, GRB>(leds[10], LEDS_PER_RUN);
////  FastLED.addLeds<WS2812B, 19, GRB>(leds[11], LEDS_PER_RUN);
////  FastLED.addLeds<WS2812B, 21, GRB>(leds[12], LEDS_PER_RUN);
////  FastLED.addLeds<WS2812B, 22, GRB>(leds[13], LEDS_PER_RUN);
////  FastLED.addLeds<WS2812B, 23, GRB>(leds[14], LEDS_PER_RUN);
////  FastLED.addLeds<WS2812B, 25, GRB>(leds[15], LEDS_PER_RUN);
////  FastLED.addLeds<WS2812B, 26, GRB>(leds[16], LEDS_PER_RUN);
////  FastLED.addLeds<WS2812B, 27, GRB>(leds[17], LEDS_PER_RUN);
////  FastLED.addLeds<WS2812B, 32, GRB>(leds[18], LEDS_PER_RUN);
////  FastLED.addLeds<WS2812B, 33, GRB>(leds[19], LEDS_PER_RUN);
////
////  // ------------------ Your JSON string ------------------
////  String input =
////    "{\"255S\":{\"run\":3,\"index\":2,\"name\":\"Pennsylvania Av (3)\"},"
////    "\"254N\":{\"run\":2,\"index\":3,\"name\":\"Junius St (3)\"},"
////    "\"254S\":{\"run\":3,\"index\":100,\"name\":\"Junius St (3)\"}}";
////
////  // ------------------ JSON Parsing ----------------------
////  StaticJsonDocument<4096> doc;
////  DeserializationError err = deserializeJson(doc, input);
////
////  if (err) {
////    Serial.println("JSON parse error!");
////    Serial.println(err.c_str());
////    return;
////  }
////
////  // Convert JSON to stationMap
////  for (JsonPair kv : doc.as<JsonObject>()) {
////    String stationID = kv.key().c_str();
////    JsonObject obj = kv.value();
////
////    int run   = obj["run"];
////    int index = obj["index"];
////
////    stationMap[stationID] = { run, index };
////
////    Serial.print("Loaded station: ");
////    Serial.print(stationID);
////    Serial.print(" → run=");
////    Serial.print(run);
////    Serial.print(" index=");
////    Serial.println(index);
////  }
////
////  // ------------------ Light LEDs ------------------
////  for (int r = 0; r < NUM_RUNS; r++) {
////    fill_solid(leds[r], LEDS_PER_RUN, CRGB::Black);
////  }
////
////  // Turn on LEDs based on parsed data
////  for (auto &p : stationMap) {
////    int run = p.second.run;
////    int idx = p.second.index;
////
////    if (run >= 0 && run < NUM_RUNS &&
////        idx >= 0 && idx < LEDS_PER_RUN) {
////      leds[run][idx] = CRGB::Red;
////    }
////  }
////
////  FastLED.show();
////}
////
////void loop() {}
//
#include <Arduino.h>
#include <FastLED.h>

#define LED_PIN_0   23 // Run 0
#define LED_PIN_1   2 // Run 0
#define LED_PIN_2   5
#define LED_PIN_3   15
#define LED_PIN_4   21
#define LED_PIN_5   13        
#define LED_PIN_6   22
#define LED_PIN_7   21        
#define LED_PIN_8   24
#define LED_PIN_9   1        // change this to your LED data pin
#define LED_PIN_10  3
#define LED_PIN_11  4        
#define LED_PIN_12  5
#define LED_PIN_13  6        // change this to your LED data pin
#define LED_PIN_14  7
#define LED_PIN_15  8        
#define LED_PIN_16  9
#define LED_PIN_17  10
#define LED_PIN_18  11        
#define LED_PIN_19  12
#define LED_COUNT   100       // number of LEDs you want to turn on
#define BRIGHTNESS  50       // brightness 0–255

CRGB leds_0[LED_COUNT];
CRGB leds_1[LED_COUNT];
CRGB leds_2[LED_COUNT];
CRGB leds_3[LED_COUNT];
CRGB leds_4[LED_COUNT];
CRGB leds_5[LED_COUNT];
CRGB leds_6[LED_COUNT];
CRGB leds_7[LED_COUNT];
CRGB leds_8[LED_COUNT];
CRGB leds_9[LED_COUNT];
CRGB leds_10[LED_COUNT];
CRGB leds_11[LED_COUNT];
CRGB leds_12[LED_COUNT];
CRGB leds_13[LED_COUNT];
CRGB leds_14[LED_COUNT];
CRGB leds_15[LED_COUNT];
CRGB leds_16[LED_COUNT];
CRGB leds_17[LED_COUNT];
CRGB leds_18[LED_COUNT];
CRGB leds_19[LED_COUNT];

// Struct to hold parsed command values
struct ParsedCommand {
 int run;
 int index;
 byte r, g, b;
 bool valid;
 bool end;
};

// Helper function to parse and return values
ParsedCommand parseInputLine(const String &line) {
 ParsedCommand cmd = {0, 0, 0, 0, 0, false, false};
 if (line.equalsIgnoreCase("END")) {
   cmd.end = true;
   cmd.valid = true;
   return cmd;
 }
 int firstComma = line.indexOf(',');
 int secondComma = line.indexOf(',', firstComma + 1);

 if (firstComma > 0 && secondComma > firstComma) {
   String runStr = line.substring(0, firstComma);
   String indexStr = line.substring(firstComma + 1, secondComma);
   String colorStr = line.substring(secondComma + 1);

   cmd.run = runStr.toInt();
   cmd.index = indexStr.toInt();
   long colorValue = strtol(colorStr.c_str(), NULL, 16);
   cmd.r = (colorValue >> 16) & 0xFF;
   cmd.g = (colorValue >> 8) & 0xFF;
   cmd.b = colorValue & 0xFF;
   cmd.valid = true;
 }
 return cmd;
}

void setup() {
 Serial.begin(115200);
 Serial1.begin(115200, SERIAL_8N1, 18, 19);
 delay(500);
 Serial.println("ESP32 UART ready (RX=18, TX=19)");

 FastLED.addLeds<WS2812B, LED_PIN_0, GRB>(leds_0, LED_COUNT);
 FastLED.addLeds<WS2812B, LED_PIN_1, GRB>(leds_1, LED_COUNT);
 FastLED.addLeds<WS2812B, LED_PIN_2, GRB>(leds_2, LED_COUNT);
 FastLED.addLeds<WS2812B, LED_PIN_3, GRB>(leds_3, LED_COUNT);
 FastLED.addLeds<WS2812B, LED_PIN_4, GRB>(leds_4, LED_COUNT);
 FastLED.addLeds<WS2812B, LED_PIN_5, GRB>(leds_5, LED_COUNT);
 FastLED.addLeds<WS2812B, LED_PIN_6, GRB>(leds_6, LED_COUNT);
 FastLED.addLeds<WS2812B, LED_PIN_7, GRB>(leds_7, LED_COUNT);
 FastLED.addLeds<WS2812B, LED_PIN_8, GRB>(leds_8, LED_COUNT);
 FastLED.addLeds<WS2812B, LED_PIN_9, GRB>(leds_9, LED_COUNT);
 FastLED.addLeds<WS2812B, LED_PIN_10, GRB>(leds_10, LED_COUNT);
 FastLED.addLeds<WS2812B, LED_PIN_11, GRB>(leds_11, LED_COUNT);
 FastLED.addLeds<WS2812B, LED_PIN_12, GRB>(leds_12, LED_COUNT);
 FastLED.addLeds<WS2812B, LED_PIN_13, GRB>(leds_13, LED_COUNT);
 FastLED.addLeds<WS2812B, LED_PIN_14, GRB>(leds_14, LED_COUNT);
 FastLED.addLeds<WS2812B, LED_PIN_15, GRB>(leds_15, LED_COUNT);
 FastLED.addLeds<WS2812B, LED_PIN_16, GRB>(leds_16, LED_COUNT);
 FastLED.addLeds<WS2812B, LED_PIN_17, GRB>(leds_17, LED_COUNT);
 FastLED.addLeds<WS2812B, LED_PIN_18, GRB>(leds_18, LED_COUNT);
 FastLED.addLeds<WS2812B, LED_PIN_19, GRB>(leds_19, LED_COUNT);
 FastLED.setBrightness(BRIGHTNESS);

 fill_solid(leds_0, LED_COUNT, CRGB::Black);
 fill_solid(leds_1, LED_COUNT, CRGB::Black);
 fill_solid(leds_2, LED_COUNT, CRGB::Black);
 fill_solid(leds_3, LED_COUNT, CRGB::Black);
 fill_solid(leds_4, LED_COUNT, CRGB::Black);
 fill_solid(leds_5, LED_COUNT, CRGB::Black);
 fill_solid(leds_6, LED_COUNT, CRGB::Black);
 fill_solid(leds_7, LED_COUNT, CRGB::Black);
 fill_solid(leds_8, LED_COUNT, CRGB::Black);
 fill_solid(leds_9, LED_COUNT, CRGB::Black);
 fill_solid(leds_10, LED_COUNT, CRGB::Black);
 fill_solid(leds_11, LED_COUNT, CRGB::Black);
 fill_solid(leds_12, LED_COUNT, CRGB::Black);
 fill_solid(leds_13, LED_COUNT, CRGB::Black);
 fill_solid(leds_14, LED_COUNT, CRGB::Black);
 fill_solid(leds_15, LED_COUNT, CRGB::Black);
 fill_solid(leds_16, LED_COUNT, CRGB::Black);
 fill_solid(leds_17, LED_COUNT, CRGB::Black);
 fill_solid(leds_18, LED_COUNT, CRGB::Black);
 fill_solid(leds_19, LED_COUNT, CRGB::Black);
 FastLED.show();
}

String inputLine = "";   // <-- must be global or static

void loop() {
   while (Serial1.available() > 0) {
       char c = Serial1.read();

       if (c == '\n') {
           inputLine.trim();

           ParsedCommand cmd = parseInputLine(inputLine);

           if (cmd.valid) {

               if (cmd.end) {
                   Serial.println("End message received");
                   FastLED.show();    // update all strips
               } else {

                   Serial.print("Run: ");
                   Serial.print(cmd.run);
                   Serial.print(", Index: ");
                   Serial.print(cmd.index);
                   Serial.print(", Color: ");
                   Serial.print(cmd.r);
                   Serial.print(",");
                   Serial.print(cmd.g);
                   Serial.print(",");
                   Serial.println(cmd.b);

                   if (cmd.index >= 0 && cmd.index < LED_COUNT) {

                       switch (cmd.run) {
                           case 0:  leds_0[cmd.index]  = CRGB(cmd.r, cmd.g, cmd.b); break;
                           case 1:  leds_1[cmd.index]  = CRGB(cmd.r, cmd.g, cmd.b); break;
                           case 2:  leds_2[cmd.index]  = CRGB(cmd.r, cmd.g, cmd.b); break;
                           case 3:  leds_3[cmd.index]  = CRGB(cmd.r, cmd.g, cmd.b); break;
                           case 4:  leds_4[cmd.index]  = CRGB(cmd.r, cmd.g, cmd.b); break;
                           case 5:  leds_5[cmd.index]  = CRGB(cmd.r, cmd.g, cmd.b); break;
                           case 6:  leds_6[cmd.index]  = CRGB(cmd.r, cmd.g, cmd.b); break;
                           case 7:  leds_7[cmd.index]  = CRGB(cmd.r, cmd.g, cmd.b); break;
                           case 8:  leds_8[cmd.index]  = CRGB(cmd.r, cmd.g, cmd.b); break;
                           case 9:  leds_9[cmd.index]  = CRGB(cmd.r, cmd.g, cmd.b); break;
                           case 10: leds_10[cmd.index] = CRGB(cmd.r, cmd.g, cmd.b); break;
                           case 11: leds_11[cmd.index] = CRGB(cmd.r, cmd.g, cmd.b); break;
                           case 12: leds_12[cmd.index] = CRGB(cmd.r, cmd.g, cmd.b); break;
                           case 13: leds_13[cmd.index] = CRGB(cmd.r, cmd.g, cmd.b); break;
                           case 14: leds_14[cmd.index] = CRGB(cmd.r, cmd.g, cmd.b); break;
                           case 15: leds_15[cmd.index] = CRGB(cmd.r, cmd.g, cmd.b); break;
                           case 16: leds_16[cmd.index] = CRGB(cmd.r, cmd.g, cmd.b); break;
                           case 17: leds_17[cmd.index] = CRGB(cmd.r, cmd.g, cmd.b); break;
                           case 18: leds_18[cmd.index] = CRGB(cmd.r, cmd.g, cmd.b); break;
                           case 19: leds_19[cmd.index] = CRGB(cmd.r, cmd.g, cmd.b); break;
                       }
                   }
               }
           } else {
               Serial.print("Invalid input: ");
               Serial.println(inputLine); 
           }

           inputLine = "";  // reset buffer
       }

       else {
           inputLine += c;  // accumulate characters
       }
   }
}

// #include <FastLED.h>

// // ---- CONFIG ----
// #define LED_PIN_0   23 // Run 0
// #define LED_PIN_1   2 // Run 0
// //#define LED_PIN_2   5
// //#define LED_PIN_3   15
// //#define LED_PIN_4   21
// //#define LED_PIN_5   15        
// //#define LED_PIN_6   22
// //#define LED_PIN_7   21        
// //#define LED_PIN_8   22
// //#define LED_PIN_9   15        // change this to your LED data pin
// //#define LED_PIN_10  23
// //#define LED_PIN_11  21        
// //#define LED_PIN_12  22
// //#define LED_PIN_13  15        // change this to your LED data pin
// //#define LED_PIN_14  24
// //#define LED_PIN_15  21        
// //#define LED_PIN_16  22
// //#define LED_PIN_17  25
// //#define LED_PIN_18  21        
// //#define LED_PIN_19  22

// #define LED_COUNT   30
// #define BRIGHTNESS  150

// CRGB leds_0[LED_COUNT];
// CRGB leds_1[LED_COUNT];
// //CRGB leds_2[LED_COUNT];
// //CRGB leds_3[LED_COUNT];
// //CRGB leds_4[LED_COUNT];
// //CRGB leds_5[LED_COUNT];
// //CRGB leds_6[LED_COUNT];
// //CRGB leds_7[LED_COUNT];
// //CRGB leds_8[LED_COUNT];
// //CRGB leds_9[LED_COUNT];
// //CRGB leds_10[LED_COUNT];
// //CRGB leds_11[LED_COUNT];
// //CRGB leds_12[LED_COUNT];
// //CRGB leds_13[LED_COUNT];
// //CRGB leds_14[LED_COUNT];
// //CRGB leds_15[LED_COUNT];
// //CRGB leds_16[LED_COUNT];
// //CRGB leds_17[LED_COUNT];
// //CRGB leds_18[LED_COUNT];
// //CRGB leds_19[LED_COUNT];

// void setup() {
//   Serial.begin(115200);
//   Serial1.begin(115200, SERIAL_8N1, 18, 19);
//   delay(500);
//   Serial.println("ESP32 UART ready (RX=18, TX=19)");

//   // ---- FASTLED INIT ----
//   FastLED.addLeds<WS2812B, LED_PIN_0, GRB>(leds_0, LED_COUNT);
//   FastLED.addLeds<WS2812B, LED_PIN_1, GRB>(leds_1, LED_COUNT);
// //  FastLED.addLeds<WS2812B, LED_PIN_2, GRB>(leds_2, LED_COUNT);
// //  FastLED.addLeds<WS2812B, LED_PIN_3, GRB>(leds_3, LED_COUNT);
// //  FastLED.addLeds<WS2812B, LED_PIN_4, GRB>(leds_4, LED_COUNT);
// //  FastLED.addLeds<WS2812B, LED_PIN_5, GRB>(leds_5, LED_COUNT);
// //  FastLED.addLeds<WS2812B, LED_PIN_6, GRB>(leds_6, LED_COUNT);
// //  FastLED.addLeds<WS2812B, LED_PIN_7, GRB>(leds_7, LED_COUNT);
// //  FastLED.addLeds<WS2812B, LED_PIN_8, GRB>(leds_8, LED_COUNT);
// //  FastLED.addLeds<WS2812B, LED_PIN_9, GRB>(leds_9, LED_COUNT);
// //  FastLED.addLeds<WS2812B, LED_PIN_10, GRB>(leds_10, LED_COUNT);
// //  FastLED.addLeds<WS2812B, LED_PIN_11, GRB>(leds_11, LED_COUNT);
// //  FastLED.addLeds<WS2812B, LED_PIN_12, GRB>(leds_12, LED_COUNT);
// //  FastLED.addLeds<WS2812B, LED_PIN_13, GRB>(leds_13, LED_COUNT);
// //  FastLED.addLeds<WS2812B, LED_PIN_14, GRB>(leds_14, LED_COUNT);
// //  FastLED.addLeds<WS2812B, LED_PIN_15, GRB>(leds_15, LED_COUNT);
// //  FastLED.addLeds<WS2812B, LED_PIN_16, GRB>(leds_16, LED_COUNT);
// //  FastLED.addLeds<WS2812B, LED_PIN_17, GRB>(leds_17, LED_COUNT);
// //  FastLED.addLeds<WS2812B, LED_PIN_18, GRB>(leds_18, LED_COUNT);
// //  FastLED.addLeds<WS2812B, LED_PIN_19, GRB>(leds_19, LED_COUNT);
//   FastLED.setBrightness(BRIGHTNESS);

//   // ---- TURN EVERYTHING ON ----
//   fill_solid(leds_0,   LED_COUNT, CRGB::White);   // set color here
// //  fill_solid(leds_2, LED_COUNT, CRGB::White);
// //  fill_solid(leds_3, LED_COUNT, CRGB::White);
// //  fill_solid(leds_4, LED_COUNT, CRGB::White);
//   FastLED.show();
// }

// void loop() {
//   // nothing — LEDs stay on
// }
