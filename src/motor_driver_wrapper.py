import serial
import math 

from tlv_protocol import *
from threading import Lock

class MotorWrapper():
    def __init__(self, serial_port, baudrate=115200, timeout=2, lock=None):
        """Initialize motor wrapper"""
        self.ser = None
        self.ser = serial.Serial(serial_port, baudrate, timeout=timeout)
        self.lock = lock

        self.motor_wrapper_running = False


    def __del__(self):
        try:
            if self.ser:
                self.ser.close()
                self.ser = None
        except Exception as e:
            raise e

    def koruza_restore_motor(self, pos_x, pos_y, pos_z):
        """Restore motors to default position"""
        # pos_x = self.status["motors"]["x"]
        # pos_y = self.status["motors"]["y"]
        # pos_z = self.status["motors"]["z"]

        encoded_message = EnocdedMessage()
        cmd_restore_motor = create_command_tlv(TlvCommand.COMMAND_RESTORE_MOTOR)
        motor_position_command = create_motor_position_tlv(pos_x, pos_y, pos_z)
        encoded_message.add_tlv(cmd_restore_motor)
        encoded_message.add_tlv(motor_position_command)
        checksum = create_checksum_tlv(encoded_message.tlvs)
        encoded_message.add_tlv(checksum)

        self.lock.acquire()
        self.ser.write(encoded_message.tlvs)  # send message over serial
        self.lock.release()
        return True
        

    def koruza_move_motor(self, motors_connected, x, y, z):
        """Move motor to set position"""

        if not motors_connected:
            return False

        # print("Sending data to serial")

        encoded_message = EnocdedMessage()
        cmd_move_motor = create_command_tlv(TlvCommand.COMMAND_MOVE_MOTOR)
        motor_position_command = create_motor_position_tlv(x, y, z)
        encoded_message.add_tlv(cmd_move_motor)
        encoded_message.add_tlv(motor_position_command)
        checksum = create_checksum_tlv(encoded_message.tlvs)
        encoded_message.add_tlv(checksum)

        self.lock.acquire()
        self.ser.write(encoded_message.tlvs)  # send message over serial
        self.lock.release()
        return True

    def koruza_homing(self, motors_connected):
        """Home to center"""

        if not motors_connected:
            return False

        encoded_message = EnocdedMessage()
        cmd_home_motor = create_command_tlv(TlvCommand.COMMAND_HOMING)
        encoded_message.add_tlv(cmd_home_motor)
        checksum = create_checksum_tlv(encoded_message.tlvs)
        encoded_message.add_tlv(checksum)

        self.lock.acquire()
        self.ser.write(encoded_message.tlvs)  # send message over serial
        self.lock.release()
        return True


# test code
# lock = Lock()
# motor_wrapper = MotorWrapper("/dev/ttyAMA0", lock=lock)
# motor_wrapper.koruza_move_motor(True, 1000, 0, 0)

