import serial
import logging
import json
from threading import Thread, Lock

from .src.led_driver import LedDriver
from .src.sfp_wrapper import SfpWrapper
from .src.motor_driver_wrapper import MotorWrapper
from .src.gpio_control import GpioControl
from .src.communication import *

from ..src.constants import BLE_PORT
from ..src.config_manager import config_manager

from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
import xmlrpc.client

log = logging.getLogger()

class Koruza():
    def __init__(self):
        """Initialize koruza.py wrapper with all drivers"""
        self.ser = serial.Serial("/dev/ttyAMA0", baudrate=115200, timeout=2)
        self.lock = Lock()

        self.motor_wrapper = None
        try:
            self.motor_wrapper = MotorWrapper(serial_handler=self.ser, lock=self.lock)  # open serial and start motor driver wrapper
            print("Initialized Motor Wrapper")
        except Exception as e:
            print(f"Failed to init Motor Driver: {e}")

        self.led_driver = None
        try:
            self.led_driver = LedDriver()
            print("Initialized Led Driver")
        except Exception as e:
            print("Failed to init LED Driver")

        self.sfp_wrapper = None
        try:
            self.sfp_wrapper = SfpWrapper()
            print("Initialized Sfp Wrapper")
        except Exception as e:
            print("Failed to init SFP Wrapper")

        self.gpio_control = GpioControl()
        self.gpio_control.sfp_config()

        self.ble_driver = None

    def issue_ble_command(self, command, params):
        """Issue ble command with a new client connection, close connection after call"""
        return  # TODO implement BLE client
        with xmlrpc.client.ServerProxy(f"http://localhost:{BLE_PORT}", allow_none=True) as client:
            print(f"Issuing ble command {command} with {params}")
            client.send_command(command, params)  

    def get_sfp_data(self):
        self.sfp_wrapper.update_sfp_diagnostics()
        sfp_data = self.sfp_wrapper.get_complete_diagnostics()
        return sfp_data

    def get_motors_position(self):
        """Expose getter for motor position"""
        return self.motor_wrapper.position_x, self.motor_wrapper.position_y

    def set_led_color(self, color, mode):
        """Expose method to set LED color"""
        self.led_driver.set_color(color, mode)

    def disable_led(self):
        """Expose method to disable LED"""
        self.led_driver.turn_off()

    def move_motors(self, steps_x, steps_y, steps_z):
        """Expose method to move motors"""
        self.motor_wrapper.move_motor(steps_x, steps_y, steps_z)

    def move_motors_to(self, x, y, z):
        """Expose method to move motors to (x, y, z)"""
        self.motor_wrapper.move_motor(x, y, z)

    def home(self):
        """Expose method for koruza homing"""
        self.motor_wrapper.home()

    def reboot_motor_driver(self):
        """Reboot motor driver."""
        # not implemented on motor end
        msg = Message()
        tlv_command = create_command_tlv(TlvCommand.COMMAND_REBOOT)
        msg.add_tlv(tlv_command)
        checksum = create_checksum_tlv(msg)
        msg.add_tlv(checksum)
        encoded_msg = msg.encode()
        frame = build_frame(encoded_msg)
        # print(frame)

        self.lock.acquire()
        self.ser.write(frame)  # send message over serial
        self.lock.release()
        return True

    def upgrade_motor_driver(self):
        """Update motor driver MCU firmware"""
        msg = Message()
        tlv_command = create_command_tlv(TlvCommand.COMMAND_FIRMWARE_UPGRADE)
        msg.add_tlv(tlv_command)
        checksum = create_checksum_tlv(msg)
        msg.add_tlv(checksum)
        encoded_msg = msg.encode()
        frame = build_frame(encoded_msg)

        self.lock.acquire()
        self.ser.write(frame)  # send message over serial
        self.lock.release()
        return True

    def hard_reset(self):
        """Power cycle motor driver unit"""
        self.gpio_control.koruza_reset()

    def calibration_forward_transform(self):
        """Calibration forward transform"""
        self.status["camera_calibration"]["offset_x"] = self.status["camera_calibration"]["global_offset_x"] - \
            self.status["camera_calibration"]["zoom_x"] * \
            self.status["camera_calibration"]["width"] / self.status["camera_calibration"]["zoom_w"]

        self.status["camera_calibration"]["offset_y"] = self.status["camera_calibration"]["global_offset_y"] - \
            self.status["camera_calibration"]["zoom_y"] * \
            self.status["camera_calibration"]["height"] / self.status["camera_calibration"]["zoom_h"]

    def calibration_inverse_transform(self):
        """Calibration inverse transform"""
        self.status["camera_calibration"]["global_offset_x"] = self.status["camera_calibration"]["offset_x"] * \
            self.status["camera_calibration"]["zoom_w"] + \
            self.status["camera_calibration"]["zoom_x"] * self.status["camera_calibration"]["width"]

        self.status["camera_calibration"]["global_offset_y"] = self.status["camera_calibration"]["offset_y"] * \
            self.status["camera_calibration"]["zoom_h"] + \
            self.status["camera_calibration"]["zoom_y"] * self.status["camera_calibration"]["height"]

    def set_webcam_calibration(self, offset_x, offset_y):
        # Given offsets are in zoomed-in coordinates, so we need to transform them
        # to global coordinates based on configured zoom levels.
        self.status["camera_calibration"]["offset_x"] = offset_x
        self.status["camera_calibration"]["offset_y"] = offset_y
        self.koruza_calibration_inverse_transform()

    def set_distance(distance):
        """Set camera distance"""
        self.status["camera_calibration"]["distance"] = distance


# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)

with SimpleXMLRPCServer(('localhost', 8000),
                        requestHandler=RequestHandler, allow_none=True) as server:
    server.register_introspection_functions()
    server.register_instance(Koruza())
    print('Serving XML-RPC on localhost port 8000')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received, exiting.")
        # sys.exit(0)

