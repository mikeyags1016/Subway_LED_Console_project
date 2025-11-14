#include <Arduino.h>

void setup() {
  Serial.begin(115200);      // For debugging over USB
  Serial1.begin(115200);     // UART to Raspberry Pi using TX1/RX1 pins

  Serial.println("ESP32 UART ready");
}

void loop() {
  // -------- RECEIVE FROM RASPBERRY PI --------
  if (Serial1.available()) {
    String msg = Serial1.readStringUntil('\n');  // read line ending in \n

    Serial.print("Received from Pi: ");
    Serial.println(msg);

    // -------- RESPOND BACK TO PI --------
    Serial1.println("ESP32 received: " + msg);
  }

  delay(10);
}
