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
from .data_manager import DataManager

from ...src.constants import DEVICE_MANAGEMENT_PORT
from ...src.colors import Color

import xmlrpc.client

log = logging.getLogger()

class Koruza():
    def __init__(self):
        """Initialize koruza.py wrapper with all drivers"""
        self.ser = serial.Serial("/dev/ttyAMA0", baudrate=115200, timeout=2)
        self.lock = Lock()


        # Init remote device manager xmlrpc client
        self.remote_device_manager_client = xmlrpc.client.ServerProxy(f"http://localhost:{DEVICE_MANAGEMENT_PORT}", allow_none=True)

        # Init config manager
        self.data_manager = DataManager()

        # Init sfp GPIO
        self.gpio_control = GpioControl()
        self.gpio_control.sfp_config()
        self.sfp_data = None  # prepare empty sfp data

        # Init motor control
        self.motor_control = None
        try:
            self.motor_control = MotorControl(serial_handler=self.ser, lock=self.lock, data_manager=self.data_manager)  # open serial and start motor driver wrapper
            log.info("Initialized Motor Wrapper")
        except Exception as e:
            log.error(f"Failed to init Motor Driver: {e}")

        # Init led control
        self.led_control = None
        try:
            self.led_control = LedControl(data_manager=self.data_manager)
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

        # Init ble driver
        self.ble_driver = None

        self.running = True

        time.sleep(1)
        # start loop
        self.sfp_diagnostics_loop = Thread(target=self._update_sfp_diagnostics, daemon=True)
        self.sfp_diagnostics_loop.start()

    def __del__(self):
        """Destructor"""
        self.running = False
        self.sfp_diagnostics_loop.join()

    def get_led_data(self):
        """Return calibration data"""
        return self.data_manager.data["led"]

    def update_led_data(self, new_data):
        """Update calibration data with new values"""
        self.data_manager.update_led_data(new_data)

    def get_calibration_data(self):
        """Return calibration data"""
        return self.data_manager.data["calibration"]

    def update_calibration_data(self, new_data):
        """Update calibration data with new values"""
        self.data_manager.update_calibration_data(new_data)

    def toggle_led(self):
        """Toggle led"""
        self.led_control.toggle_led()

    def get_sfp_diagnostics(self):
        """Expose sfp getter"""
        return self.sfp_data

    def _update_sfp_diagnostics(self):
        """Run in thread to update sfp diagnostics and update LED color"""
        while self.running:
            # TODO handle properly
            try:
                self.sfp_data = self._get_sfp_data()
                rx_power_dBm = self.sfp_data["sfp_0"]["diagnostics"]["rx_power_dBm"]
                self.set_led_color(rx_power_dBm)
            except Exception as e:
                log.warning(e)
            time.sleep(0.2)  # update five times

    def issue_remote_command(self, command, params):
        """Issue RPC call to other unit with a RPC client instance"""
        # make synchronous for now, later this will have to be async for it to work!
        
        try:
            # print("Issuing remote command to second unit")
            response = self.remote_device_manager_client.request_remote(command, params)
            # print(f"Requested remote done, response: {response}")
            return response
        except Exception as e:
            log.error(f"Failed to get response from remote unit: {e}")
            return None

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

    def move_motors(self, steps_x, steps_y, steps_z=0):
        """Expose method to move motors"""
        self.motor_control.move_motor(steps_x, steps_y, steps_z)

    def move_motors_to(self, x, y):
        """Expose method to move motors to (x, y, z)"""
        self.motor_control.move_motor_to(x, y, 0)

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

    # def snapshot(self):
    #     try:
    #         self._camera = picamera.PiCamera()
    #         self._camera.resolution = self.RESOLUTION
    #         self._camera.hflip = True
    #         self._camera.vflip = True
    #         print("Camera initialised.")
    #     except picamera.PiCameraError:
    #         print("ERROR: Failed to initialize camera.")

    #     # Capture snapshot
    #     with picamera.array.PiRGBArray(self._camera) as output:
    #         self._camera.capture(output, format='bgr')
    #         # Store image to ndarray and convert it to grayscale
    #         frame = cv2.cvtColor(output.array, cv2.COLOR_BGR2GRAY)
    #         cv2.imwrite(os.path.join(self.CAMERA_STORAGE_PATH,'test-snapshot.jpg'),frame)
    #         # Crop
    #         frame = frame[self._crop_y:self._crop_y + 0.4 * self.RESOLUTION[1], self._crop_x:self._crop_x + 0.4 * self.RESOLUTION[0]]

    #     self._camera.close()

    #     return frame


    # def calibration_forward_transform(self):
    #     """Calibration forward transform"""
    #     self.status["camera_calibration"]["offset_x"] = self.status["camera_calibration"]["global_offset_x"] - \
    #         self.status["camera_calibration"]["zoom_x"] * \
    #         self.status["camera_calibration"]["width"] / self.status["camera_calibration"]["zoom_w"]

    #     self.status["camera_calibration"]["offset_y"] = self.status["camera_calibration"]["global_offset_y"] - \
    #         self.status["camera_calibration"]["zoom_y"] * \
    #         self.status["camera_calibration"]["height"] / self.status["camera_calibration"]["zoom_h"]

    # def calibration_inverse_transform(self):
    #     """Calibration inverse transform"""
    #     self.status["camera_calibration"]["global_offset_x"] = self.status["camera_calibration"]["offset_x"] * \
    #         self.status["camera_calibration"]["zoom_w"] + \
    #         self.status["camera_calibration"]["zoom_x"] * self.status["camera_calibration"]["width"]

    #     self.status["camera_calibration"]["global_offset_y"] = self.status["camera_calibration"]["offset_y"] * \
    #         self.status["camera_calibration"]["zoom_h"] + \
    #         self.status["camera_calibration"]["zoom_y"] * self.status["camera_calibration"]["height"]

    # def set_webcam_calibration(self, offset_x, offset_y):
    #     # Given offsets are in zoomed-in coordinates, so we need to transform them
    #     # to global coordinates based on configured zoom levels.
    #     self.status["camera_calibration"]["offset_x"] = offset_x
    #     self.status["camera_calibration"]["offset_y"] = offset_y
    #     self.koruza_calibration_inverse_transform()

    # def set_distance(distance):
    #     """Set camera distance"""
    #     self.status["camera_calibration"]["distance"] = distance