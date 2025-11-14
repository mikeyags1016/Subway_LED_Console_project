import serial
from time import sleep

ser = serial.Serial("/dev/ttyAMA0", 115200, timeout=1)

while True:
    # Send command to ESP32
    ser.write(b"PING\n")
    print("Sent: PING")

    # Wait for reply
    reply = ser.readline().decode().strip()
    if reply:
        print("ESP32 replied:", reply)
    else:
        print("No reply")

    sleep(1)
