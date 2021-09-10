"""
Updates local data - used to sync data between modules
"""

import json
from threading import Lock
from filelock import FileLock

DATA_FILENAME = "./koruza_v2/koruza_v2_driver/data/data.json"
CALIBRATION_FILENAME = "./koruza_v2/config/calibration.json"
FACTORY_DEFAULTS = "./koruza_v2/config/factory_defaults.json"  # file is write protected, login as root and use # chattr +i factory_defaults.json, to restore us chattr -i factory_defaults.json

class DataManager():
    def __init__(self):
        """Init data manager"""
        self.lock = Lock()

        self.data = self.load_json_file(DATA_FILENAME)
        self.calibration = self.load_json_file(CALIBRATION_FILENAME)

        print(f"Saved calibration: {self.calibration}")

    def update_calibration(self, key_value_pairs):
        """Update calibration data with given key_value_pairs"""
        print("Updating calibration data")
        self.lock.acquire()
        with FileLock(CALIBRATION_FILENAME + ".lock"):
            with open(CALIBRATION_FILENAME, "w") as calibration_file:
                for key, data in key_value_pairs:
                    print(key, data)
                    self.calibration["calibration"][key] = data
                    print(self.calibration)
                json.dump(self.calibration, calibration_file, indent=4)
        self.lock.release()

    def get_calibration(self):
        """Getter for motor data"""
        self.lock.acquire()
        calibration = self.calibration
        self.lock.release()
        return calibration 

    def restore_factory_calibration(self):
        """Restore calibration to factory settings"""
        print("Resetting calibration data")
        self.lock.acquire()
        default_settings = self.load_json_file(FACTORY_DEFAULTS)

        print(f"Default settings: {default_settings}")

        with FileLock(CALIBRATION_FILENAME + ".lock"):
            with open(CALIBRATION_FILENAME, "w") as calibration_file:
                # for key, data in self.calibration["calibration"].values():
                # print(key, data)
                self.calibration["calibration"]["offset_x"] = default_settings["calibration"]["offset_x"]
                self.calibration["calibration"]["offset_y"] = default_settings["calibration"]["offset_y"]
                print(self.calibration)
                json.dump(self.calibration, calibration_file, indent=4)
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

    def load_json_file(self, filename):
        """Loads json file"""
        with FileLock(filename + ".lock"):
            with open(filename) as data_file:
                return json.load(data_file)