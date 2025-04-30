import math
import numpy as np

#################################################################### Function to interpolate between points

def interpolate_coordinates(goal_x_coords, goal_y_coords, goal_z_coords, steps=5, skip_indices=[]):
   
    interpolated_x, interpolated_y, interpolated_z = [], [], []

    for i in range(len(goal_x_coords) - 1):
    
        # Skip interpolation for relocation steps
        if i in skip_indices or (i + 1) in skip_indices:
            continue
        
        x_start, x_end = goal_x_coords[i], goal_x_coords[i + 1]
        y_start, y_end = goal_y_coords[i], goal_y_coords[i + 1]
        z_start, z_end = goal_z_coords[i], goal_z_coords[i + 1]
        
        # Generate interpolated points between start and end
        x_points = np.linspace(x_start, x_end, steps)
        y_points = np.linspace(y_start, y_end, steps)
        z_points = np.linspace(z_start, z_end, steps)

        interpolated_x.extend(x_points)
        interpolated_y.extend(y_points)
        interpolated_z.extend(z_points)

    # Add the final points (the last coordinate), skipping if it's in skip_indices
    if len(goal_x_coords) - 1 not in skip_indices:
        interpolated_x.append(goal_x_coords[-1])
        interpolated_y.append(goal_y_coords[-1])
        interpolated_z.append(goal_z_coords[-1])

    # return interpolated_x, interpolated_y, interpolated_z

#################################################################### check reachability function

def check_reachability(goal_x, goal_y, goal_z, L1 = 250, L2 = 250):

    # Distance from joint 2 to end effector
    r = math.sqrt(goal_x**2 + goal_y**2 + goal_z**2) 
    
    # Check if the desired position is reachable
    if r > (L1 + L2) or r < abs(L1 - L2):
        raise ValueError("Target position is unreachable.")
    

#################################################################### move arm funciton

def move_arm(joint_1_angle, joint_2_angle):
    # Desired Joint Angles (radians)
    joint_angles = [
        joint_1_angle, # Joint 1 (calcualated angle)
        joint_2_angle, # Joint 2 (calculated angle)
    ]
    
# move arm here

          
#################################################################### IK Function

def inverse_kinematics(goal_x, goal_y, goal_z, L1=250,L2=250):
    EF_offset = 0

    r = math.sqrt(math.sqrt(goal_x**2 + goal_y**2)**2 + (goal_z + EF_offset)**2)  # Distance from joint 2 to end effector

    D_rad = math.atan2((goal_z + EF_offset), (math.sqrt(goal_x**2 + goal_y**2)))    # Angle from horizontal to r
    D_deg = (D_rad * 180) / math.pi

    C_rad = math.acos((L2**2 - r**2 - L1**2) / (-2 * r * L1))
    A_rad = math.acos((r**2 - L1**2 - L2**2) / (-2 * L1 * L2))

    C_deg = (C_rad * 180) / math.pi
    A_deg = (A_rad * 180) / math.pi


    # print(f"A_deg: {A_deg}, A_rad: {A_rad}")
    # print(f"C_deg: {C_deg}, C_rad: {C_rad}")
    # print(f"D_deg: {D_deg}, D_rad: {D_rad}")
    # print(f"r: {r}")

    theta_deg = 180 - D_deg - C_deg
    theta_rad = math.pi/2 - D_rad - C_rad  # angle for joint 2

    phi_deg = A_deg #180 - A_deg
    phi_rad = (phi_deg * math.pi) / 180 # angle for joint 4

    gamma_rad = math.atan(goal_y/goal_x)
    gamma_deg = (gamma_rad * 180) / math.pi # angle for base 

    base_angle = gamma_deg
    joint_1_angle = theta_deg
    joint_2_angle = phi_deg
    joint_3_angle = 90 - joint_2_angle + joint_1_angle
    
    # Angles sent to stepper motors
    joint_1_stepper_angle = theta_deg - 45  # Homing offsets
    joint_2_stepper_angle = 155 - phi_deg   # Homing offsets

    # print(f"theta_deg: {theta_deg}")
    # print(f"theta_rad: {theta_rad}")
    # print(f"phi_rad: {phi_rad}")
    # print(f"phi_deg: {phi_deg}")
    
    # print(f"joint_1_angle: {joint_1_angle}")
    # print(f"joint_2_angle: {joint_2_angle}")
    # print(f"joint_1_stepper_angle: {joint_1_stepper_angle}")
    # print(f"joint_2_stepper_angle: {joint_2_stepper_angle}")

    return [base_angle, joint_1_angle, joint_2_angle, joint_3_angle]

####################################################################

#MAIN
def main():

    # Arm lengths
    L1 = 250  # Link 1 Length: 250mm
    L2 = 250 # Link 2 Length: 250mm

    # Desired end points to interpolate between
    goal_x_coords = [300]
    goal_y_coords = [-300]
    goal_z_coords = [100]

    ####################################################################

    # Interpolate 5 points between each end point, and skip relocation steps
    #goal_x_coords, goal_y_coords, goal_z_coords = interpolate_coordinates(goal_x_coords, goal_y_coords, goal_z_coords, steps=5) #, skip_indices=[9])    

    # Iterates through all desired positions
    for i in range(len(goal_x_coords)):
        x = goal_x_coords[i]
        y = goal_y_coords[i]
        z = goal_z_coords[i] # add z offset here
        
        # Check reachability using function
        check_reachability(x, y, z, L1, L2)
        
        # Calculate angles for desired coordinate position using IK function
        angles = inverse_kinematics(x, y, z, L1,L2)
        print(angles)
        

        # Move arm to desired position using move arm function
        # move_arm(joint_1_stepper_angle, joint_2_stepper_angle)    
            
    ##########################################################################################################

if __name__ == "__main__":
    main()
