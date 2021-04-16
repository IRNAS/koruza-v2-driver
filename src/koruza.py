import serial
import logging
import logging.handlers
import json
from threading import Thread, Lock

from .led_control import LedControl
from .sfp_monitor import SfpMonitor
from .motor_control import MotorControl
from .gpio_control import GpioControl
from .communication import *
from .config_manager import ConfigManager

from ...src.constants import BLE_PORT
from ...src.colors import Color

import xmlrpc.client

log = logging.getLogger()

class Koruza():
    def __init__(self):
        """Initialize koruza.py wrapper with all drivers"""
        self.ser = serial.Serial("/dev/ttyAMA0", baudrate=115200, timeout=2)
        self.lock = Lock()

        # Init config manager
        self.config_manager = ConfigManager()

        # Init motor control
        self.motor_control = None
        try:
            self.motor_control = MotorControl(serial_handler=self.ser, lock=self.lock, config_manager=self.config_manager)  # open serial and start motor driver wrapper
            log.info("Initialized Motor Wrapper")
        except Exception as e:
            log.error(f"Failed to init Motor Driver: {e}")

        # Init led control
        self.led_control = None
        try:
            self.led_control = LedControl(config_manager=self.config_manager)
            log.info("Initialized Led Driver")
        except Exception as e:
            log.error(f"Failed to init LED Driver: {e}")

        # Init sfp control
        self.sfp_control = None
        try:
            self.sfp_control = SfpMonitor()
            log.info("Initialized Sfp Wrapper")
        except Exception as e:
            log.error(f"Failed to init SFP Wrapper: {e}")

        # Init sfp GPIO
        self.gpio_control = GpioControl()
        self.gpio_control.sfp_config()
        self.sfp_data = None  # prepare empty sfp data

        # Init ble driver
        self.ble_driver = None

        self.running = True

        time.sleep(1)
        # start loop
        sfp_diagnostics_loop = Thread(target=self._update_sfp_diagnostics, daemon=True)
        sfp_diagnostics_loop.start()

    def __del__(self):
        """Destructor"""
        self.running = False
        sfp_diagnostics_loop.join()

    def get_camera_config(self):
        """Return calibration config"""
        return self.config_manager.config["camera"]

    def update_camera_config(self, new_config):
        """Update calibration config with new values"""
        self.config_manager.update_camera_config(new_config)

    def get_calibration_config(self):
        """Return calibration config"""
        return self.config_manager.config["calibration"]

    def update_calibration_config(self, new_calib):
        """Update calibration config with new values"""
        self.config_manager.update_calibration_config(new_calib)

    def toggle_led(self):
        """Toggle led"""
        self.led_control.toggle_led()

    def get_sfp_diagnostics(self):
        """Expose sfp getter"""
        return self.sfp_data

    def _update_sfp_diagnostics(self):
        """Run in thread to update sfp diagnostics and update LED color"""
        while self.running:
            self.sfp_data = self._get_sfp_data()
            rx_power_dBm = self.sfp_data["sfp_0"]["diagnostics"]["rx_power_dBm"]
            self.set_led_color(rx_power_dBm)
            time.sleep(1)  # update once a second

    def issue_ble_command(self, command, params):
        """Issue ble command with a new client connection, close connection after call"""
        return  # TODO implement BLE client
        with xmlrpc.client.ServerProxy(f"http://localhost:{BLE_PORT}", allow_none=True) as client:
            print(f"Issuing ble command {command} with {params}")
            client.send_command(command, params)  

    def _get_sfp_data(self):
        self.sfp_control.update_sfp_diagnostics()
        sfp_data = self.sfp_control.get_complete_diagnostics()
        return sfp_data

    def get_motors_position(self):
        """Expose getter for motor position"""
        return self.motor_control.position_x, self.motor_control.position_y

    def set_led_color(self, rx_power):
        """Expose method to set LED color"""
        if rx_power >= -40:
            color = Color.NO_SIGNAL
        if rx_power >= -38:
            color = Color.BAD_SIGNAL
        if rx_power >= -30:
            color = Color.VERY_WEAK_SIGNAL
        if rx_power >= -25:
            color = Color.WEAK_SIGNAL
        if rx_power >= -20:
            color = Color.MEDIUM_SIGNAL
        if rx_power >= -15:
            color = Color.GOOD_SIGNAL
        if rx_power >= -10:
            color = Color.VERY_GOOD_SIGNAL
        if rx_power >= -5:
            color = Color.EXCELLENT_SIGNAL
        self.led_control.set_color(color)

    def disable_led(self):
        """Expose method to disable LED"""
        self.led_control.turn_off()

    def move_motors(self, steps_x, steps_y, steps_z):
        """Expose method to move motors"""
        self.motor_control.move_motor(steps_x, steps_y, steps_z)

    def move_motors_to(self, x, y, z):
        """Expose method to move motors to (x, y, z)"""
        self.motor_control.move_motor(x, y, z)

    def home(self):
        """Expose method for koruza homing"""
        self.motor_control.home()

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