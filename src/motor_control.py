import time
import serial
import math 
import logging
import json

from .communication import *
from threading import Thread, Lock

log = logging.getLogger()

class MotorControl():
    def __init__(self, serial_handler, lock, data_manager):
        """Initialize motor wrapper"""

        self.data_manager = data_manager

        self.ser = None
        self.ser = serial_handler
        self.lock = lock

        self.motor_wrapper_running = False

        self.position_x = self.data_manager.data["motors"]["last_x"]  # read from json file
        self.position_y = self.data_manager.data["motors"]["last_y"]  # read from json file
        self.position_z = None

        self.encoder_x = None
        self.encoder_y = None

        self.motor_loop_running = True

        self.motors_connected = False  # set to true when first data is read


        self.restore_motor(self.position_x, self.position_y, 0)  # restore motor on init - restore to previous stored position in koruza.py - restore to 0,0,0 here
        time.sleep(0.5)

        self.motor_data_thread = Thread(target=self.motor_status_loop, daemon=True)
        self.motor_data_thread.start()

    def __del__(self):
        try:
            if self.ser:
                self.ser.close()
                self.ser = None
        except Exception as e:
            log.error(f"Error when trying to close serial: {e}")

    def motor_status_loop(self):
        """Periodically read motor values"""
        while True:
            if self.motor_loop_running:
                ret = self.get_motor_status()
                if ret is None:
                    self.motors_connected = False
            else:
                break
            time.sleep(0.5)

    # NOTE: this has to run periodically to get last motor position and move accordingly
    def get_motor_status(self):
        """Get motor status and update state"""

        msg = Message()
        tlv_command = create_command_tlv(TlvCommand.COMMAND_GET_STATUS)
        msg.add_tlv(tlv_command)
        tlv_checksum = create_checksum_tlv(msg)
        msg.add_tlv(tlv_checksum)
        encoded_msg = msg.encode()
        frame = build_frame(encoded_msg)

        self.lock.acquire()
        self.ser.write(frame)  # send message over serial
        try:
            response = read_frame(self.ser)  # read response
            # print(f"Read response: {response}")
            self.lock.release()
        except Exception as e:
            log.error(f"Error when reading frame: {e}")
            self.lock.release()
            return None  # return None if serial timed out - no motor connected

        if not self.motors_connected:
            self.motors_connected = True
            self.restore_motor(self.position_x, self.position_y, 0)
            time.sleep(0.5)
        
        response_clean = clean_frame(response)

        self.lock.acquire()
        try:
            parsed = message_parse(response_clean)
            if parsed[0] == MessageResult.MESSAGE_SUCCESS:
                message = parsed[1]
                for tlv in message.tlvs:
                    print(f"Tlv type: {tlv.type}")
                    print(f"Tlv value: {tlv.value}")
                    if tlv.type == TlvType.TLV_MOTOR_POSITION:  # get data from reply
                        self.position_x = bytes_to_int(bytearray(tlv.value[0:4]), signed=True)
                        self.position_y = bytes_to_int(bytearray(tlv.value[4:8]), signed=True)
                        self.position_z = bytes_to_int(bytearray(tlv.value[8:12]), signed=True)

                        self.data_manager.update_motors_data([("last_x", self.position_x), ("last_y", self.position_y)])
                
                    if tlv.type == TlvType.TLV_ENCODER_VALUE:  # get data from reply
                        self.encoder_x = bytes_to_int(bytearray(tlv.value[0:4]), signed=True)
                        self.encoder_y = bytes_to_int(bytearray(tlv.value[4:8]), signed=True)

                        print(f"Encoder x: {self.encoder_x}, encoder y: {self.encoder_y}")
            
            self.lock.release()
            return True  # return True if success

        except Exception as e:
            log.error(f"Error parsing motor response: {e}")
            self.lock.release()  # release lock after completion/failure
            return False  # return False if message received but failed to parse


    def restore_motor(self, pos_x=0, pos_y=0, pos_z=0):
        """Restore motors to default position"""

        if self.position_x is not None:
            pos_x = self.position_x
        if self.position_y is not None:
            pos_y = self.position_y
        if self.position_z is not None:
            pos_z = self.position_z

        log.info(f"Restoring motor position")

        msg = Message()
        tlv_command = create_command_tlv(TlvCommand.COMMAND_RESTORE_MOTOR)
        msg.add_tlv(tlv_command)
        motor_position = create_motor_position_tlv(pos_x, pos_y, pos_z)
        msg.add_tlv(motor_position)
        checksum = create_checksum_tlv(msg)
        msg.add_tlv(checksum)
        encoded_msg = msg.encode()
        frame = build_frame(encoded_msg)

        self.lock.acquire()
        self.ser.write(frame)  # send message over serial
        self.lock.release()
        return True
        

    def move_motor_to(self, x, y, z):
        """Move motor to set position"""

        if not self.motors_connected:
            return False

        log.info("Moving motors to")

        msg = Message()
        tlv_command = create_command_tlv(TlvCommand.COMMAND_MOVE_MOTOR)
        msg.add_tlv(tlv_command)
        motor_position = create_motor_position_tlv(x, y, z)
        msg.add_tlv(motor_position)
        checksum = create_checksum_tlv(msg)
        msg.add_tlv(checksum)
        encoded_msg = msg.encode()
        frame = build_frame(encoded_msg)

        self.lock.acquire()
        self.ser.write(frame)  # send message over serial
        self.lock.release()
        return True


    def move_motor(self, x, y, z):
        """Move motor relative to current position"""

        if not self.motors_connected:
            return False

        log.info("Moving motors")

        x = self.position_x + x
        y = self.position_y + y
        z = self.position_z + z

        msg = Message()
        tlv_command = create_command_tlv(TlvCommand.COMMAND_MOVE_MOTOR)
        msg.add_tlv(tlv_command)
        motor_position = create_motor_position_tlv(x, y, z)
        msg.add_tlv(motor_position)
        checksum = create_checksum_tlv(msg)
        msg.add_tlv(checksum)
        encoded_msg = msg.encode()
        frame = build_frame(encoded_msg)

        self.lock.acquire()
        self.ser.write(frame)  # send message over serial
        self.lock.release()
        return True


    def home(self):
        """Home to center"""

        if not self.motors_connected:
            return False

        log.info("Homing")

        msg = Message()
        cmd_home_motor = create_command_tlv(TlvCommand.COMMAND_HOMING)
        msg.add_tlv(cmd_home_motor)
        checksum = create_checksum_tlv(msg)
        msg.add_tlv(checksum)
        encoded_msg = msg.encode()
        frame = build_frame(encoded_msg)

        self.lock.acquire()
        self.ser.write(frame)  # send message over serial
        self.lock.release()
        return True