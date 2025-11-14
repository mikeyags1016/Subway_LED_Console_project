#include <Arduino.h>

void setup() {
  Serial.begin(115200);   // USB serial for debugging
  Serial1.begin(115200);  // UART TX/RX pins
}

void loop() {
  // Send a simple message instead of JSON
  Serial1.println("Hello from ESP32!");

  // Also print to USB Serial so you can see it
  Serial.println("Sent: Hello from ESP32!");

  delay(1000);
}
