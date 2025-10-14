/*
  ESP32 CODE 

  - linked list for storing graph data for Subway lines
  - multi processing? (maybe not since this is an esp32)
  - read in data from client raspberry pi 
  - send data to LEDs through linked list structure, traverse through LEDs to pick which stops need to light up
*/

#include <Arduino.h>
#include "WS2812BStrip.h"

#include <Arduino.h>
#include "WS2812BStrip.h"

#define LED_PIN   5
#define LED_COUNT 60

using namespace WS2812B;

LED leds[LED_COUNT];
LEDStrip strip(leds, LED_COUNT);

class LEDList {
  private:
    LED* head;
    unsigned int size;

  public:
    LEDList(LED* leds, unsigned int count) {
      head = &leds[0];
      size = count;

      for (unsigned int i = 0; i < count-1; i++) {
        if (i == 0) {
          leds[i].prev = nullptr;
        }
        else {
          leds[i].prev = &leds[i-1];
        }
        if (i == count - 1) {
          leds[i].next = nullptr;          
        } else {
          leds[i].next = &leds[i + 1];    
        }
      }
    }

    LED* getHead() { return head; }
    unsigned int getSize() { return size; }

    void setAll(uint8_t r, uint8_t g, uint8_t b) {
      LED* current = head;
      while (current) {
        current->red   = r;
        current->green = g;
        current->blue  = b;
        current = current->next;
      }
    }

    void setOne(int index, uint8_t r, uint8_t g, uint8_t b) {
      if (index < 0 || index >= size) return;
      LED* current = head;
      for (int i = 0; i < index; i++) {
        current = current->next;
      }
      current->red = r;
      current->green = g;
      current->blue = b;
    }
};

// TODO: ROUTE POWER TO CORRECT DATALINE ON LED BOARD, FIGURE OUT THIS WITH VINCE AND ANDREW
void dataline_route(LEDList route) {

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