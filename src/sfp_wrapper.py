import time
import logging

from ..hardware.sfp_driver import Sfp
from ..hardware.pca9546 import Pca9546
from .constants import SFP_TRANSMIT, SFP_RECEIVE

Pca9546_address = 0x70
SFP_TRANSMIT_line = 0x01
SFP_RECEIVE_line = 0x02

class SfpWrapper():
    def __init__(self):
        """Init sfp wrapper:
            - init an instance of the pca9546 switch
            - init an instance of the sfp class
            - we're switching between two sfp's with the same address - one for receiving and one for transmitting data
        """
        self.switch = None
        self.sfp_0 = None
        self.sfp_1 = None

        self.data = {
            "sfp_0": {
                "module_info": None,
                "diagnostics": None
            },
            "sfp_1": {
                "module_info": None,
                "diagnostics": None
            }
        }

        try:
            self.switch = Pca9546(Pca9546_address)
        except Exception as e:
            logging.error(e)

        try:
            self.init()
        except Exception as e:
            logging.error(e)

    def init(self):
        """Initialize wrapper"""
        if self.switch is not None:
            
            print("Initing sfp 0")
            # initialize sfp_0
            self.switch.select_channel(val=SFP_TRANSMIT_line)
            try:
                self.sfp_0 = Sfp()
                self.data["sfp_0"]["module_info"] = self.sfp_0.get_module_info()
            except Exception as e:
                logging.error(e)

            print("Initing sfp 1")
            # initialize sfp_1
            self.switch.select_channel(val=SFP_RECEIVE_line)
            try:
                self.sfp_1 = Sfp()
                self.data["sfp_1"]["module_info"] = self.sfp_1.get_module_info()
            except Exception as e:
                logging.error(e)

    def update_sfp_diagnostics(self):
        """Get data from both sfp's"""
        if self.switch is not None:
            
            # print("Getting sfp 0 data")
            # initialize sfp_0
            self.switch.select_channel(val=SFP_TRANSMIT_line)
            try:
                self.data["sfp_0"]["diagnostics"] = self.sfp_0.get_diagnostics()
                # print(self.data["sfp_0"])
            except Exception as e:
                logging.error(e)

            # print("Getting sfp 1 data")
            # initialize sfp_1
            self.switch.select_channel(val=SFP_RECEIVE_line)
            try:
                self.data["sfp_1"]["diagnostics"] = self.sfp_1.get_diagnostics()
                # print(self.data["sfp_1"])
            except Exception as e:
                logging.error(e)

    def get_module_info(self, module_select):
        """Return module info of selected module"""
        return self.data[f"sfp_{module_select}"]["module_info"]

    def get_module_diagnostics(self, module_select):
        """Return module diagnostics of selected module"""
        return self.data[f"sfp_{module_select}"]["diagnostics"]

# wrapper = SfpWrapper()
# for i in range(0, 100):
#     time.sleep(1)
#     wrapper.update_sfp_diagnostics()
#     print(f"Getting module 0 diagnostics: {wrapper.get_module_diagnostics(0)}")
#     print(f"Getting module 1 diagnostics: {wrapper.get_module_diagnostics(1)}")