import struct
import serial
import time
from threading import Thread, Lock

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
            print(frame)
            break
        if rx == b'\xf1':  # start of new frame
            start_frame_detected = True
            frame += rx
        if start_frame_detected:
            frame += rx

lock = Lock()

ser = serial.Serial("/dev/ttyAMA0", 115200)

# 0xf1 START OF FRAME 
# 0x01, 0x00, 0x01, 0x01, (TLV_COMMAND 1 length GET_STATUS)
# 0x08, 0x00, 0x02, 0x00, 0x00 (TLV_POWER_READING 2 length 0x00 0x00)
# 0x03, 0x00, 0x04, 0xFE, 0x83, 0xB3, 0x25 - crc32
# 0xf2 END OF FRAME
# GET_STATUS + RX_POWER
packed = struct.pack("B" * 18, 0xf1, 0x01, 0x00, 0x01, 0x01, 0x08, 0x00, 0x02, 0x00, 0x00, 0x03, 0x00, 0x04, 0xFE, 0x83, 0xB3, 0x25, 0xF2)

print(packed)
ser.write(packed)
read_frame()


