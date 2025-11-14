import serial
from time import sleep

ser = serial.Serial("/dev/tty/AMA10", 115200)

while True:
    recieved_data = ser.read()
    sleep(0.03)
    data_left = ser.inWaiting()
    received_data += ser.read(data_left)
    print(received_data)
    ser.write(received_data)