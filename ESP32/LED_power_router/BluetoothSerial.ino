#include "BluetoothSerial.h"

BluetoothSerial SerialBT;

void setup() {
  Serial.begin(115200);
  SerialBT.begin("ESP32_BT"); // name it whatever you want
  Serial.println("Bluetooth started! Pair with ESP32_BT");
}

// Get and print the Bluetooth MAC address
  const uint8_t* mac = esp_bt_dev_get_address();
  Serial.printf("Bluetooth device name: %s\n", "ESP32_BT");
  Serial.printf("Bluetooth MAC address: %02X:%02X:%02X:%02X:%02X:%02X\n",
                mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
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
