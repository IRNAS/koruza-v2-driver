import serial
import math 

from communication import *
from threading import Lock

class MotorWrapper():
    def __init__(self, serial_port, baudrate=115200, timeout=2, lock=None):
        """Initialize motor wrapper"""
        self.ser = None
        self.ser = serial.Serial(serial_port, baudrate, timeout=timeout)
        self.lock = lock

        self.motor_wrapper_running = False

        self.position_x = None
        self.position_y = None
        self.position_z = None

    def __del__(self):
        try:
            if self.ser:
                self.ser.close()
                self.ser = None
        except Exception as e:
            raise e

    def get_motor_status(self):
        """Get motor status and update state"""

        msg = Message()
        tlv_command = create_command_tlv(TlvCommand.COMMAND_GET_STATUS)
        msg.add_tlv(tlv_command)
        tlv_checksum = create_checksum_tlv(msg)
        msg.add_tlv(tlv_checksum)
        encoded_msg = msg.encode()
        # print(f"Encoded message: {encoded_msg}")
        frame = build_frame(encoded_msg)

        
        self.lock.acquire()
        self.ser.write(frame)  # send message over serial
        self.lock.release()

        response = read_frame(self.ser)  # read response
        response_clean = clean_frame(response)
        print(f"Cleaned response: {response_clean}")
        parsed = message_parse(response_clean)
        # parse motor position from message
        print(f"Num decoded tlvs: {len(parsed[1].tlvs)}")
        if parsed[0] == MessageResult.MESSAGE_SUCCESS:
            # print(parsed[1])
            message = parsed[1]
            for tlv in message.tlvs:
                # print("new TLV")
                if tlv.type == TlvType.TLV_MOTOR_POSITION:  # get data from reply
                    print(tlv.to_string())

    def restore_motor(self, pos_x, pos_y, pos_z):
        """Restore motors to default position"""
        # pos_x = self.status["motors"]["x"]
        # pos_y = self.status["motors"]["y"]
        # pos_z = self.status["motors"]["z"]

        print(f"Restoring motors to: {pos_x}, {pos_y}, {pos_z}")
        msg = Message()
        tlv_command = create_command_tlv(TlvCommand.COMMAND_RESTORE_MOTOR)
        msg.add_tlv(tlv_command)
        motor_position = create_motor_position_tlv(pos_x, pos_y, pos_z)
        msg.add_tlv(motor_position)
        checksum = create_checksum_tlv(msg)
        msg.add_tlv(checksum)
        encoded_msg = msg.encode()
        frame = build_frame(encoded_msg)
        print(frame)

        self.lock.acquire()
        self.ser.write(frame)  # send message over serial
        self.lock.release()
        return True
        

    def move_motor(self, motors_connected, x, y, z):
        """Move motor to set position"""

        if not motors_connected:
            return False

        # print("Sending data to serial")
        print(f"Moving motors for {x} {y} {z}")
        msg = Message()
        tlv_command = create_command_tlv(TlvCommand.COMMAND_MOVE_MOTOR)
        msg.add_tlv(tlv_command)
        motor_position = create_motor_position_tlv(x, y, z)
        msg.add_tlv(motor_position)
        checksum = create_checksum_tlv(msg)
        msg.add_tlv(checksum)
        encoded_msg = msg.encode()
        frame = build_frame(encoded_msg)
        print(frame)

        self.lock.acquire()
        self.ser.write(frame)  # send message over serial
        self.lock.release()
        return True

    def homing(self, motors_connected):
        """Home to center"""

        if not motors_connected:
            return False

        msg = Message()
        cmd_home_motor = create_command_tlv(TlvCommand.COMMAND_HOMING)
        msg.add_tlv(cmd_home_motor)
        checksum = create_checksum_tlv(msg.tlvs)
        msg.add_tlv(checksum)
        encoded_msg = msg.encode()
        frame = build_frame(encoded_msg)

        self.lock.acquire()
        self.ser.write(frame)  # send message over serial
        self.lock.release()
        return True


# test code
# lock = Lock()
# motor_wrapper = MotorWrapper("/dev/ttyAMA0", lock=lock)
# motor_wrapper.koruza_move_motor(True, 1000, 0, 0)

