#include <Arduino.h>
#include <FastLED.h>
#include <map>

#define NUM_RUNS  20       // You said you will have ~20 LED runs
#define LEDS_PER_RUN 300   // Adjust as needed
#define BRIGHTNESS 5

// Map: stationID -> (run, index)
struct StationInfo {
  int run;
  int index;
};

std::map<String, StationInfo> stationMap;

// Create arrays for all LED runs
CRGB leds[NUM_RUNS][LEDS_PER_RUN];

// ----------------------------- SETUP -----------------------------
void setup() {
  Serial.begin(115200);
  FastLED.setBrightness(BRIGHTNESS);

  // ------------- Initialize all LED strips -------------
  // Assign each run to pins 2–21 (you can customize)
  int pins[NUM_RUNS] = {
    2,3,4,5,12,13,14,15,16,17,
    18,19,21,22,23,25,26,27,32,33
  };

  for (int r = 0; r < NUM_RUNS; r++) {
    FastLED.addLeds<WS2812B, -1 /*temp*/, GRB>(leds[r], LEDS_PER_RUN);
  }
  // Important: assign the correct data pins AFTER registration
  for (int r = 0; r < NUM_RUNS; r++) {
    FastLED[ r ].setPin(pins[r]);
  }

  // ------------------ Test JSON fragment -------------------
  String input = R"(
    },
        "255S": {
            "run": 0,
            "index": 2,
            "name": "Pennsylvania Av (3)"
        },
        "254N": {
            "run": 0,
            "index": 3,
            "name": "Junius St (3)"
        },
        "254S": {
            "run": 1,
            "index": 100,
            "name": "Junius St (3)"
        },
  )";

  int pos = 0;

  while (true) {
    int q1 = input.indexOf("\"", pos);
    if (q1 < 0) break;
    int q2 = input.indexOf("\"", q1 + 1);
    if (q2 < 0) break;

    String stationID = input.substring(q1 + 1, q2);
    pos = q2 + 1;

    int brace = input.indexOf("{", pos);
    if (brace < 0) break;
    if (brace - q2 > 6) continue;

    // run
    int runPos = input.indexOf("\"run\"", brace);
    if (runPos < 0) break;
    int colon1 = input.indexOf(":", runPos);
    int runValue = input.substring(colon1 + 1).toInt();

    // index
    int indexPos = input.indexOf("\"index\"", runPos);
    if (indexPos < 0) break;
    int colon2 = input.indexOf(":", indexPos);
    int indexValue = input.substring(colon2 + 1).toInt();

    StationInfo info{ runValue, indexValue };
    stationMap[stationID] = info;
  }

  // ------------------ Light LEDs based on map -------------------
  // Clear all strips first
  for (int r = 0; r < NUM_RUNS; r++) {
    fill_solid(leds[r], LEDS_PER_RUN, CRGB::Black);
  }

  // Light each station based on its run and index
  for (auto &entry : stationMap) {
    String station = entry.first;
    int run   = entry.second.run;
    int index = entry.second.index;

    Serial.print("Lighting station ");
    Serial.print(station);
    Serial.print(" at run ");
    Serial.print(run);
    Serial.print(" index ");
    Serial.println(index);

    if (run >= 0 && run < NUM_RUNS && index >= 0 && index < LEDS_PER_RUN) {
      leds[run][index] = CRGB::Red;   // choose a color (you can customize)
    }
  }

  FastLED.show();
}

void loop() {}
