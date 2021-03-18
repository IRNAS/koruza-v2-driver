import struct
import serial
import time
from threading import Lock

from motor_driver_wrapper import MotorWrapper
from communication import *

def read_frame():
    """Read frame, starting with 0xf1 and ending with 0xf2"""
    frame = b''  # initialize empty byte
    start_frame_detected = False
    while True:
        rx = ser.read()
        # print(rx)
        if rx == b'\xf2':  # end of frame
            start_frame_detected = False
            frame += rx
            print(f"Response: {frame}")
            break
        if rx == b'\xf1':  # start of new frame
            start_frame_detected = True
            frame += rx
        if start_frame_detected:
            frame += rx

def parse_test_vector(vector):
    vals = vector.lower().split(" ")
    vals = [int("0x" + v, 16) for v in vals]
    # for v in vals:
    #     print(v)
    #     print(int("0x" + v, 16))
    # print(vals)
    return struct.pack("B" * len(vals), *vals)


# # # RESTORE MOTORS
ser = serial.Serial("/dev/ttyAMA0", 115200)
packed = struct.pack("B" * 28, 0xf1, 0x01, 0x00, 0x01, 0x07, 0x04, 0x00, 0x0C, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x00, 0x04, 0x72, 0x07, 0x40, 0xDA, 0xF2)
print(packed)
ser.write(packed)

# # # GET_STATUS = "F1 01 00 01 01 03 00 04 A5 05 DF 1B F2"
# # # GET_STATUS_MSG = parse_test_vector(GET_STATUS)
# # # ser.write(GET_STATUS_MSG)  # write and get response
# # # read_frame()

# # # GET_STATUS_RX_POWER = "F1 01 00 01 01 08 00 02 04 44 03 00 04 EB 5E F3 F3 A8 F2"
# # # GET_STATUS_RX_POWER_MSG = parse_test_vector(GET_STATUS_RX_POWER)
# # # ser.write(GET_STATUS_RX_POWER_MSG)  # write and get response
# # # read_frame()

time.sleep(5)
print("MOVING FOR 1000 0 0")
MOVE_MOTORS_1000_0_0 = "F1 01 00 01 02 04 00 0C 00 00 03 E8 00 00 00 00 00 00 00 00 03 00 04 05 F3 F1 6B 39 F2"
MOVE_MOTORS_MSG = parse_test_vector(MOVE_MOTORS_1000_0_0)
print(MOVE_MOTORS_MSG)
ser.write(MOVE_MOTORS_MSG)

time.sleep(5)
print("MOVING FOR -1000 0 0")
MOVE_MOTORS_NEG_1000_0_0 = "F1 01 00 01 02 04 00 0C FF FF FC 18 00 00 00 00 00 00 00 00 03 00 04 5E 62 9D 78 F2"
MOVE_MOTORS_MSG = parse_test_vector(MOVE_MOTORS_NEG_1000_0_0)
print(MOVE_MOTORS_MSG)
ser.write(MOVE_MOTORS_MSG)

# # MOVE Y MOTOR
time.sleep(5)
print("MOVING FOR 0 1000 0")
MOVE_MOTORS_1000_0_0 = "F1 01 00 01 02 04 00 0C 00 00 00 00 00 00 03 E8 00 00 00 00 03 00 04 F3 F1 18 0D 79 F2"
MOVE_MOTORS_MSG = parse_test_vector(MOVE_MOTORS_1000_0_0)
print(MOVE_MOTORS_MSG)
ser.write(MOVE_MOTORS_MSG)

# # DOESNT WORK APPARENTLY
time.sleep(5)
print("MOVING FOR 0 -1000 0")
MOVE_MOTORS_1000_0_0 = "F1 01 00 01 02 04 00 0C 00 00 00 00 FF FF FC 18 00 00 00 00 03 00 04 F3 F1 18 0D 79 F2"
MOVE_MOTORS_MSG = parse_test_vector(MOVE_MOTORS_1000_0_0)
print(MOVE_MOTORS_MSG)
ser.write(MOVE_MOTORS_MSG)

# # MOVE Y MOTOR
time.sleep(5)
print("MOVING FOR 0 0 0")
MOVE_MOTORS_0_0_0 = "F1 01 00 01 02 04 00 0C 00 00 00 00 00 00 00 00 00 00 00 00 03 00 04 6F 28 F3 F3 C9 F2"
MOVE_MOTORS_MSG = parse_test_vector(MOVE_MOTORS_0_0_0)
print(MOVE_MOTORS_MSG)
ser.write(MOVE_MOTORS_MSG)

# MOVE ALL THREE AXES
time.sleep(5)
print("MOVING FOR 1000 1000 1000")
MOVE_MOTORS_1000_1000_1000 = "F1 01 00 01 02 04 00 0C 00 00 03 E8 00 00 03 E8 00 00 03 E8 03 00 04 1E 3D AC 00 F2"
MOVE_MOTORS_MSG = parse_test_vector(MOVE_MOTORS_1000_1000_1000)
print(MOVE_MOTORS_MSG)
ser.write(MOVE_MOTORS_MSG)


""" TEST SAME THING WITH motor_driver_wrapper """
# ser = serial.Serial("/dev/ttyAMA0", 115200)
# packed = struct.pack("B" * 28, 0xf1, 0x01, 0x00, 0x01, 0x07, 0x04, 0x00, 0x0C, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x00, 0x04, 0x72, 0x07, 0x40, 0xDA, 0xF2)
# print(packed)
# ser.write(packed)

lock = Lock()
# time.sleep(5)
motor_driver = MotorWrapper("/dev/ttyAMA0", baudrate=115200, timeout=2, lock=lock)
# manually restore motor position at init
motor_driver.restore_motor(0, 0, 0)
time.sleep(0.5)
# motor_driver.get_motor_status()

time.sleep(5)
print("MOVING FOR 1000 0 0")
motor_driver.move_motor(True, 1000, 0, 0)

time.sleep(5)
print("MOVING FOR -1000 0 0")
motor_driver.move_motor(True, -1000, 0, 0)

# # MOVE Y MOTOR
time.sleep(5)
print("MOVING FOR 0 1000 0")
motor_driver.move_motor(True, 0, 1000, 0)

# DOESNT WORK APPARENTLY
time.sleep(5)
time.sleep(5)
print("MOVING FOR 0 -1000 0")
motor_driver.move_motor(True, 0, -1000, 0)

# # MOVE Y MOTOR
time.sleep(5)
print("MOVING FOR 0 0 0")
motor_driver.move_motor(True, 0, 0, 0)

# # MOVE Y MOTOR
time.sleep(5)
print("MOVING FOR 1000 1000 1000")
motor_driver.move_motor(True, 1000, 1000, 1000)