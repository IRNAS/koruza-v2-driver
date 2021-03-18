import struct
import serial
import time
from threading import Thread, Lock

from src.communication import *

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

ser = serial.Serial("/dev/ttyAMA0", 115200)

# 0xf1 START OF FRAME 
# 0x01, 0x00, 0x01, 0x01, (TLV_COMMAND 1 length GET_STATUS)
# 0x08, 0x00, 0x02, 0x00, 0x00 (TLV_POWER_READING 2 length 0x00 0x00)
# 0x03, 0x00, 0x04, 0xFE, 0x83, 0xB3, 0x25 - crc32
# 0xf2 END OF FRAME
# GET_STATUS + RX_POWER
# packed = struct.pack("B" * 18, 0xf1, 0x01, 0x00, 0x01, 0x01, 0x08, 0x00, 0x02, 0x00, 0x00, 0x03, 0x00, 0x04, 0xFE, 0x83, 0xB3, 0x25, 0xF2)

# print(packed)
# ser.write(packed)
# read_frame()

# # recreate same message with tlv_protocol.py

msg = Message()
tlv_command = create_command_tlv(TlvCommand.COMMAND_GET_STATUS)
msg.add_tlv(tlv_command)
# tlv_power_reading = create_power_reading_tlv(0x00)  # probably address of sfp?? - this is probably moved to raspberry pi now
# msg.add_tlv(tlv_power_reading)
# print(msg)
tlv_checksum = create_checksum_tlv(msg)
msg.add_tlv(tlv_checksum)
encoded_msg = msg.encode()
# print(f"Encoded message: {encoded_msg}")
frame = build_frame(encoded_msg)
ser.write(frame)
read_frame()


# BEFORE MOVING MOTORS WE HAVE TO EXPLICITLY CALL COMMAND_RESTORE_MOTOR
# CALL GET_MOTOR_STATUS EVEN EARLIER
msg = Message()
# 1. create command tlv
tlv_command = create_command_tlv(TlvCommand.COMMAND_RESTORE_MOTOR)
msg.add_tlv(tlv_command)
# 2. add motor position
motor_position = create_motor_position_tlv(0, 0, 0)
msg.add_tlv(motor_position)
# 3. add checksum
checksum_tlv = create_checksum_tlv(msg)
msg.add_tlv(checksum_tlv)
encoded_msg = msg.encode()
frame = build_frame(encoded_msg)
print(frame)
ser.write(frame)

# # THIS WORKS FOR SOME REASON
# # packed = struct.pack("B" * 28, 0xf1, 0x01, 0x00, 0x01, 0x07, 0x04, 0x00, 0x0C, 0xFF, 0xFF, 0xEF, 0x07, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x00, 0x04, 0xFC, 0xAD, 0x99, 0x20, 0xF2)
# # print(packed)
# # ser.write(packed)
# # '
# # packed = struct.pack("B" * 28, 0xf1, 0x01, 0x00, 0x01, 0x07, 0x04, 0x00, 0x0C, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x00, 0x04, 0xFC, 0xAD, 0x99, 0x20, 0xF2)
# # print(packed)
# # ser.write(packed)'

# time.sleep(0.5)
# TEST MOVE MOTORS
# msg = Message()
# # 1. always create command tlv first
# tlv_command = create_command_tlv(TlvCommand.COMMAND_MOVE_MOTOR)
# msg.add_tlv(tlv_command)
# # 2. create move motor tlv
# motor_command_left = create_motor_position_tlv(0, 0, 0)
# msg.add_tlv(motor_command_left)
# # 3. DON'T FORGET TO ADD CHECKSUM
# tlv_checksum = create_checksum_tlv(msg)
# msg.add_tlv(tlv_checksum)
# encoded_msg = msg.encode()
# print(f"Encoded motor command: {encoded_msg}")
# frame = build_frame(encoded_msg)
# ser.write(frame)
# time.sleep(1)
# packed = struct.pack("B" * 28, 0xf1, 0x01, 0x00, 0x01, 0x02, 0x04, 0x00, 0x0C, 0x80, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0xC9, 0x62, 0x00, 0x00, 0x00, 0x00, 0x03, 0x00, 0x04, 0x6E, 0x87, 0xBB, 0xAE, 0xF2)
# print(packed)
# ser.write(packed)
