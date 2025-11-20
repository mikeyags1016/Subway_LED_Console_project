#include <Arduino.h>

String jsonPath;

void setup() {
  Serial.begin(115200);    

  // Explicitly map UART pins:
  // RX = GPIO16, TX = GPIO17
  Serial1.begin(115200, SERIAL_8N1, 18, 19);
  delay(500);
  Serial.println("ESP32 UART ready (RX=16, TX=17)");
}

void loop() {
  if (Serial1.available()) {
    jsonPath = Serial1.readStringUntil('\n');
    
    Serial.print("Format: ");
    Serial.println(jsonPath);
  }
}
