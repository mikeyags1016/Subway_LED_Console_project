#include <Arduino.h>

void setup() {
  Serial.begin(115200);       // USB Serial Monitor
  Serial1.begin(115200);      // UART from Raspberry Pi

  Serial.println("ESP32 UART Receiver Ready");
}

void loop() {

  // Check if Pi sent anything
  if (Serial1.available()) {
    String msg = Serial1.readStringUntil('\n');   // read until newline
    msg.trim();                                   // clean \r and spaces

    Serial.print("From Pi: ");
    Serial.println(msg);
  }

  delay(5);
}
