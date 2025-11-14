#include <Arduino.h>
#include <ArduinoJson.h>

void setup() {
  Serial.begin(115200);   // USB serial for debugging
  Serial1.begin(115200);  // UART TX/RX pins
}

void loop() {
  StaticJsonDocument<200> doc;
  doc["temp"] = 22.5;
  doc["status"] = "OK";

  serializeJson(doc, Serial1);
  Serial1.println(); // newline makes parsing easier

  delay(1000);
}
