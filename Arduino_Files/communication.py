import serial
import struct
import time

class Serial_Device:
    def __init__(self, port: str, baud: int):
        self.port = port
        self.baud = baud
        # Open serial connection (adjust COM port and baud rate as needed)
        self.ser = serial.Serial(port, baud, timeout=1)
        time.sleep(2)  # Wait for Arduino to reset


    def send_data_f(self, data_array: list[float]):
        start_byte = b'\xFF'
        # Pack the floats into bytes
        data = struct.pack('<' + 'f' * len(data_array), *data_array)  # Little-endian format

        # Send start byte + data
        self.ser.write(start_byte + data)

    def send_data_byte(self, byte):
        start_byte = b'\x7F'

        data = struct.pack('B', byte)
        # Send start byte + data
        self.ser.write(start_byte + data)

    def read_data_byte(self):
        print("checking serial")
        if self.ser.in_waiting >= 2:
            print("serial available")
            start_byte = self.ser.read(1)
            if start_byte == b'\xAA':  # Start byte detected
                data = self.ser.read(1)
                print("Data: ")
                print(data)
                return data
            else:
                print("Start byte not detected, flushing garbage...")
                self.ser.reset_input_buffer()
        return None  # Return None instead of False
            
        

