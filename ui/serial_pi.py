import serial
import json

ser = serial.Serial('/dev/serial0', 115200, timeout=1)

while True:
    line = ser.readline().decode('utf-8').strip()

    if line:
        try:
            data = json.loads(line)
            print("Received:", data)
        except json.JSONDecodeError:
            print("Bad JSON:", line)
