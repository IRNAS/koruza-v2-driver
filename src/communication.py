"""
Defines and implements actions for TLV protocol used for motor driver communication
"""

import serial
import struct
import binascii

# MOVE TO CONSTANTS
MAX_TLV_COUNT = 25

### HELPER FUNCTIONS ###
def convert_to_bytes(value, num_bytes):
    return value.to_bytes(length=num_bytes, byteorder="big")

def bytes_to_int(byte_array, signed=False):
    return int.from_bytes(byte_array, byteorder="big", signed=signed)

def message_checksum(encoded_message):
    return binascii.crc32(encoded_message)

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
        print(f"Tlv type: {self.type}, tlv value: {self.value}")

""" Representation of a protocol message in bytes """
class Message():
    def __init__(self):
        self.tlv_objs = []

    def add_tlv(self, tlv):
        """Add tlv object to message. Encode before sending"""
        self.tlv_objs.append(tlv)

    def encode(self):
        """Encode all tlvs into byte array"""
        encoded_msg = b''
        for tlv in self.tlv_objs:
            encoded_msg += tlv.encode()

        return encoded_msg

""" Representation of a protocol message in objects (decoded TLVs) """
class DecodedMessage():
    def __init__(self):
        self.tlvs = []

    def add_tlv(self, tlv):
        """Add tlv to message, increase message length"""
        self.tlvs.append(tlv)

# def parse_tlv(tlv_type, tlv_message):
#     """Parse tlv and save into tlv class based on type"""
#     tlv = Tlv(type=tlv_type)
#     if tlv_type == TlvType.TLV_COMMAND:
#         tlv.value = parse_command_tlv(tlv_message)
#     if tlv_type == TlvType.TLV_REPLY:
#         tlv.value = parse_reply_tlv(tlv_message)
#     if tlv_type == TlvType.TLV_CHECKSUM:
#         tlv.value = parse_checksum_tlv(tlv_message)
#     if tlv_type == TlvType.TLV_MOTOR_POSITION:
#         tlv.value = parse_motor_position_tlv(tlv_message)
#     if tlv_type == TlvType.TLV_CURRENT_READING:
#         tlv.value = parse_current_reading_tlv(tlv_message)
#     if tlv_type == TlvType.TLV_SFP_CALIBRATION:
#         tlv.value = parse_sfp_calibration_tlv(tlv_message)
#     if tlv_type == TlvType.TLV_ERROR_REPORT:
#         tlv.value = parse_error_report_tlv(tlv_message)
#     if tlv_type == TlvType.TLV_POWER_READING:
#         tlv.value = parse_power_reading_tlv(tlv_message)
#     if tlv_type == TlvType.TLV_ENCODER_VALUE:
#         tlv.value = parse_encoder_value_tlv(tlv_message)
#     return tlv

""" Create TLV """
# NOTE: observed weird behaviour with packing bytes in this order or similar: "BHB" should pack 4 bytes but actually packs 5???
def create_command_tlv(command):
    tlv = Tlv(TlvType.TLV_COMMAND, [0x00, 0x01], [command])
    # tlv = struct.pack("BBBB", TlvType.TLV_COMMAND, 0x00, 0x01, command)
    return tlv

def create_reply_tlv(reply):
    tlv = Tlv(TlvType.TLV_REPLY, [0x00, 0x01], [reply])
    # tlv = struct.pack("BBB", TlvType.TLV_REPLY, 0x00, 0x01, reply)
    return tlv

def create_motor_position_tlv(x, y, z):
    #tlv = Tlv(type=TlvType.TLV_MOTOR_POSITION, length=12)  # motor position is int32_t, so 3*4 bytes
    x_bytes = convert_to_bytes(x, 4)
    y_bytes = convert_to_bytes(y, 4)
    z_bytes = convert_to_bytes(z, 4)
    tlv = Tlv(TlvType.TLV_MOTOR_POSITION, [0x00, 0x0C], [*x_bytes, *y_bytes, *z_bytes])
    # tlv = struct.pack("BBBBBBBBBBBBBBB", TlvType.TLV_MOTOR_POSITION, 0x00, 0x0C, x_bytes[0], x_bytes[1], x_bytes[2], x_bytes[3], y_bytes[0], y_bytes[1], y_bytes[2], y_bytes[3], z_bytes[0], z_bytes[1], z_bytes[2], z_bytes[3])
    return tlv

def create_error_report_tlv(report):
    r_bytes = convert_to_bytes(report, 4)
    tlv = Tlv(TlvType.TLV_ERROR_REPORT, [0x00, 0x04], [*r_bytes])
    # tlv = struct.pack("BBBI", TlvType.TLV_ERROR_REPORT, 0x00, 0x04, report)
    return tlv

def create_current_reading_tlv(current):
    c_bytes = convert_to_bytes(current, 2)
    tlv = Tlv(TlvType.TLV_CURRENT_READING, [0x00, 0x02], [*c_bytes])
    # tlv = struct.pack("BBBH", TlvType.TLV_CURRENT_READING, 0x00, 0x02, current)
    return tlv

def create_power_reading_tlv(power):
    p_bytes = convert_to_bytes(power, 2)
    tlv = Tlv(TlvType.TLV_POWER_READING, [0x00, 0x02], [*p_bytes])
    # tlv = struct.pack("BBBBB", TlvType.TLV_POWER_READING, 0x00, 0x02, p_bytes[0], p_bytes[1])
    return tlv

def create_encoder_value_tlv(x, y):
    x_bytes = convert_to_bytes(x, 4)
    y_bytes = convert_to_bytes(y, 4)
    tlv = Tlv(TlvType.TLV_ENCODER_VALUE, [0x00, 0x08], [*x_bytes, *y_bytes])
    # tlv = struct.pack("BBBBBBBBBBB", TlvType.TLV_ENCODER_VALUE, 0x00, 0x08, x_bytes[0], x_bytes[1], x_bytes[2], x_bytes[3], y_bytes[0], y_bytes[1], y_bytes[2], y_bytes[3])
    return tlv

def create_sfp_calibration_tlv(offset_x, offset_y):
    offset_x_bytes = convert_to_bytes(offset_x, 4)
    offset_y_bytes = convert_to_bytes(offset_y, 4)
    tlv = Tlv(TlvType.TLV_SFP_CALIBRATION, [0x00, 0x08], [*offset_x_bytes, *offset_y_bytes])
    # tlv = struct.pack("BBBBBBBBBB", TlvType.TLV_SFP_CALIBRATION, 0x00, 0x08, offset_x_bytes[0], offset_x_bytes[1], offset_x_bytes[2], offset_x_bytes[3], offset_y_bytes[0], offset_y_bytes[1], offset_y_bytes[2], offset_y_bytes[3])
    return tlv

def create_checksum_tlv(message):
    check_sum = 0
    tlv_values_appended = b''
    for tlv in message.tlv_objs:
        tlv_len = int.from_bytes(bytearray(tlv.length), "big", signed=False)
        print(f"Tlv len: {tlv_len}")
        tlv_values_appended += struct.pack("B" * tlv_len,  *tlv.value)
    checksum = binascii.crc32(tlv_values_appended)
    checksum_bytes = convert_to_bytes(checksum, 4)
    tlv = Tlv(TlvType.TLV_CHECKSUM, [0x00, 0x04], [checksum_bytes[0], checksum_bytes[1], checksum_bytes[2], checksum_bytes[3]])
    return tlv

""" Parse received TLV """
def parse_tlv(tlv_bytearray):
    print(f"tlv bytearray: {tlv_bytearray}")
    type = tlv_bytearray[0]  #first byte is TLV Type
    length = int.from_bytes(tlv_bytearray[1:3], "big")  #next two bytes are length of value
    value = struct.unpack("B" * length, tlv_bytearray[3:3+length])
    tlv = Tlv(type=type, length=length, value=value)  # handle value later when processing tlv
    print(tlv)
    return tlv

# def parse_command_tlv(tlv):
#     unpacked = struct.unpack("BBBB", tlv)
#     print(unpacked)
#     command = unpacked[2]
#     return command

# def parse_reply_tlv(tlv):
#     unpacked = struct.unpack("BHB", tlv)
#     reply = unpacked[2]
#     return reply

# def parse_motor_position_tlv(tlv):
#     unpacked = struct.unpack("BHBBBBBBBBBBBB", tlv)
#     x = bytes_to_int(unpacked[2:6], signed=True)
#     y = bytes_to_int(unpacked[6:10], signed=True)
#     z = bytes_to_int(unpacked[10:14], signed=True)
#     motor_pos = MotorPosition(x, y, z)
#     return motor_pos

# def parse_error_report_tlv(tlv):
#     unpacked = struct.unpack("BHI", tlv)
#     error_report = unpacked[2]
#     error_report = ErrorReport(error_report)
#     return error_report

# def parse_current_reading_tlv(tlv):
#     unpacked = struct.unpack("BHH", tlv)
#     current = unpacked[2]
#     return current

# def parse_power_reading_tlv(tlv):
#     unpacked = struct.unpack("BHH", tlv)
#     power = unpacked[2]
#     return power

# def parse_encoder_value_tlv(tlv):
#     unpacked = struct.unpack("BHBBBBBBBB", tlv)
#     x = bytes_to_int(unpacked[2:6], signed=True)
#     y = bytes_to_int(unpacked[6:10], signed=True)
#     encoder_value = EncoderValue(x, y)
#     return encoder_value

# def parse_sfp_calibration_tlv(tlv):
#     unpacked = struct.unpack("BHBBBBBBBB", tlv)
#     offset_x = bytes_to_int(unpacked[2:6], signed=False)
#     offset_y = bytes_to_int(unpacked[6:10], signed=False)
#     calib = SfpCalibration(offset_x, offset_y)
#     return calib

# def parse_checksum_tlv(tlv):
#     unpacked = struct.unpack("BHBBBB", tlv)
#     checksum = bytes_to_int(unpacked[2:6], signed=False)
#     return checksum

# [type: 1 byte] [length: 2 bytes] [value: length bytes] - one TLV
# [TLV#1] [TLV#2] ...
""" Parse message consisting of TLV packets """
def message_parse(message):
    """
    Parse message containing TLV commands.
    Input is (probably) a byte array coming from the motor driver.
    """
    messages = Message()  # init new message class, parse data into it
    print(f"Whole message length: {len(message)}")

    offset = 0
    while offset < len(message):
        # if len(messages.tlvs) >= MAX_TLV_COUNT:  # not sure yet how this is gonna work, since we're not working with c structs here
        #     return MessageResult.MESSAGE_ERROR_TOO_MANY_TLVS, None

        start_offset = offset
        unpacked_tlv_type = message[offset:offset+1]  # parse using correct offsets
        print(f"tlv type buffer: {message[offset:offset+1]}")
        print(f"Unpacked tlv_type: {unpacked_tlv_type}")
        offset += 1  # increment offset by 1 (remember, size is 1 byte in size)
        print(f"Offset after unpacking type: {offset}")

        length = int.from_bytes(message[offset:offset+2], "big")  # length is 2 bytes in size
        print(f"length buffer: {message[offset:offset+2]}")
        print(f"Unpacked length: {length}")
        offset += (2 + length)
        print(f"Offset after unpacking length: {offset}")

        tlv_message = message[start_offset:offset]
        print(f"Whole tlv: {tlv_message}")
        tlv = parse_tlv(tlv_message)

        if unpacked_tlv_type == TlvType.TLV_CHECKSUM:
            checksum = message_checksum(message[0:start_offset])  # check checksum on message so far
            if checksum != tlv.value:
                return MessageResult.MESSAGE_ERROR_CHECKSUM_MISMATCH, None

        messages.add_tlv(tlv)

        # offset += 1
        print(f"Offset after unpacking TLV: {offset}")

    return MessageResult.MESSAGE_SUCCESS, messages  # return value is MessageResult, msg (None if fail)

def build_frame(byte_array_message):
    """Add 0xf1 to beginning of message and 0xf2 to end of message"""
    return b'\xf1' + byte_array_message + b'\xf2'

# test message packing
msg = Message()
tlv_command = create_command_tlv(TlvCommand.COMMAND_MOVE_MOTOR)  # len 1
msg.add_tlv(tlv_command)
tlv_reply = create_reply_tlv(TlvReply.REPLY_ERROR_REPORT)  # len 1
msg.add_tlv(tlv_reply)
tlv_motor_position = create_motor_position_tlv(123, 123, 123)  # len 12
msg.add_tlv(tlv_motor_position)
tlv_motor_current = create_current_reading_tlv(12345)  # len 2
msg.add_tlv(tlv_motor_current)
tlv_sfp_calib = create_sfp_calibration_tlv(200, 400)  # len 8
msg.add_tlv(tlv_sfp_calib)
tlv_error_report = create_error_report_tlv(123)  # len 4
msg.add_tlv(tlv_error_report)
tlv_power_reading = create_power_reading_tlv(130)  # len 2
msg.add_tlv(tlv_power_reading)
tlv_encoder = create_encoder_value_tlv(55, 66)  # len 8
msg.add_tlv(tlv_encoder)
tlv_checksum = create_checksum_tlv(msg)
msg.add_tlv(tlv_checksum)

framed_msg = build_frame(msg.encode())
print(framed_msg)

# parse message, discard frames, look for them elsewhere TODO
framed_msg = framed_msg[1:-1]
print(framed_msg)

message_parse(framed_msg)

# message_result, decoded_message = message_parse(encoded_message.tlvs)

# for decoded_tlv in decoded_message.tlvs:
#     decoded_tlv.to_string()