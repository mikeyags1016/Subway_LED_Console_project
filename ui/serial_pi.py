import serial
from time import sleep

ser = serial.Serial("/dev/ttyAMA10", 115200)

while True:
    ser.write(b'HIHIHIHIHI\r\n')
    print("Sent")
    sleep(1)