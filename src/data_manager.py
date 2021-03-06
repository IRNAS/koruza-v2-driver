"""
Updates local data - used to sync data between modules
"""

import json
from pathlib import Path
from threading import Lock
from filelock import FileLock

DATA_FILENAME = "./koruza_v2/koruza_v2_driver/data/data.json"
CALIBRATION_FILENAME = "./koruza_v2/config/calibration.json"
FACTORY_DEFAULTS = "./koruza_v2/config/factory_defaults.json"  # file is write protected, login as root and use # chattr +i factory_defaults.json, to restore us chattr -i factory_defaults.json
CURRENT_CALIBRATION_FILENAME = "./koruza_v2/config/current_calibration.json"

class DataManager():
    def __init__(self):
        """Init data manager"""
        self.lock = Lock()

        self.data = self.load_json_file(DATA_FILENAME)

        print(f"Loading calibration")
        self.calibration = self.load_json_file(CALIBRATION_FILENAME)

        print(f"Saved calibration: {self.calibration}")

        self.create_temp_file()
        self.current_calibration = self.load_json_file(CURRENT_CALIBRATION_FILENAME)

    def create_temp_file(self):
        with open(CALIBRATION_FILENAME, "r") as out_file:
            file_exists = Path(CURRENT_CALIBRATION_FILENAME).is_file()
            print(f"File exists: {file_exists}")
            if not file_exists:
                with open(CURRENT_CALIBRATION_FILENAME, "w+") as in_file:
                    for line in out_file:
                        in_file.write(line)

    def update_current_calibration(self, calib_json):
        """Update calibration data with given calib_json"""
        print(f"Updating calibration data with: {calib_json}")
        self.lock.acquire()
        try:
            with FileLock(CURRENT_CALIBRATION_FILENAME + ".lock"):
                with open(CURRENT_CALIBRATION_FILENAME, "w") as calibration_file:
                    for key, data in calib_json.items():
                        print(key, data)
                        self.current_calibration["calibration"][key] = data
                    json.dump(self.current_calibration, calibration_file, indent=4)
            print(self.current_calibration)
        except Exception as e:
            print(f"Error: {e}")
        self.lock.release()

    def update_current_camera_config(self, config_json):
        """Update camera config"""
        print(f"Updating camera config data with: {config_json}")
        self.lock.acquire()
        try:
            with FileLock(CURRENT_CALIBRATION_FILENAME + ".lock"):
                with open(CURRENT_CALIBRATION_FILENAME, "w") as calibration_file:
                    for key, data in config_json.items():
                        print(key, data)
                        self.current_calibration["camera_config"][key] = data
                    json.dump(self.current_calibration, calibration_file, indent=4)
            print(self.current_calibration)
        except Exception as e:
            print(f"Error: {e}")
        self.lock.release()

    def update_camera_config(self, config_json):
        """Update camera config"""
        print(f"Updating camera config data with: {config_json}")
        self.lock.acquire()
        try:
            with FileLock(CALIBRATION_FILENAME + ".lock"):
                with open(CALIBRATION_FILENAME, "w") as calibration_file:
                    for key, data in config_json.items():
                        print(key, data)
                        self.calibration["camera_config"][key] = data
                    json.dump(self.calibration, calibration_file, indent=4)
            print(self.calibration)
        except Exception as e:
            print(f"Error: {e}")
        self.lock.release()

    def update_calibration(self, calib_json):
        """Update calibration data with given calib_json"""
        print(f"Updating calibration data with: {calib_json}")
        self.lock.acquire()
        try:
            with FileLock(CALIBRATION_FILENAME + ".lock"):
                with open(CALIBRATION_FILENAME, "w") as calibration_file:
                    for key, data in calib_json.items():
                        print(key, data)
                        self.calibration["calibration"][key] = data
                    json.dump(self.calibration, calibration_file, indent=4)
            print(self.calibration)
        except Exception as e:
            print(f"Error: {e}")
        self.lock.release()

    def get_calibration(self):
        """Getter for calibration data"""
        self.lock.acquire()
        calibration = self.calibration
        self.lock.release()
        return calibration 

    def get_current_calibration(self):
        self.lock.acquire()
        calib = self.current_calibration
        self.lock.release()
        return calib

    def restore_factory_calibration(self):
        """Restore calibration to factory settings"""
        print("Resetting calibration data")
        self.lock.acquire()
        default_settings = self.load_json_file(FACTORY_DEFAULTS)

        print(f"Default settings: {default_settings}")
        with FileLock(CURRENT_CALIBRATION_FILENAME + ".lock"):
            with open(CURRENT_CALIBRATION_FILENAME, "w") as calibration_file:
                # print(key, data)
                self.current_calibration["calibration"]["offset_x"] = default_settings["calibration"]["offset_x"]
                self.current_calibration["calibration"]["offset_y"] = default_settings["calibration"]["offset_y"]
                self.current_calibration["calibration"]["zoom_level"] = default_settings["calibration"]["zoom_level"]
                self.current_calibration["camera_config"]["X"] = default_settings["camera_config"]["X"]
                self.current_calibration["camera_config"]["Y"] = default_settings["camera_config"]["Y"]
                self.current_calibration["camera_config"]["IMG_P"] = default_settings["camera_config"]["IMG_P"]
                print(self.current_calibration)
                json.dump(self.current_calibration, calibration_file, indent=4)
        self.lock.release()

    def update_motors_data(self, key_value_pairs):
        """Update motors data with given key_value_pairs"""
        self.lock.acquire()
        with FileLock(DATA_FILENAME + ".lock"):
            with open(DATA_FILENAME, "w") as data_file:
                for key, data in key_value_pairs:
                    self.data["motors"][key] = data
                    # print(self.motors)
                json.dump(self.data, data_file, indent=4)
        self.lock.release()

    def get_motor_data(self):
        """Getter for motor data"""
        self.lock.acquire()
        motor_data = self.data["motors"]
        self.lock.release()
        return motor_data

    def update_led_data(self, value):
        """Update camera data with given key_value_pairs"""
        self.lock.acquire()
        with FileLock(DATA_FILENAME + ".lock"):
            with open(DATA_FILENAME, "w") as data_file:
                self.data["led"] = value
                json.dump(self.data, data_file, indent=4)
                print(f"New led data: {self.data}")
        self.lock.release()

    def get_led_data(self):
        """Getter for led data"""
        self.lock.acquire()
        led_data = self.data["led"]
        self.lock.release()
        return led_data

    def update_zoom_data(self, value):
        """Update camera zoom data with given value"""
        self.lock.acquire()
        with FileLock(DATA_FILENAME + ".lock"):
            with open(DATA_FILENAME, "w") as data_file:
                self.data["zoom"] = value
                json.dump(self.data, data_file, indent=4)
                print(f"New zoom data: {self.data}")
        self.lock.release()

    def get_zoom_data(self):
        """Getter for zoom data"""
        self.lock.acquire()
        zoom_data = self.data["zoom"]
        self.lock.release()
        return zoom_data

    def load_json_file(self, filename):
        """Loads json file"""
        with FileLock(filename + ".lock"):
            with open(filename) as data_file:
                return json.load(data_file)