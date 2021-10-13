import time
import logging

from ..hardware.sfp import Sfp
from ..hardware.pca9546a import Pca9546a

log = logging.getLogger()

Pca9546a_address = 0x70
SFP_CAMERA_line = 0x01
SFP_OUT_line = 0x02

SFP_CAMERA = 0
SFP_OUT = 1

class SfpMonitor():
    def __init__(self):
        """Init sfp wrapper:
            - init an instance of the Pca9546a switch
            - init an instance of the sfp class
            - we're switching between two sfp's with the same address - one for receiving and one for transmitting data
        """
        self.switch = None
        self.sfp_0 = None
        self.sfp_1 = None

        self.data = {
            "sfp_0": {
                "module_info": {},
                "diagnostics": {}
            },
            "sfp_1": {
                "module_info": {},
                "diagnostics": {}
            }
        }

        try:
            self.switch = Pca9546a(Pca9546a_address)
        except Exception as e:
            log.error(f"Error when initializing pca9546a switch: {e}")

        try:
            self.init()
        except Exception as e:
            log.error(f"Error when initializing sfp drivers: {e}")

    def init(self):
        """Initialize wrapper"""
        if self.switch is not None:
            self.switch.select_channel(val=SFP_CAMERA_line)
            try:
                self.sfp_0 = Sfp()
                self.data["sfp_0"]["module_info"] = self.sfp_0.get_module_info()
                log.info("Initialized sfp 0")
            except Exception as e:
                log.error(f"Error when initializing sfp 0: {e}")

            self.switch.select_channel(val=SFP_OUT_line)
            try:
                self.sfp_1 = Sfp()
                self.data["sfp_1"]["module_info"] = self.sfp_1.get_module_info()
                log.info("Initialized sfp 1")
            except Exception as e:
                log.error(f"Error when initializing sfp 1: {e}")

            print(self.data)

    def update_sfp_diagnostics(self):
        """Get data from both sfp's"""
        if self.switch is not None:
            if self.sfp_0:
                self.switch.select_channel(val=SFP_CAMERA_line)
                try:
                    self.data["sfp_0"]["diagnostics"] = self.sfp_0.get_diagnostics()
                except Exception as e:
                    log.error(f"Error when getting sfp 0 diagnostics: {e}")

            if self.sfp_1:
                self.switch.select_channel(val=SFP_OUT_line)
                try:
                    self.data["sfp_1"]["diagnostics"] = self.sfp_1.get_diagnostics()
                except Exception as e:
                    log.error(f"Error when getting sfp 1 diagnostics: {e}")

    def get_module_info(self, module_select):
        """Return module info of selected module"""
        return self.data[f"sfp_{module_select}"]["module_info"]

    def get_module_diagnostics(self, module_select):
        """Return module diagnostics of selected module"""
        return self.data[f"sfp_{module_select}"]["diagnostics"]

    def get_complete_diagnostics(self):
        """Return both sets of diagnostics"""
        return self.data