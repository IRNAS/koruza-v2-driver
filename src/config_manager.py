"""
Updates global config - used to sync file between modules
"""

import json
from threading import Lock
from filelock import FileLock

CONFIG_FILENAME = "./koruza_v2/koruza_v2_driver/config/config.json"

class ConfigManager():
    def __init__(self):
        """Init config manager"""
        # self.SETTINGS_FILE = "./koruza_v2/config.json"
        # self.config = self.load_json_file()
        self.lock = Lock()

        self.config = self.load_json_file(CONFIG_FILENAME)

    def get_camera_config(self):
        """Return updated camera config"""
        return self.camera

    def update_calibration_config(self, key_value_pairs):
        """Update calibration config with given key_value_pairs"""
        print("Updating calibration config")
        self.lock.acquire()
        with FileLock(CONFIG_FILENAME + ".lock"):
            with open(CONFIG_FILENAME, "w") as config_file:
                for key, data in key_value_pairs:
                    print(key, data)
                    self.config["calibration"][key] = data
                    print(self.config)
                json.dump(self.config, config_file, indent=4)
        self.lock.release()

    def update_motors_config(self, key_value_pairs):
        """Update motors config with given key_value_pairs"""
        self.lock.acquire()
        with FileLock(CONFIG_FILENAME + ".lock"):
            with open(CONFIG_FILENAME, "w") as config_file:
                for key, data in key_value_pairs:
                    self.config["motors"][key] = data
                    # print(self.motors)
                json.dump(self.config, config_file, indent=4)
        self.lock.release()

    def update_camera_config(self, key_value_pairs):
        """Update camera config with given key_value_pairs"""
        self.lock.acquire()
        with FileLock(CONFIG_FILENAME + ".lock"):
            with open(CONFIG_FILENAME, "w") as config_file:
                for key, data in key_value_pairs:
                    self.config["camera"][key] = data
                json.dump(self.config, config_file, indent=4)
                print(f"New camera config: {self.config}")
        self.lock.release()

    def load_json_file(self, filename):
        """Loads json file"""
        with FileLock(filename + ".lock"):
            with open(filename) as config_file:
                return json.load(config_file)

# config_manager = ConfigManager()  # expose config manager