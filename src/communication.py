"""
Defines and implements actions for TLV protocol used for motor driver communication
"""

import time
import serial
import struct
import binascii
import logging

log = logging.getLogger()

# MOVE TO CONSTANTS
MAX_TLV_COUNT = 25

### HELPER FUNCTIONS ###
def convert_to_bytes(value, num_bytes, signed=False):
    return value.to_bytes(length=num_bytes, byteorder="big", signed=signed)

def bytes_to_int(byte_array, signed=False):
    return int.from_bytes(byte_array, byteorder="big", signed=signed)

def message_checksum(encoded_message):
    return binascii.crc32(encoded_message)

class Marker():
    START = int.from_bytes(b'\xf1', "big")
    END = int.from_bytes(b'\xf2', "big")
    ESCAPE = int.from_bytes(b'\xf3', "big")

""" Defines all TLV supported by the protocol """
class TlvType():
    TLV_COMMAND = 1
    TLV_REPLY = 2
    TLV_CHECKSUM = 3
    TLV_MOTOR_POSITION = 4
    TLV_CURRENT_READING = 5
    TLV_SFP_CALIBRATION = 6
    TLV_ERROR_REPORT = 7
    TLV_POWER_READING = 8
    TLV_ENCODER_VALUE = 9
    TLV_VIBRATION_VALUE = 10

    TLV_NET_HELLO = 100
    TLV_NET_SIGNATURE = 101

""" Defines commands supported by the TLV_COMMAND TLV """
class TlvCommand():
    COMMAND_GET_STATUS = 1
    COMMAND_MOVE_MOTOR = 2
    COMMAND_SEND_IR = 3
    COMMAND_REBOOT = 4
    COMMAND_FIRMWARE_UPGRADE = 5
    COMMAND_HOMING = 6
    COMMAND_RESTORE_MOTOR = 7

""" Defines replies supported by the TLV_REPPLY TLV """
class TlvReply():
    REPLY_STATUS_REPORT = 1
    REPLY_ERROR_REPORT = 2

""" Contents of the TLV_MOTOR_POSITION TLV """
class MotorPosition():
    def __init__(self, x=None, y=None, z=None):
        self.x = x  # int32_t type
        self.y = y  # int32_t type
        self.z = z  # int32_t type

""" Contents of the TLV_ENCODER_VALUE TLV """
class EncoderValue():
    def __init__(self, x=None, y=None):
        self.x = None  # int32_t type
        self.y = None  # int32_t type

""" Contents of the TLV_VIBRATION_VALUE TLV """
""" DEPRECATED """
class VibrationValue():
    def __init__(self):
        self.avg_x = None  # int32_t type
        self.avg_y = None  # int32_t type
        self.avg_z = None  # int32_t type

        self.max_x = None  # int32_t type
        self.max_y = None  # int32_t type
        self.max_z = None  # int32_t type

""" Contents of the TLV_ERROR_REPORT TLV """
class ErrorReport():
    def __init__(self, code=None):
        self.code = None  # uint32_t type

""" Contents of the TLV_SFP_CALIBRATION TLV """
class SfpCalibration():
    def __init__(self, offset_x, offset_y):
        self.offset_x = None  # uint32_t type
        self.offset_y = None  # uint32_t type

""" Message operations result codes """
class MessageResult():
    MESSAGE_SUCCESS = 0
    MESSAGE_ERROR_TOO_MANY_TLVS = -1
    MESSAGE_ERROR_OUT_OF_MEMORY = -2
    MESSAGE_ERROR_BUFFER_TOO_SMALL = -3
    MESSAGE_ERROR_PARSE_ERROR = -4
    MESSAGE_ERROR_CHECKSUM_MISMATCH = -5
    MESSAGE_ERROR_TLV_NOT_FOUND = -6

""" TLV and message classes"""
class Tlv():
    def __init__(self, type=None, length=None, value=None):
        self.type = type
        self.length = length
        self.value = value

    def encode(self):
        """Encode tlv to byte string"""
        encoded = struct.pack("BBB" + "B" * len(self.value), self.type, *self.length, *self.value)
        return encoded

    def to_string(self):
        return f"Tlv type: {self.type}, tlv value: {self.value}"

""" Representation of a protocol message in bytes """
class Message():
    def __init__(self):
        self.tlvs = []

    def add_tlv(self, tlv):
        """Add tlv object to message. Encode before sending"""
        self.tlvs.append(tlv)

    def encode(self):
        """Encode all tlvs into byte array"""
        encoded_msg = b''
        for tlv in self.tlvs:
            encoded_msg += tlv.encode()

        return encoded_msg

""" Representation of a protocol message in objects (decoded TLVs) """
class DecodedMessage():
    def __init__(self):
        self.tlvs = []

    def add_tlv(self, tlv):
        """Add tlv to message, increase message length"""
        self.tlvs.append(tlv)

""" Create TLV """
# NOTE: observed weird behaviour with packing bytes in this order or similar: "BHB" should pack 4 bytes but actually packs 5???
def create_command_tlv(command):
    tlv = Tlv(TlvType.TLV_COMMAND, [0x00, 0x01], [command])
    return tlv

def create_reply_tlv(reply):
    tlv = Tlv(TlvType.TLV_REPLY, [0x00, 0x01], [reply])
    return tlv

def create_motor_position_tlv(x, y, z):
    x_bytes = convert_to_bytes(x, 4, signed=True)
    y_bytes = convert_to_bytes(y, 4, signed=True)
    z_bytes = convert_to_bytes(z, 4, signed=True)
    tlv = Tlv(TlvType.TLV_MOTOR_POSITION, [0x00, 0x0C], [*x_bytes, *y_bytes, *z_bytes])
    return tlv

def create_error_report_tlv(report):
    r_bytes = convert_to_bytes(report, 4)
    tlv = Tlv(TlvType.TLV_ERROR_REPORT, [0x00, 0x04], [*r_bytes])
    return tlv

def create_current_reading_tlv(current):
    c_bytes = convert_to_bytes(current, 2)
    tlv = Tlv(TlvType.TLV_CURRENT_READING, [0x00, 0x02], [*c_bytes])
    return tlv

def create_power_reading_tlv(power):
    p_bytes = convert_to_bytes(power, 2)
    tlv = Tlv(TlvType.TLV_POWER_READING, [0x00, 0x02], [*p_bytes])
    return tlv

def create_encoder_value_tlv(x, y):
    x_bytes = convert_to_bytes(x, 4, signed=True)
    y_bytes = convert_to_bytes(y, 4, signed=True)
    tlv = Tlv(TlvType.TLV_ENCODER_VALUE, [0x00, 0x08], [*x_bytes, *y_bytes])
    return tlv

def create_sfp_calibration_tlv(offset_x, offset_y):
    offset_x_bytes = convert_to_bytes(offset_x, 4)
    offset_y_bytes = convert_to_bytes(offset_y, 4)
    tlv = Tlv(TlvType.TLV_SFP_CALIBRATION, [0x00, 0x08], [*offset_x_bytes, *offset_y_bytes])
    return tlv

def create_checksum_tlv(message):
    check_sum = 0
    tlv_values_appended = b''
    for tlv in message.tlvs:
        tlv_len = int.from_bytes(bytearray(tlv.length), "big", signed=False)
        tlv_values_appended += struct.pack("B" * tlv_len,  *tlv.value)
    checksum = binascii.crc32(tlv_values_appended)
    checksum_bytes = convert_to_bytes(checksum, 4)
    tlv = Tlv(TlvType.TLV_CHECKSUM, [0x00, 0x04], [checksum_bytes[0], checksum_bytes[1], checksum_bytes[2], checksum_bytes[3]])
    return tlv

""" Parse received TLV """
def parse_tlv(tlv_bytearray):
    type = tlv_bytearray[0]  #first byte is TLV Type
    length = int.from_bytes(tlv_bytearray[1:3], "big")  #next two bytes are length of value
    value = struct.unpack("B" * length, tlv_bytearray[3:3+length])
    tlv = Tlv(type=type, length=length, value=value)  # handle value later when processing tlv
    return tlv

# [type: 1 byte] [length: 2 bytes] [value: length bytes] - one TLV
# [TLV#1] [TLV#2] ...
""" Parse message consisting of TLV packets """
def message_parse(message):
    """
    Parse message containing TLV commands.
    Input is (probably) a byte array coming from the motor driver.
    """
    messages = Message()  # init new message class, parse data into it

    offset = 0
    while offset < len(message):

        start_offset = offset
        unpacked_tlv_type = message[offset:offset+1]  # parse using correct offsets
        offset += 1  # increment offset by 1 (remember, Size is 1 byte in size)

        length = int.from_bytes(message[offset:offset+2], "big")  # length is 2 bytes in size
        offset += (2 + length)

        tlv_message = message[start_offset:offset]

        try:
            tlv = parse_tlv(tlv_message)

            if unpacked_tlv_type == TlvType.TLV_CHECKSUM:
                checksum = message_checksum(message[0:start_offset])  # check checksum on message so far
                if checksum != tlv.value:
                    return MessageResult.MESSAGE_ERROR_CHECKSUM_MISMATCH, None

            messages.add_tlv(tlv)
        except Exception as e:
            log.error(f"During tlv parsing an exception occured: {e}")

    return MessageResult.MESSAGE_SUCCESS, messages  # return value is MessageResult, msg (None if fail)

def build_frame(bytes_msg):
    """Add 0xf1 to beginning of message and 0xf2 to end of message"""
    insert_indices = []
    for index, b in enumerate(bytes_msg):
        # escape all frame markers
        if b == Marker.START or b == Marker.END or b == Marker.ESCAPE:
            insert_indices.append(index)

    bytes_msg = bytearray(bytes_msg)  # bytes is immutable, change to bytearray
    for ind in insert_indices:
        bytes_msg[ind:ind] = b'\xf3'
    return b'\xf1' + bytes(bytes_msg) + b'\xf2'

def read_frame(ser, timeout=2):
    """Read frame, starting with 0xf1 and ending with 0xf2"""
    frame = b''  # initialize empty byte
    start_frame_detected = False
    prev_char = None

    start_time = time.time()

    while True:
        rx = ser.read()
        if rx == b'\xf2' and prev_char != b'\xf3':  # end of frame if not escaped by '\xf3'
            start_frame_detected = False
            frame += rx
            break
        if rx == b'\xf1' and prev_char != b'\xf3':  # start of new frame
            start_frame_detected = True
        if start_frame_detected:
            frame += rx

        if time.time() - start_time > timeout:
            raise Exception("Serial timed out")

        prev_char = rx
    
    return frame

def clean_frame(frame):
    """Clear markers from frame"""
    start_index = 0
    end_index = 0
    remove_indices = []
    prev_char = None
    for index, b in enumerate(frame):

        # clean frame of escape character \xf3

        # clean START markers
        if b == Marker.START and not prev_char == Marker.END:
            start_index = index
        elif b == Marker.START and prev_char == Marker.END:
            remove_indices.append(index-1)
        
        # clean END markers
        if Marker.END and not prev_char == Marker.ESCAPE:
            end_index = index
        elif Marker.END and prev_char == Marker.ESCAPE:
            remove_indices.append(index-1)

        # clean ESCAPE markers
        if b == Marker.ESCAPE and prev_char == Marker.ESCAPE:
            remove_indices.append(index-1)

        prev_char = b

    frame_byte_array = bytearray(frame)
    for ind in remove_indices:
        try:
            del frame_byte_array[ind]  # remove from byte array
        except Exception as e:
            log.error(f"Error removing at index {ind}")

    frame = bytes(frame_byte_array)
    return frame[start_index+1:end_index - len(remove_indices)]