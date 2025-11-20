/*
  ESP32 CODE 

  - linked list for storing graph data for Subway lines
  - multi processing? (maybe not since this is an esp32)
  - read in data from client raspberry pi 
  - send data to LEDs through linked list structure, traverse through LEDs to pick which stops need to light up
*/

#include <Arduino.h>
#include "WS2812BStrip.h"
#include <string>

#define LED_PIN   5
#define LED_COUNT 60

using namespace WS2812B;

LED leds[LED_COUNT];
LEDStrip strip(leds, LED_COUNT);

class LEDList {
private:
    LED* head;
    LED* tail;
    string station_name;
    unsigned int size;

public:
    LEDList() : head(nullptr), tail(nullptr), size(0), string("") {}

    LEDList(LED* leds, unsigned int count) {
        initialize(leds, count);
    }

    void initialize(LED* leds, unsigned int count) {
        head = &leds[0];
        size = count;

        for (unsigned int i = 0; i < count; i++) {
            leds[i].prev = (i == 0) ? nullptr : &leds[i - 1];
            leds[i].next = (i == count - 1) ? nullptr : &leds[i + 1];
        }

        tail = &leds[count - 1];
    }

    LED* getHead() { return head; }
    unsigned int getSize() { return size; }

    void setAll(uint8_t r, uint8_t g, uint8_t b) {
        LED* current = head;
        while (current) {
            current->red = r;
            current->green = g;
            current->blue = b;
            current = current->next;
        }
    }

    void setOne(int index, uint8_t r, uint8_t g, uint8_t b) {
        if (index < 0 || index >= size) return;
        LED* current = head;
        for (int i = 0; i < index; i++)
            current = current->next;

        current->red = r;
        current->green = g;
        current->blue = b;
    }
};

class LEDMap {
public:
    static const int NUM_ROUTES = 9;
    static const int ROUTE_LENGTH = 60;

    LED leds[NUM_ROUTES * ROUTE_LENGTH];  
    LEDList routes[NUM_ROUTES];

    LEDMap();
};

// Linked list structure with branch and station IDs for each run 
// One larger dictionary with each run (for starting purposes)

LEDMap::LEDMap() {
    // 1 Train
    routes[0].initialize(&leds[0], 38);  // 38 stations
    std::string line1_names[] = {
        "Van Cortlandt Park–242 St", "238 St", "231 St", "Marble Hill–225 St", "215 St",
        "207 St", "Dyckman St", "191 St", "181 St", "168 St–Washington Hts", "157 St",
        "145 St", "137 St–City College", "125 St", "116 St–Columbia University",
        "Cathedral Pkwy–110 St", "103 St", "96 St", "86 St", "79 St", "72 St",
        "66 St–Lincoln Center", "59 St–Columbus Circle", "50 St", "Times Sq–42 St",
        "34 St–Penn Station", "28 St", "23 St", "18 St", "14 St", "Christopher St–Sheridan Sq",
        "Houston St", "Canal St", "Franklin St", "Chambers St", "Cortlandt St",
        "Rector St", "South Ferry"
    };

    for (int i = 0; i < 38; i++) {
        leds[i].station_name = line1_names[i];
    }

    // 2 Train
    routes[1].initialize(&leds[60], 48);  // next block of LEDs
    std::string line2_names[] = {
        "Wakefield–241 St", "Nereid Ave–238 St", "233 St", "225 St", "219 St",
        "Gun Hill Rd", "Burke Ave", "Allerton Ave", "Pelham Pkwy", "Bronx Park East",
        "E 180 St", "West Farms Sq–E Tremont Ave", "174–175 Sts", "Freeman St",
        "Simpson St", "Intervale Ave", "Prospect Ave", "Jackson Ave", "3 Ave–149 St",
        "149 St–Grand Concourse", "135 St", "125 St", "116 St", "Central Park North–110 St",
        "96 St", "Times Sq–42 St", "34 St–Penn Station", "14 St", "Chambers St",
        "Park Place", "Fulton St", "Wall St", "Clark St", "Borough Hall", "Hoyt St",
        "Nevins St", "Atlantic Av–Barclays Ctr", "Bergen St", "Grand Army Plaza",
        "Eastern Pkwy–Bklyn Museum", "Franklin Ave", "President St", "Sterling St",
        "Winthrop St", "Church Ave", "Beverly Rd", "Newkirk Ave–Little Haiti",
        "Flatbush Ave–Brooklyn College"
    };

    for (int i = 0; i < 48; i++) {
        leds[60 + i].station_name = line2_names[i];
    }
}

// TODO: ROUTE POWER TO CORRECT DATALINE ON LED BOARD, FIGURE OUT THIS WITH VINCE AND ANDREW
void dataline_route(string route, int starting_index) {
  // Path given from API: A1 -> A2 -> (branch) B1 -> B2 -> B3
  // Ask vince to send the line for the starting node as well
  

  // Check if you need to go up or down the line


  // Figure out how the output is going to look like 
  
}

LEDList ledList(leds, LED_COUNT);

void setup() {
  Serial.begin(115200);   // Debug console over USB
  Serial2.begin(9600, SERIAL_8N1, 16, 17); // UART2 on GPIO16=RX, GPIO17=TX

  initLEDStrip(leds, LED_COUNT);
  strip.start = ledList.getHead();
  ledList.setAll(0,0,0);
  strip.write(LED_PIN);

  Serial.println("ESP32 LED controller ready (UART mode).");
}

void loop() {
  static String input = "";

  // ADD: STORE DIFFERENT LINKED LISTS FOR DIFFERENT ROUTES ON LED BOARD, WILL GET VERY INVOLvED

  while (Serial2.available()) {
    char c = Serial2.read();
    if (c == '\n') {
      input.trim();
      Serial.print("Received: ");
      Serial.println(input);

      int idx, r, g, b;
      if (sscanf(input.c_str(), "%d,%d,%d,%d", &idx, &r, &g, &b) == 4) {
        // Individual LED
        ledList.setOne(idx, r, g, b);
      } else if (sscanf(input.c_str(), "%d,%d,%d", &r, &g, &b) == 3) {
        // Whole strip
        ledList.setAll(r, g, b);
      }


      // CHANGE: READ IN DATA INTO LINKED LIST STRUCTURE, RUN POWER ROUTING FUNCTION


      strip.write(LED_PIN);
      input = ""; // reset buffer
    } 
    else {
      input += c;
    }
  }
}