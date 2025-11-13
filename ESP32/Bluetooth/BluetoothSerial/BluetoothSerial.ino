#include "BluetoothSerial.h"
#include "esp_bt_device.h"   // ✅ Required for esp_bt_dev_get_address()

BluetoothSerial SerialBT;

void setup() {
  Serial.begin(115200);
  SerialBT.begin("ESP32_BT"); // Set your device name
  Serial.println("Bluetooth started! Pair with ESP32_BT");

  // ✅ Get and print MAC address
  const uint8_t* mac = esp_bt_dev_get_address();
  Serial.printf("Bluetooth MAC address: %02X:%02X:%02X:%02X:%02X:%02X\n",
                mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
}

void loop() {
  if (Serial.available()) {
    SerialBT.write(Serial.read()); // USB → Bluetooth
  }

  if (SerialBT.available()) {
    Serial.write(SerialBT.read()); // Bluetooth → USB
  }

  delay(20);
}
