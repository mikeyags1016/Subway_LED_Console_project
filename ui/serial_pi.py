import serial

# Open UART on Raspberry Pi
ser = serial.Serial('/dev/serial0', 115200, timeout=1)

print("Listening on /dev/serial0...")

while True:
    line = ser.readline().decode('utf-8', errors='ignore').strip()
    
    if line:
        print("Received:", line)
