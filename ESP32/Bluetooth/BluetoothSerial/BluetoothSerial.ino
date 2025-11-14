#include <Arduino.h>

void setup() {
  Serial.begin(115200);     // USB serial monitor
  Serial1.begin(115200);    // UART to Raspberry Pi (TX/RX)

  Serial.println("ESP32 Ready. Sending data to Raspberry Pi...");
}

void loop() {
  // Send a message to Raspberry Pi
  Serial1.println("Hello Pi!");

  // Check for data coming back from Raspberry Pi
  while (Serial1.available()) {
    uint8_t incoming = Serial1.read();
    Serial.print("Pi replied: ");
    Serial.write(incoming);
    Serial.println();
  }

  delay(1000);
}
