#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Dec  2 12:16:52 2024

@author: clairehamilton
"""

import threading
from Phidget22.Phidget import *
from Phidget22.Devices.Stepper import *
from Phidget22.Devices.VoltageInput import *
import time

# Constants
FSR_THRESHOLD = 1000  # Voltage threshold in mV for stage transition
REV_STEPS_WITH_RESCALE = 20000 * 16  # Steps per revolution * rescale factor

# Global state variables
initiate_flag = False
stop_flag = False  
quit_flag = False
next_stage_flag = False
return_flag = False

stage_1 = False
stage_2 = False
stage_3 = False
stage_4 = False
stage_5 = False

def input_listener():
    """Thread function to listen for user input."""
    global stop_flag, quit_flag, return_flag, next_stage_flag
    while True:
        key = input().strip().lower()
        if key == "s":
            print("Stopping motors. Press 'r' to resume, or 'i' to reset to original position.")
            stop_flag = True
        elif key == "q":
            print("Exiting program ...")
            quit_flag = True
        elif key == "n":
            print("User initiated next stage.")
            next_stage_flag = True

def setup_devices():
    """Starting communication with sensors and motors."""
    global stage_1
    print("Setting up devices...")
    
    # Set up FSR
    fsr = VoltageInput()
    fsr.setHubPort(5)
    fsr.setDeviceSerialNumber(740507)
    fsr.setChannel(0)
    fsr.setIsHubPortDevice(True)
    fsr.openWaitForAttachment(5000)
    print("FSR attached successfully.")

    # Set up Stepper 1
    stepper1 = Stepper()
    stepper1.setHubPort(4)
    stepper1.setDeviceSerialNumber(740507)
    stepper1.openWaitForAttachment(5000)
    stepper1.setEngaged(True)
    stepper1.setVelocityLimit(30000)
    print("Stepper1 engaged.")

    # Set up Stepper 2
    stepper2 = Stepper()
    stepper2.setHubPort(3)
    stepper2.setDeviceSerialNumber(740507)
    stepper2.openWaitForAttachment(5000)
    stepper2.setEngaged(True)
    stepper2.setVelocityLimit(30000)
    print("Stepper2 engaged.")
    
    # Set up Stepper 3
    stepper3 = Stepper()
    stepper3.setHubPort(1)
    stepper3.setDeviceSerialNumber(740507)
    stepper3.openWaitForAttachment(5000)
    stepper3.setEngaged(True)
    stepper3.setVelocityLimit(30000)
    print("Stepper3 engaged.")
    
    # Set up Stepper 4
    stepper4 = Stepper()
    stepper4.setHubPort(0)
    stepper4.setDeviceSerialNumber(740507)
    stepper4.openWaitForAttachment(5000)
    stepper4.setEngaged(True)
    stepper4.setVelocityLimit(30000)
    print("Stepper4 engaged.")


    print("Setup complete. Press Enter to begin lowering platform.")
    key = input().strip().lower()
    if key == "":
        stage_1 = True
        return fsr, stepper1, stepper2, stepper3, stepper4
    else:
        print("Invalid key.")

def monitor_fsr(fsr, stepper):
    """
    Stage 1: Using FSR to control motion of the platform.
    :param fsr: Used to access functions for force sensing resistor.
    :param stepper: Used to access functions for one motor.
    """
    global stop_flag, quit_flag, return_flag, stage_2
    print("Platform lowering.")
    stepper.setTargetPosition(REV_STEPS_WITH_RESCALE*20)
    while not quit_flag:
        voltage = fsr.getVoltage() * 1000  # Convert to mV
        if stop_flag:
            position_after_stop = stepper.getPosition()
            print(f"Stepper at port {stepper.getHubPort()} stopped by user.")
            stepper.setTargetPosition(stepper.getPosition())
            key = input().strip().lower()
            if key == 'r':
                print("Resuming motors...")
                stop_flag = False
                stepper.setTargetPosition(REV_STEPS_WITH_RESCALE-position_after_stop)
                continue
            elif key == 'i':
                return_flag = True
                stop_flag = False
                return
            elif key == 'q':
                quit_flag = True
                print("Exiting program...")
                return
            else:
                print('Invalid input')
                
        if voltage > FSR_THRESHOLD:
            print("Jar Detected. Platform motion stopped, moving onto motion of scroll plate.")
            stepper.setTargetPosition(stepper.getPosition())  # Stop Stepper1
            stage_1 = False
            stage_2 = True
            return
        
        time.sleep(0.5)

def operate_stepper_single(stepper, target_position):
    """
    Operate a stepper motor and wait for completion.
    :param stepper: Used to access functions for one motor.
    :param target_position: Target position for stepper motor.
    """
    global stop_flag, quit_flag, next_stage_flag
    
    print(f"Operating Stepper at port {stepper.getHubPort()}...")
    original_target_position = stepper.getPosition()+target_position
    stepper.setTargetPosition(original_target_position)

    while stepper.getIsMoving():
        if quit_flag:
            return
        if next_stage_flag:
            stepper.setTargetPosition(stepper.getPosition())
            next_stage_flag = False
            return
        if stop_flag:
            position_after_stop = stepper.getPosition()
            print(f"Stepper at port {stepper.getHubPort()} stopped by user.")
            print("Press 'r' to resume motors or 'i' to reset to original position.")
            stepper.setTargetPosition(stepper.getPosition())
            key = input().strip().lower()
            if key == 'r':
                print("Resuming motors...")
                stop_flag = False
                stepper.setTargetPosition(target_position-position_after_stop)
                continue
            elif key == 'q':
                print("Exiting program...")
                return
            elif key == 'i':
                return_flag = True
                stop_flag = False
                return
            else:
                print("Invalid key! Press 'r' to resume or 'i' to reset to original position.")
                    
        time.sleep(0.1)

    print(f"Stepper at port {stepper.getHubPort()} motion complete.")


def operate_stepper_multiple(stepper_list, target_positions):
    """
    Operate multiple stepper motors and wait for completion.
    :param stepper_list: List of stepper motor objects.
    :param target_positions: List of target positions for the steppers.
    """
    global stop_flag, quit_flag, return_flag, next_stage_flag

    if len(stepper_list) != len(target_positions):
        print("Error: Number of steppers and target positions must match.")
        return

    # Set target positions for all steppers
    for i, stepper in enumerate(stepper_list):
        print(f"Operating Stepper at port {stepper.getHubPort()}...")
        original_target_position = stepper.getPosition() + target_positions[i]
        stepper.setTargetPosition(original_target_position)

    while any(stepper.getIsMoving() for stepper in stepper_list):
        if next_stage_flag:
            stepper.setTargetPosition(stepper.getPosition())
            next_stage_flag = False
            return
        if quit_flag:
            return
        if stop_flag:
            for stepper in stepper_list:
                position_after_stop = stepper.getPosition()
                print(f"Stepper at port {stepper.getHubPort()} stopped by user.")
                stepper.setTargetPosition(position_after_stop)

            key = input().strip().lower()
            if key == 'r':
                print("Resuming motors...")
                stop_flag = False
                for i, stepper in enumerate(stepper_list):
                    position_after_stop = stepper.getPosition()
                    stepper.setTargetPosition(target_positions[i] - position_after_stop)
                continue
            elif key == 'i':
                return_flag = True
                stop_flag = False
                return
            else:
                while True:
                    print("Invalid key! Press 'r' to resume or 'q' to quit.")
                    key = input().strip().lower()
                    if key == 'r':
                        print("Resuming motors...")
                        stop_flag = False
                        for i, stepper in enumerate(stepper_list):
                            position_after_stop = stepper.getPosition()
                            stepper.setTargetPosition(target_positions[i] - position_after_stop)
                        break  # Exit the loop on valid input
                    elif key == 'q':
                        quit_flag = True
                        print("Exiting program...")
                        return
        time.sleep(0.1)

def return_to_initial_multiple(steppers):
    """
    Stage 4: Return steppers to initial positions.
    :param steppers: List of steppers to reset.
    """
    print("Returning steppers to initial positions.")
    for i in range(len(steppers)):
        steppers[i].setTargetPosition(0)
    print("All steppers returned to initial positions.")

def return_to_initial_single(stepper):
    """
    Stage 4: Return stepper to initial positions.
    :param stepper: Stepper to reset.
    """
    stepper.setTargetPosition(0)
    while stepper.getIsMoving():
        if quit_flag:
            return
        time.sleep(0.1)
    print("Stepper returned to initial position. Please quit program.")
    

def main():
    global stop_flag, quit_flag, return_flag, stage_1, stage_2, stage_3, stage_4, stage_5

    # Start input listener in a separate thread
    listener_thread = threading.Thread(target=input_listener, daemon=True)
    listener_thread.start()

    # Stage 1: Setup and enable devices
    fsr, stepper1, stepper2, stepper3, stepper4 = setup_devices()
    steppers = [stepper1, stepper2, stepper3, stepper4]

    # Stage 2: Stepper1 rotates until FSR threshold is reached. Platform lowering
    if stage_1:
        monitor_fsr(fsr, stepper1)

    if quit_flag:
        return
            
    if return_flag:
        print("Returning stepper1 back to original position")
        stage_2 = False
        stage_5 = True

    if stage_2:
        print("Twisting top and bottom scroll plate.")
        operate_stepper_multiple([stepper2, stepper3], [REV_STEPS_WITH_RESCALE/2, REV_STEPS_WITH_RESCALE/2])
        stage_3 = True
        stage_2 = False
        
    if return_flag:
        stage_3 = False
        stage_4 = True

    if quit_flag:
        return
    
    # Stage 3: Stepper 4 twists open jar
    if stage_3:
        print("Opening Jar")
        operate_stepper_single(stepper4, REV_STEPS_WITH_RESCALE)
        stage_4 = True
    
    if return_flag:
        print("Returning stepper2, stepper3, and stepper4 back to original position")
        stage_4 = True
    
    # Stage 4: Return to original position
    if stage_4:
        print("Press 'Enter' to ungrip jar.")
        key = input().strip().lower()
        if key == "":
            # Stage 4: Return motors to initial positions
            return_to_initial_multiple(steppers[1:])
            stage_5=True
            
    if stage_5:
        print("Remove jar. Press 'Enter' to raise platform")
        key = input().strip().lower()
        if key == "":
            return_to_initial_single(steppers[0])
        
    while not quit_flag:
       key = input().strip().lower()
       if key == 'q':
           quit_flag = True

    # Close devices
    print("Closing devices...")
    fsr.close()
    for i in range(len(steppers)):
        steppers[i].close()

    print("Program complete.")
    
if __name__ == "__main__":
    main()