# ## EXAMPLE CODE FOR RUNNER ##
# from communication import Serial_Device
# import RFBot
# import time


# while(True):

#     position_str = input("Enter a command: ")
#     if (position_str == "stop") :
#         RFBot.stop()
#     elif (position_str  == "zero") :
#         RFBot.zero()
#     elif (position_str == "close"):
#         RFBot.grip()
#     elif (position_str == "open"):
#         RFBot.release()
#     else:
#         position = [float(num) for num in position_str.split()]
#         RFBot.move(position)

#     RFBot.arduino.ser.reset_input_buffer()  ## clears buffer, waits for robot to send serial data back to indicate readiness
#     while(RFBot.getState() == None) :
#         time.sleep(0.01)
    



## EXAMPLE CODE FOR RUNNER ##

from communication import Serial_Device
import RFBot
import time

RFBot.zero()

while(True):

    position_str = input("Enter a command: ")
    if (position_str == "stop") :
        RFBot.stop()
    elif (position_str  == "zero") :
        RFBot.zero()
    elif (position_str == "close"):
        RFBot.grip()
    elif (position_str == "open"):
        RFBot.release()
    else:
        position = [float(num) for num in position_str.split()]
        RFBot.move(position)

    RFBot.arduino.ser.reset_input_buffer()  ## clears buffer, waits for robot to send serial data back to indicate readiness
    while(RFBot.getState() == None) :
        time.sleep(0.01)
    

