#include "BluetoothSerial.h"

BluetoothSerial SerialBT;

void setup() {
  Serial.begin(115200);
  SerialBT.begin("ESP32_BT"); // name it whatever you want
  Serial.println("Bluetooth started! Pair with ESP32_BT");
}

void loop() {
  if (Serial.available()) {
    SerialBT.write(Serial.read()); // forward from USB to Bluetooth
  }

  if (SerialBT.available()) {
    char incoming = SerialBT.read();
    Serial.write(incoming);
  }

  delay(20);
}
