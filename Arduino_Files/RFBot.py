from Arduino_Files.communication import Serial_Device
import Arduino_Files.IK as IK

class RFBot:
    def __init__(self, port='COM3', baud='9600'):
        self.arduino = Serial_Device(port=port, baud=baud)
        self.isReady = True

    def stop(self):
        """Stop the robot."""
        self.arduino.send_data_byte(0)

    def zero(self):
        """Move the robot to the zero position."""
        self.arduino.send_data_f([0, 45, 45, 90])

    def grip(self):
        """Activate the gripper."""
        self.arduino.send_data_byte(1)

    def release(self):
        """Release the gripper."""
        self.arduino.send_data_byte(2)

    def move(self, pos):
        """
        Move the robot to a specified (x, y, z) position.
        """
        if len(pos) != 3:
            raise ValueError("Position must have 3 elements: (x, y, z)")

        x, y, z = pos

        # if not IK.check_reachability(x, y, z, 250, 250):
        #     print("Not reachable")
        #     return

        angles = IK.inverse_kinematics(x, y, z, 250, 250)

        # You could add extra validation here if needed for angles
        print(f"Moving to angles: {angles}")
        self.arduino.send_data_f(angles)
        # self.get_state()

    def get_state(self):
        """
        Read a byte of state data from the Arduino.
        """
        # print(self.arduino.read_data_byte())
        return self.arduino.read_data_byte()
    
    def robot_state():
        
        if  len(get_state) != 0:
            return True
        
        return False


# from communication import Serial_Device
# import IK

# arduino = Serial_Device(port='COM5', baud='9600')

# isReady = True

# def stop() :
#     arduino.send_data_byte(0)

# def zero() :
#     arduino.send_data_f([0,45,45, 90])

# def grip() :
#     arduino.send_data_byte(1)

# def release() :
#         arduino.send_data_byte(2)

# def move(pos) :
#     if len(pos) != 3:  # Ensure the array is of size 5
#         raise ValueError("Array must have 5 elements")
#     else :
#         x = pos[0]
#         y = pos[1]
#         z = pos[2]
            
#         if(IK.check_reachability(x,y,z, 250, 250)):
#             pass
#         else:
#             print("Not reachable")
#         values = IK.inverse_kinematics(x,y,z, 250, 250)

#         ### add if statement here to make sure only valid angles are sent

#         print(values)
#         arduino.send_data_f(values)

# def getState():
#     data = arduino.read_data_byte()
#     return data


