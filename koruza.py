import serial
from threading import Thread, Lock

from .src.led_driver import LedDriver
from .src.sfp_wrapper import SfpWrapper
from .src.motor_driver_wrapper import MotorWrapper
from .src.communication import *

class Koruza():
    def __init__(self):
        """Initialize koruza.py wrapper with all drivers"""
        
        self.ser = serial.Serial("/dev/ttyAMA0", baudrate=115200, timeout=2)
        self.lock = Lock()

        self.motor_wrapper = None
        try:
            self.motor_wrapper = MotorWrapper(serial_handler=serial.Serial("/dev/ttyAMA0", baudrate=115200, timeout=2), lock=self.lock)  # open serial and start motor driver wrapper
            print("Initialized Motor Wrapper")
        except Exception as e:
            print("Failed to init Motor Driver")

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

    def koruza_reboot(self):
        """Reboot koruza"""
        msg = Message()
        tlv_command = create_command_tlv(TlvCommand.COMMAND_REBOOT)
        msg.add_tlv(tlv_command)
        checksum = create_checksum_tlv(msg)
        msg.add_tlv(checksum)

        self.lock.acquire()
        self.ser.write(encoded_message)  # send message over serial
        self.lock.release()
        return True

    def koruza_firmware_upgrade(self):
        """Update koruza firmware"""
        msg = Message()
        tlv_command = create_command_tlv(TlvCommand.COMMAND_FIRMWARE_UPGRADE)
        msg.add_tlv(tlv_command)
        checksum = create_checksum_tlv(msg)
        msg.add_tlv(checksum)

        self.lock.acquire()
        self.ser.write(encoded_message)  # send message over serial
        self.lock.release()
        return True

    def koruza_hard_reset(self):
        """Hard reset koruza unit"""
        # TODO implement gpio commands
        pass

    def koruza_calibration_forward_transform(self):
        """Calibration forward transform"""
        self.status["camera_calibration"]["offset_x"] = self.status["camera_calibration"]["global_offset_x"] - \
            self.status["camera_calibration"]["zoom_x"] * \
            self.status["camera_calibration"]["width"] / self.status["camera_calibration"]["zoom_w"]

        self.status["camera_calibration"]["offset_y"] = self.status["camera_calibration"]["global_offset_y"] - \
            self.status["camera_calibration"]["zoom_y"] * \
            self.status["camera_calibration"]["height"] / self.status["camera_calibration"]["zoom_h"]

    def koruza_calibration_inverse_transform(self):
        """Calibration inverse transform"""
        self.status["camera_calibration"]["global_offset_x"] = self.status["camera_calibration"]["offset_x"] * \
            self.status["camera_calibration"]["zoom_w"] + \
            self.status["camera_calibration"]["zoom_x"] * self.status["camera_calibration"]["width"]

        self.status["camera_calibration"]["global_offset_y"] = self.status["camera_calibration"]["offset_y"] * \
            self.status["camera_calibration"]["zoom_h"] + \
            self.status["camera_calibration"]["zoom_y"] * self.status["camera_calibration"]["height"]

    def koruza_set_webcam_calibration(self, offset_x, offset_y):
        # Given offsets are in zoomed-in coordinates, so we need to transform them
        # to global coordinates based on configured zoom levels.
        self.status["camera_calibration"]["offset_x"] = offset_x
        self.status["camera_calibration"]["offset_y"] = offset_y
        self.koruza_calibration_inverse_transform()

    def koruza_set_distance(distance):
        """Set camera distance"""
        self.status["camera_calibration"]["distance"] = distance
