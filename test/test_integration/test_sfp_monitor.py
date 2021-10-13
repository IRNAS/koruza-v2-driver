import time
import smbus
import unittest

from ...src.sfp_monitor import SfpMonitor

"""
Run tests with `sudo python3 -m unittest -v koruza_v2.koruza_v2_driver.test.test_hardware.test_sfp`

This will test one of the two SFPs in given KORUZA unit. 
See ./test_integration/test_sfp_monitor for integration test of both SFPs
"""

class TestSFPMonitor(unittest.TestCase):

    # This runs once before test methods in this class are run
    @classmethod
    def setUpClass(cls):
        cls.sfp_monitor = SfpMonitor()  # use in all funtions

    """Test both sfps"""
    def test_sfps(self):
        """Check if both sfps are connected"""

        self.sfp_monitor.update_sfp_diagnostics()
        ret = self.sfp_monitor.get_complete_diagnostics()

        sfp_select = ["sfp_0", "sfp_1"]
        for sfp in ["sfp_0", "sfp_1"]:
            if ret[sfp]["module_info"] == {} or ret[sfp]["diagnostics"] == {}:
                self.fail(f"{sfp} not connected or malfunctioning!")