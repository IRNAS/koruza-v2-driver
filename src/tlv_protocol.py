"""
Defines and implements actions for TLV protocol used for motor driver communication
"""

import serial
import struct

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
    def __init__(self):
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
    def __init__(self):
        self.code = None  # uint32_t type

""" Contents of the TLV_SFP_CALIBRATION TLV """
class SfpCalibration():
    def __init__(self):
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


def parse_tlv(tlv_type, tlv_message):
    tlv = Tlv(type=tlv_type)
    if tlv_type == TlvType.TLV_COMMAND:
        tlv.value = parse_command_tlv(tlv_message)
    if tlv_type == TlvType.TLV_REPLY:
        tlv.value = parse_reply_tlv(tlv_message)
    if tlv_type == TlvType.TLV_CHECKSUM:
        tlv.value = parse_checksum_tlv(tlv_message)
    if tlv_type == TlvType.TLV_MOTOR_POSITION:
        tlv.value = parse_motor_position_tlv(tlv_message)
    if tlv_type == TlvType.TLV_CURRENT_READING:
        tlv.value = parse_current_reading_tlv(tlv_message)
    if tlv_type == TlvType.TLV_SFP_CALIBRATION:
        tlv.value = parse_sfp_calibration_tlv(tlv_message)
    if tlv_type == TlvType.TLV_ERROR_REPORT:
        tlv.value = parse_error_report_tlv(tlv_message)
    if tlv_type == TlvType.TLV_POWER_READING:
        tlv.value = parse_power_reading_tlv(tlv_message)
    if tlv_type == TlvType.TLV_ENCODER_VALUE:
        tlv.value = parse_encoder_value_tlv(tlv_message)

    return tlv

def create_command_tlv(command):
    tlv = struct.pack("BHB", TlvType.TLV_COMMAND, 1, command)
    return tlv

def create_reply_tlv(reply):
    tlv = struct.pack("BHB", TlvType.TLV_REPLY, 1, reply)
    return tlv

def create_motor_position_tlv(x, y, z):
    #tlv = Tlv(type=TlvType.TLV_MOTOR_POSITION, length=12)  # motor position is int32_t, so 3*4 bytes
    x_bytes = convert_to_bytes(x, 4)
    y_bytes = convert_to_bytes(y, 4)
    z_bytes = convert_to_bytes(z, 4)
    tlv = struct.pack("BHBBBBBBBBBBBB", TlvType.TLV_MOTOR_POSITION, 12, x_bytes[0], x_bytes[1], x_bytes[2], x_bytes[3], y_bytes[0], y_bytes[1], y_bytes[2], y_bytes[3], z_bytes[0], z_bytes[1], z_bytes[2], z_bytes[3])
    return tlv

def create_error_report_tlv(report):
    tlv = struct.pack("BHI", TlvType.TLV_ERROR_REPORT, 4, report)
    return tlv

def create_current_reading_tlv(current):
    tlv = struct.pack("BHH", TlvType.TLV_CURRENT_READING, 2, current)
    return tlv

def create_power_reading_tlv(power):
    tlv = struct.pack("BHH", TlvType.TLV_POWER_READING, 2, power)
    return tlv

def create_encoder_value_tlv(x, y):
    x_bytes = convert_to_bytes(x, 4)
    y_bytes = convert_to_bytes(y, 4)
    tlv = struct.pack("BHBBBBBBBB", TlvType.TLV_ENCODER_VALUE, 8, x_bytes[0], x_bytes[1], x_bytes[2], x_bytes[3], y_bytes[0], y_bytes[1], y_bytes[2], y_bytes[3])
    return tlv

def create_sfp_calibration_tlv(offset_x, offset_y):
    offset_x_bytes = convert_to_bytes(offset_x, 4)
    offset_y_bytes = convert_to_bytes(offset_y, 4)
    tlv = struct.pack("BHBBBBBBBB", TlvType.TLV_SFP_CALIBRATION, 8, offset_x_bytes[0], offset_x_bytes[1], offset_x_bytes[2], offset_x_bytes[3], offset_y_bytes[0], offset_y_bytes[1], offset_y_bytes[2], offset_y_bytes[3])
    return tlv

def create_checksum_tlv(checksum):
    checksum_bytes = convert_to_bytes(checksum, 4)
    tlv = struct.pack("BHBBBB", TlvType.TLV_SFP_CALIBRATION, 4, checksum_bytes[0], checksum_bytes[1], checksum_bytes[2], checksum_bytes[3])
    return tlv

### HELPER FUNCTIONS ###
def convert_to_bytes(value, num_bytes):
    return value.to_bytes(length=num_bytes, byteorder="big")

def bytes_to_int(byte_array, signed=False):
    return int.from_bytes(byte_array, byteorder="big", signed=signed)

class Tlv():
    def __init__(self, type=None, value=None):
        self.type = type
        self.value = value

    def to_string(self):
        print(f"Tlv type: {self.type}, tlv value: {self.value}")

""" Representation of a protocol message """
class EnocdedMessage():
    def __init__(self):
        self.tlvs = b''

    def add_tlv(self, tlv):
        """Add tlv to message, increase message length"""
        self.tlvs += tlv

class DecodedMessage():
    def __init__(self):
        self.tlvs = []

    def add_tlv(self, tlv):
        """Add tlv to message, increase message length"""
        self.tlvs.append(tlv)

def parse_command_tlv(tlv):
    unpacked = struct.unpack("BHB", tlv)
    print(unpacked)
    command = unpacked[2]
    return command

def parse_reply_tlv(tlv):
    unpacked = struct.unpack("BHB", tlv)
    reply = unpacked[2]
    return reply

def parse_motor_position_tlv(tlv):
    unpacked = struct.unpack("BHBBBBBBBBBBBB", tlv)
    x = bytes_to_int(unpacked[2:6], signed=True)
    y = bytes_to_int(unpacked[6:10], signed=True)
    z = bytes_to_int(unpacked[10:14], signed=True)
    return [x, y, z]

def parse_error_report_tlv(tlv):
    unpacked = struct.unpack("BHI", tlv)
    error_report = unpacked[2]
    return error_report

def parse_current_reading_tlv(tlv):
    unpacked = struct.unpack("BHH", tlv)
    current = unpacked[2]
    return current

def parse_power_reading_tlv(tlv):
    unpacked = struct.unpack("BHH", tlv)
    power = unpacked[2]
    return power

def parse_encoder_value_tlv(tlv):
    unpacked = struct.unpack("BHBBBBBBBB", tlv)
    x = bytes_to_int(unpacked[2:6], signed=True)
    y = bytes_to_int(unpacked[6:10], signed=True)
    return [x, y]

def parse_sfp_calibration_tlv(tlv):
    unpacked = struct.unpack("BHBBBBBBBB", tlv)
    offset_x = bytes_to_int(unpacked[2:6], signed=False)
    offset_y = bytes_to_int(unpacked[6:10], signed=False)
    return [offset_x, offset_y]

def parse_checksum_tlv(tlv):
    unpacked = struct.unpack("BHBBBB", tlv)
    checksum = bytes_to_int(unpacked[2:6], signed=False)
    return checksum

# [type: 1 byte] [length: 2 bytes] [value: length bytes] - one TLV
# [TLV#1] [TLV#2] ...
""" Functions used to create and parse messages """
def message_parse(message):
    """
    Parse message containing TLV commands.
    Input is (probably) a byte array coming from the motor driver.
    """
    messages = DecodedMessage()  # init new message class, parse data into it
    print(f"Whole message length: {len(message)}")

    offset = 0
    while offset < len(message):
        # if len(message) >= MAX_TLV_COUNT:  # not sure yet how this is gonna work, since we're not working with c structs here
        #     return MessageResult.MESSAGE_ERROR_TOO_MANY_TLVS, None

        start_offset = offset
        unpacked_tlv_type = struct.unpack("B", message[offset:offset+1])[0]  # parse using correct offsets
        print(f"Unpacked tlv_type: {unpacked_tlv_type}")
        offset += 1  # increment offset by 1 (remember, size is 1 byte in size)

        length = struct.unpack(">H", message[offset:offset+2])[0]  # length is 2 bytes in size
        print(f"Unpacked length: {length}")
        offset += (2 + length)

        tlv_message = message[start_offset:offset+1]
        print(f"Whole tlv: {tlv_message}")
        tlv = parse_tlv(unpacked_tlv_type, tlv_message)

        messages.add_tlv(tlv)

        offset += 1
        print(f"Offset after unpacking TLV: {offset}")

        # if tlv.type == TlvType.TLV_CHECKSUM:
        #     checksum = message_checksum(message)  # TODO implement all other checks as well

    return MessageResult.MESSAGE_SUCCESS, messages  # return value is MessageResult, msg (None if fail)
    


## test message packing
encoded_message = EnocdedMessage()
tlv_command = create_command_tlv(TlvCommand.COMMAND_MOVE_MOTOR)
encoded_message.add_tlv(tlv_command)
tlv_reply = create_reply_tlv(TlvReply.REPLY_ERROR_REPORT)
encoded_message.add_tlv(tlv_reply)
tlv_motor_position = create_motor_position_tlv(123, 123, 123)
encoded_message.add_tlv(tlv_motor_position)
tlv_motor_current = create_current_reading_tlv(12345)
encoded_message.add_tlv(tlv_motor_current)
tlv_sfp_calib = create_sfp_calibration_tlv(200, 400)
encoded_message.add_tlv(tlv_sfp_calib)
tlv_error_report = create_error_report_tlv(123)
encoded_message.add_tlv(tlv_error_report)
tlv_power_reading = create_power_reading_tlv(130)
encoded_message.add_tlv(tlv_power_reading)
tlv_encoder = create_encoder_value_tlv(55, 66)
encoded_message.add_tlv(tlv_encoder)

# # print(f"TLV Command move motor: {tlv_command}")
# # print(f"Parsed command enum: {parse_command_tlv(tlv_command)}")

message_result, decoded_message = message_parse(encoded_message.tlvs)

for decoded_tlv in decoded_message.tlvs:
    decoded_tlv.to_string()