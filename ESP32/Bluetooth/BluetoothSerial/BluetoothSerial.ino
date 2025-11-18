#include <Arduino.h>

void setup() {
  Serial.begin(115200);    

  // Explicitly map UART pins:
  // RX = GPIO16, TX = GPIO17
  Serial1.begin(115200, SERIAL_8N1, 18, 19);

  Serial.println("ESP32 UART ready (RX=16, TX=17)");
}

void loop() {
  if (Serial1.available()) {
    int b = Serial1.read();
    Serial.print("Byte: ");
    Serial.println(b);
  }
}
