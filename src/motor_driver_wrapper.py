import time
import serial
import math 
import logging
import json

from .communication import *
from threading import Thread, Lock

from ...src.config_manager import config_manager

log = logging.getLogger()
SETTINGS_FILE = "./koruza_v2/config.json"  # load settings file on init and write current motor pos and calibration

class MotorWrapper():
    def __init__(self, serial_handler, lock):
        """Initialize motor wrapper"""
        # init global json config manager
        self.config_manager = config_manager

        self.ser = None
        self.ser = serial_handler
        self.lock = lock

        self.motor_wrapper_running = False

        self.position_x = self.config_manager.motors["last_x"]  # read from json file
        self.position_y = self.config_manager.motors["last_y"]  # read from json file
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
            print(e)
            pass

    def motor_status_loop(self):
        """Periodically read motor values"""
        while True:
            # time.sleep(1)
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
        # print(f"Encoded message: {encoded_msg}")
        frame = build_frame(encoded_msg)

        self.lock.acquire()
        self.ser.write(frame)  # send message over serial
        try:
            response = read_frame(self.ser)  # read response
            self.lock.release()
            # print(response)
            # return True
        except Exception as e:
            print(e)
            self.lock.release()
            return None  # return None if serial timed out - no motor connected

        if not self.motors_connected:
            self.motors_connected = True
            self.restore_motor(self.position_x, self.position_y, 0)
             
        # cleaning files on this
        # response = b"\xf1\x02\x00\x01\x01\x04\x00\x0c\x00\x00'\x10\x00\x00'\x10\x00\x00\x00\x00\t\x00\x08\x00\x00\x00[\xff\xff\xff\xf3\xf2\x03\x00\x04\x86\x80\xbbz\xf2"
        # self.motors_connected = True  # set motors connected if message was received
        
        # print(f"Received response: {response}")
        response_clean = clean_frame(response)
        # print(f"Cleaned response: {response_clean}")
        try:
            parsed = message_parse(response_clean)
            # parse motor position from message
            # print(f"Num decoded tlvs: {len(parsed[1].tlvs)}")
            if parsed[0] == MessageResult.MESSAGE_SUCCESS:
                # print(parsed[1])
                message = parsed[1]
                for tlv in message.tlvs:
                    # print(tlv)
                    # print("new TLV")
                    if tlv.type == TlvType.TLV_MOTOR_POSITION:  # get data from reply
                        # print("MOTOR POSITION TLV")
                        self.position_x = bytes_to_int(bytearray(tlv.value[0:4]), signed=True)
                        self.position_y = bytes_to_int(bytearray(tlv.value[4:8]), signed=True)
                        self.position_z = bytes_to_int(bytearray(tlv.value[8:12]), signed=True)

                        # update config.json
                        self.config_manager.update_motors_config([("last_x", self.position_x), ("last_y", self.position_y)])
                
                    if tlv.type == TlvType.TLV_ENCODER_VALUE:  # get data from reply
                        self.encoder_x = bytes_to_int(bytearray(tlv.value[0:4]), signed=True)
                        self.encoder_y = bytes_to_int(bytearray(tlv.value[4:8]), signed=True)

            return True  # return True if success

        except Exception as e:
            print(f"Trouble parsing response: {e}")
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
        # print(f"Restoring motors to: {pos_x}, {pos_y}, {pos_z}")
        print(f"Restoring motor position!")
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
        
    def move_motor_to(self, x, y, z):
        """Move motor to set position"""
        if not self.motors_connected:
            return False

        # received resp
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

    def move_motor(self, x, y, z):
        """Move motor relative to current position"""

        if not self.motors_connected:
            return False

        print(f"Moving motors for {x} {y} {z}")
        x = self.position_x + x
        y = self.position_y + y
        z = self.position_z + z
        # received resp
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

    def home(self):
        """Home to center"""

        if not self.motors_connected:
            return False

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