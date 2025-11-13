/*
  ESP32 CODE (FastLED version)

  - Linked list for storing subway line data
  - Reads data from Raspberry Pi via UART (Serial2)
  - Lights up corresponding LEDs for stations
  - Uses FastLED for WS2812B LED control
*/

#include <Arduino.h>
#include <FastLED.h>
#include <string>

#define LED_PIN    5
#define LED_COUNT  100
#define BRIGHTNESS 50

CRGB leds[LED_COUNT];

// ============================================================================
// LED Node + Linked List
// ============================================================================

//struct LEDNode {
//  int index;
//  CRGB color;            // Holds RGB color for FastLED
//  String station_name;
//  LEDNode* next;
//  LEDNode* prev;
//};
//
//class LEDList {
//private:
//  LEDNode* head;
//  LEDNode* tail;
//  unsigned int size;
//
//public:
//  LEDList() : head(nullptr), tail(nullptr), size(0) {}
//
//  void initialize(LEDNode* nodes, unsigned int count) {
//    head = &nodes[0];
//    size = count;
//
//    for (unsigned int i = 0; i < count; i++) {
//      nodes[i].index = i;
//      nodes[i].color = CRGB::Black;
//      nodes[i].next = (i < count - 1) ? &nodes[i + 1] : nullptr;
//      nodes[i].prev = (i > 0) ? &nodes[i - 1] : nullptr;
//    }
//
//    tail = &nodes[count - 1];
//  }
//
//  LEDNode* getHead() { return head; }
//  unsigned int getSize() { return size; }
//
//  // Set all LEDs in this route to a given color
//  void setAll(const CRGB& color) {
//    LEDNode* current = head;
//    while (current) {
//      current->color = color;
//      leds[current->index] = color;
//      current = current->next;
//    }
//    FastLED.show();
//  }
//
//  // Set a specific LED (by index in list)
//  void setOne(int index, const CRGB& color) {
//    if (index < 0 || index >= size) return;
//    LEDNode* current = head;
//    for (int i = 0; i < index; i++)
//      current = current->next;
//
//    current->color = color;
//    leds[current->index] = color;
//    FastLED.show();
//  }
//};

// ============================================================================
// LED Map (contains all routes)
// ============================================================================

class LEDMap {
public:
  static const int NUM_ROUTES = 9;
  static const int ROUTE_LENGTH = 60;

  LEDNode leds[NUM_ROUTES * ROUTE_LENGTH];
  LEDList routes[NUM_ROUTES];

  void process_route();

  LEDMap();
};

LEDMap::LEDMap() {
//  // --- 1 + 3 Train Combined ---
//  const int LINE1_3_COUNT = 59;
//  routes[0].initialize(&leds[0], LINE1_3_COUNT);
//
//  String line1_3_names[] = {
//    // Line 1 (Bronx → Manhattan → Chambers St)
//    "Van Cortlandt Park–242 St", "238 St", "231 St", "Marble Hill–225 St", "215 St",
//    "207 St", "Dyckman St", "191 St", "181 St", "168 St–Washington Hts", "157 St",
//    "145 St", "137 St–City College", "125 St", "116 St–Columbia University",
//    "Cathedral Pkwy–110 St", "103 St", "96 St", "86 St", "79 St", "72 St",
//    "66 St–Lincoln Center", "59 St–Columbus Circle", "50 St", "Times Sq–42 St",
//    "34 St–Penn Station", "28 St", "23 St", "18 St", "14 St", "Christopher St–Sheridan Sq",
//    "Houston St", "Canal St", "Franklin St", "Chambers St",
//
//    // Continue on Line 3 (Brooklyn-bound after Chambers St)
//    "Park Pl", "Fulton St", "Wall St", "Clark St", "Borough Hall",
//    "Hoyt St", "Nevins St", "Atlantic Av–Barclays Ctr", "Bergen St", "Grand Army Plaza",
//    "Eastern Pkwy–Bklyn Museum", "Franklin Av–Medgar Evers College", "Nostrand Av",
//    "Kingston Av", "Crown Hts–Utica Av", "Sutter Av–Rutland Rd", "Saratoga Av",
//    "Rockaway Av", "Junius St", "Pennsylvania Av", "Van Siclen Av", "New Lots Av"
//  };
//
//  for (int i = 0; i < LINE1_3_COUNT; i++) {
//    leds[i].station_name = line1_3_names[i];
//  }
//
//  // --- B Train (+ first stop from D) ---
//  const int LINEB_COUNT = 39;
//  routes[1].initialize(&leds[LINE1_3_COUNT], LINEB_COUNT);
//
//  String lineB_names[] = {
//    // First stop from Line D
//    "Norwood–205 St",
//
//    // Full Line B (Bronx → Manhattan → Brooklyn)
//    "Bedford Park Blvd", "Kingsbridge Rd", "Fordham Rd", "Tremont Ave",
//    "174–175 Sts", "170 St", "167 St", "161 St–Yankee Stadium",
//    "155 St", "145 St", "135 St", "125 St", "116 St", "Cathedral Pkwy–110 St",
//    "103 St", "96 St", "86 St", "81 St–Museum of Natural History",
//    "72 St", "59 St–Columbus Circle", "7 Av", "47–50 Sts–Rockefeller Ctr",
//    "42 St–Bryant Park", "34 St–Herald Sq", "W 4 St–Washington Sq",
//    "Broadway–Lafayette St", "Grand St", "DeKalb Ave", "Atlantic Av–Barclays Ctr",
//    "Prospect Park", "Parkside Ave", "Church Ave", "Beverley Rd", "Cortelyou Rd",
//    "Newkirk Plaza", "Avenue H", "Avenue J", "Avenue M", "Kings Hwy",
//    "Avenue U", "Sheepshead Bay", "Brighton Beach"
//  };
//
//  for (int i = 0; i < LINEB_COUNT; i++) {
//    leds[LINE1_3_COUNT + i].station_name = lineB_names[i];
//  }
//
//  // --- 5 Train (Eastchester–Dyre Av branch → Manhattan → Flatbush Av–Brooklyn College) ---
//  const int LINE5_COUNT = 36;
//  routes[2].initialize(&leds[LINE1_3_COUNT + LINEB_COUNT], LINE5_COUNT);
//  
//  String line5_names[] = {
//    // Bronx: Eastchester Dyre Avenue branch (local)
//    "Eastchester-Dyre Av",
//    "Baychester Av",
//    "Gun Hill Rd",
//    "Pelham Pkwy",
//    "Morris Park",
//    "E 180 St",
//    "West Farms Sq-E Tremont Av",
//    "174 St",
//    "Freeman St",
//    "Simpson St",
//    "Intervale Av",
//    "Prospect Av",
//    "Jackson Av",
//    "3 Av-149 St",
//    "149 St-Grand Concourse",
//    "138 St-Grand Concourse",
//  
//    // Manhattan (Lexington Ave express/local stops used by 5)
//    "125 St",
//    "86 St",
//    "59 St",
//    "Grand Central-42 St",
//    "14 St-Union Sq",
//    "Brooklyn Bridge-City Hall",
//    "Fulton St",
//    "Wall St",
//    "Bowling Green",
//  
//    // Brooklyn (most weekday trains continue to Flatbush Av-Brooklyn College)
//    "Borough Hall",
//    "Nevins St",
//    "Atlantic Av-Barclays Ctr",
//    "Franklin Av-Medgar Evers College",
//    "President St-Medgar Evers College",
//    "Sterling St",
//    "Winthrop St",
//    "Church Av",
//    "Beverly Rd",
//    "Newkirk Av-Little Haiti",
//    "Flatbush Av-Brooklyn College"
//  };
//  
//  for (int i = 0; i < LINE5_COUNT; i++) {
//    leds[LINE1_3_COUNT + LINEB_COUNT + i].station_name = line5_names[i];
//  }
//  
//  // --- A + C Trains combined (Inwood–207 St → Far Rockaway–Mott Ave) ---
//  const int LINEAC_COUNT = 49;
//  routes[3].initialize(&leds[LINE1_3_COUNT + LINEB_COUNT + LINE5_COUNT], LINEAC_COUNT);
//  
//  String lineAC_names[] = {
//    // Manhattan
//    "Inwood–207 St",
//    "Dyckman St",
//    "190 St",
//    "181 St",
//    "175 St",
//    "168 St",
//    "163 St–Amsterdam Av",
//    "155 St",
//    "145 St",
//    "125 St",
//    "59 St–Columbus Circle",
//    "42 St–Port Authority Bus Terminal",
//    "34 St–Penn Station",
//    "14 St",
//    "W 4 St–Washington Sq",
//    "Canal St",
//    "Chambers St",
//    "Fulton St",
//  
//    // Brooklyn
//    "High St",
//    "Jay St–MetroTech",
//    "Hoyt–Schermerhorn Sts",
//    "Lafayette Av",
//    "Clinton–Washington Avs",
//    "Franklin Av",
//    "Nostrand Av",
//    "Kingston–Throop Avs",
//    "Utica Av",
//    "Ralph Av",
//    "Rockaway Av",
//    "Broadway Junction",
//    "Liberty Av",
//    "Van Siclen Av",
//    "Shepherd Av",
//    "Euclid Av",
//    "Grant Av",
//  
//    // Queens + Rockaways (A line extension)
//    "80 St",
//    "88 St",
//    "Rockaway Blvd",
//    "104 St",
//    "111 St",
//    "Ozone Park–Lefferts Blvd",
//    "Aqueduct Racetrack",
//    "Aqueduct–North Conduit Av",
//    "Howard Beach–JFK Airport",
//    "Broad Channel",
//    "Beach 67 St",
//    "Beach 60 St",
//    "Beach 44 St",
//    "Beach 36 St",
//    "Beach 25 St",
//    "Far Rockaway–Mott Av"
//  };
//  
//  for (int i = 0; i < LINEAC_COUNT; i++) {
//    leds[LINE1_3_COUNT + LINEB_COUNT + LINE5_COUNT + i].station_name = lineAC_names[i];
//  }
}

// ============================================================================
// Main Program
// ============================================================================

void setup() {
  Serial.begin(115200);
  Serial2.begin(9600, SERIAL_8N1, 16, 17); // UART2 on GPIO16=RX, GPIO17=TX

  LEDMap subwayMap; 

  FastLED.addLeds<WS2812B, LED_PIN, GRB>(leds, LED_COUNT);
  FastLED.setBrightness(BRIGHTNESS);

  Serial.println("ESP32 LED controller ready (UART mode, FastLED).");

  // Example: Turn on all LEDs for route 1 in blue
  subwayMap.routes[0].setAll(CRGB::Blue);
  delay(1000);
  subwayMap.routes[0].setAll(CRGB::Black);
}

void loop() {
  // Example animation: walk a red dot through all LEDs
  for (int i = 0; i < LED_COUNT; i++) {
    leds[i] = CRGB::Red;
    FastLED.show();
    delay(50);
    leds[i] = CRGB::Black;
  }
}
