import serial
from time import sleep

# Open UART0 on Raspberry Pi (GPIO14 TX → ESP32 RX)
ser = serial.Serial("/dev/ttyAMA0", 115200)

print("Raspberry Pi UART Sender Ready")

while True:
    message = "HIHIHIHIHI\n"
    ser.write(message.encode())   # Send message with newline
    print("Sent:", message.strip())

    sleep(1)
