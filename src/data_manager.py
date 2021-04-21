"""
Updates local data - used to sync data between modules
"""

import json
from threading import Lock
from filelock import FileLock

DATA_FILENAME = "./koruza_v2/koruza_v2_driver/data/data.json"

class DataManager():
    def __init__(self):
        """Init data manager"""
        self.lock = Lock()

        self.data = self.load_json_file(DATA_FILENAME)

    def update_calibration_data(self, key_value_pairs):
        """Update calibration data with given key_value_pairs"""
        print("Updating calibration data")
        self.lock.acquire()
        with FileLock(DATA_FILENAME + ".lock"):
            with open(DATA_FILENAME, "w") as data_file:
                for key, data in key_value_pairs:
                    print(key, data)
                    self.data["calibration"][key] = data
                    print(self.data)
                json.dump(self.data, data_file, indent=4)
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

    def update_led_data(self, value):
        """Update camera data with given key_value_pairs"""
        self.lock.acquire()
        with FileLock(DATA_FILENAME + ".lock"):
            with open(DATA_FILENAME, "w") as data_file:
                self.data["led"] = value
                json.dump(self.data, data_file, indent=4)
                print(f"New led data: {self.data}")
        self.lock.release()

    def load_json_file(self, filename):
        """Loads json file"""
        with FileLock(filename + ".lock"):
            with open(filename) as data_file:
                return json.load(data_file)