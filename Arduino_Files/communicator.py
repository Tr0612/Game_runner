import serial
import struct
import time

class Serial_Device:
    def __init__(self, port: str, baud: int):
        self.port = port
        self.baud = baud
        # Open serial connection (adjust COM port and baud rate as needed)
        self.ser = serial.Serial(port, baud)
        time.sleep(2)  # Wait for Arduino to reset


    def send_data_f(self, data_array: list[float]):
        self.start_byte = b'\xFF'
        # Pack the floats into bytes
        self.data = struct.pack('<' + 'f' * len(data_array), *data_array)  # Little-endian format

        # Send start byte + data
        self.ser.write(self.start_byte + self.data)
        
        
        
        
# arduino = Serial_Device(port='COM3', baud='9600')

# while(True):
#     values_str = input("Enter an array of angle values: ")
#     values = [float(num) for num in values_str.split()]
#     arduino.send_data_f(values)

