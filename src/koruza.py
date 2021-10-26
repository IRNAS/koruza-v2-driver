import json
import serial
import socket
import logging
import requests
import subprocess
import logging.handlers

from threading import Thread, Lock

from .communication import *
from .led_control import LedControl
from .sfp_monitor import SfpMonitor
from .data_manager import DataManager
from .gpio_control import GpioControl
from .motor_control import MotorControl

from ...src.colors import Color
from ...src.camera_util import *
from ...src.config_manager import get_config, set_config
from ...src.constants import DEVICE_MANAGEMENT_PORT

import xmlrpc.client

log = logging.getLogger()

class Koruza():
    def __init__(self):
        """Initialize koruza.py wrapper with all drivers"""
        log.info(f"Initialized koruza main")
        self.ser = serial.Serial("/dev/ttyAMA0", baudrate=115200, timeout=2)
        self.lock = Lock()

        # Get device configuration
        self.config = get_config()
        log.info(f"Loaded config: {self.config}")

        # Init remote device manager xmlrpc client
        self.remote_device_manager_client = xmlrpc.client.ServerProxy(f"http://localhost:{DEVICE_MANAGEMENT_PORT}", allow_none=True)

        # Init config manager
        self.data_manager = DataManager()

        # Init sfp GPIO
        self.gpio_control = GpioControl()
        self.gpio_control.sfp_config()
        self.sfp_data = {}  # prepare empty sfp data

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

        # Set camera settings to configured calibration
        cam_config = self.get_camera_config()
        self.update_camera_config(cam_config["X"], cam_config["Y"], cam_config["IMG_P"])

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

    def get_unit_id(self):
        """Return device id"""
        return self.config.get("unit_id", "Not Set")

    def get_unit_version(self):
        """Return device software version"""
        return self.config.get("version", "Not Set")

    def get_led_data(self):
        """Return led data"""
        return self.data_manager.get_led_data()

    def update_led_data(self, new_data):
        """Update led data with new values"""
        self.data_manager.update_led_data(new_data)

    def get_zoom_data(self):
        """Return zoom data"""
        return self.data_manager.get_zoom_data()

    def update_zoom_data(self, new_data):
        """Update zoom data with new values"""
        self.data_manager.update_zoom_data(new_data)

    def get_calibration(self):
        """Return calibration data"""
        return self.data_manager.get_calibration()

    def get_current_calibration(self):
        return self.data_manager.get_current_calibration()

    def update_calibration(self, new_data):
        """Update calibration data with new values"""
        self.data_manager.update_calibration(new_data)

    def update_current_calibration(self, new_data):
        """Update calibration data with new values"""
        self.data_manager.update_current_calibration(new_data)

    def restore_calibration(self):
        """Restore calibration to factory default"""
        self.data_manager.restore_factory_calibration()

    def get_camera_config(self):
        """Return camera config"""
        return self.data_manager.get_calibration()["camera_config"]

    def get_current_camera_config(self):
        """Return camera config"""
        return self.data_manager.get_current_calibration()["camera_config"]

    def toggle_led(self):
        """Toggle led"""
        self.led_control.toggle_led()

    def get_sfp_diagnostics(self):
        """Expose sfp getter"""
        return self.sfp_data

    def get_motor_status(self):
        """Return status of motor"""
        return self.motor_control.get_motors_connected()

    def _update_sfp_diagnostics(self):
        """Run in thread to update sfp diagnostics and update LED color"""
        while self.running:
            # TODO handle properly
            # try:
            self.sfp_data = self._get_sfp_data()
            # print(f"Sfp data: {self.sfp_data}")
            rx_power_dBm = self.sfp_data.get("sfp_0", {}).get("diagnostics", {}).get("rx_power_dBm", -40)
            # print(f"Rx_power_dbm: {rx_power_dBm}")
            self.set_led_color(rx_power_dBm)
            # except Exception as e:
            #     log.warning(f"An exception occured when updating sfp diagnostics: {e}")
            time.sleep(0.2)  # update five times

    def issue_remote_command(self, command, params):
        """Issue RPC call to other unit with a RPC client instance"""
        # make synchronous for now, later this will have to be async for it to work! TODO
        
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
        if rx_power >= -3:
            color = Color.PERFECT_SIGNAL
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

    def take_picture(self):
        """Take picture and return int array"""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        LOCALHOST = s.getsockname()[0]
        s.close()
        VIDEO_STREAM_SRC = f"http://{LOCALHOST}:8080/?action=snapshot"

        r = requests.get(VIDEO_STREAM_SRC, stream=True)
        if r.status_code == 200:
            return r.content  # returning this is by faaaar the fastest method, takes 0.2 seconds for whole call - check commit #cee4070 for some tests
        else:
            return None

    def hard_reset(self):
        """Power cycle motor driver unit"""
        self.gpio_control.koruza_reset()

    def update_unit(self):
        """Call update.sh script to update unit to latest version"""
        try:
            r = requests.get('https://api.github.com/repos/IRNAS/koruza-v2-pro/releases')
            latest_release = r.json()[0]  # first element of list is the first release
            latest_tag = latest_release.get("tag_name", "")
            if latest_tag == "":
                return False, ""
            else:
                local_tag = self.config.get("version", "")
                if latest_tag != local_tag:
                    proc = subprocess.Popen(f"./koruza_v2/update.sh {latest_tag}", stdout=subprocess.PIPE, shell=True)
                    set_config("version", latest_tag)
                    return True, latest_tag
                else:
                    return False, latest_tag
                
        except Exception as e:
            log.error(f"An error occured when trying to update unit: {e}")

    def update_camera_config(self, zoom_factor=None, x=0, y=0, img_p=1):
        """Update camera config by setting new zoom factor"""
        # get new values from desired zoom factor
        if zoom_factor is not None:
            x, y, img_p = calculate_camera_config(zoom_factor)
        # set new values
        set_camera_config(x, y, img_p)

        # restart video stream service
        subprocess.call("sudo /bin/systemctl restart video_stream.service".split(" "))

    def update_camera_calib(self, cam_config=None):
        """Update camera_config in calibration.json"""
        if cam_config is None:
            cam_config = get_camera_config()
        self.data_manager.update_camera_config({"X": cam_config["x"], "Y": cam_config["y"], "IMG_P": cam_config["img_p"]})


    def update_current_camera_calib(self):
        cam_config = get_camera_config()
        self.data_manager.update_current_camera_config({"X": cam_config["x"], "Y": cam_config["y"], "IMG_P": cam_config["img_p"]})

    def focus_on_marker(self, marker_x, marker_y, img_p, cam_config):
        """Focus on marker from given params"""
        # covert to global coordinates
        global_marker_x = marker_x * img_p + cam_config["X"] * 720
        global_marker_y = (1.0 - cam_config["Y"]) * 720.0 - (720 - marker_y) * img_p
        marker_x = round(global_marker_x)
        marker_y = round(global_marker_y)

        # get new position of top left zoom area based on calculation
        x, y, clamped_x, clamped_y = calculate_zoom_area_position(marker_x, marker_y, img_p)
        
        if img_p != 1.0:
            marker_x, marker_y = calculate_marker_pos(x, y, img_p)

        # set new values
        set_camera_config(clamped_x, clamped_y, img_p)

        # restart video stream service
        subprocess.call("sudo /bin/systemctl restart video_stream.service".split(" "))

        return marker_x, marker_y

def clamp(n, smallest, largest): 
    return max(smallest, min(n, largest))

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