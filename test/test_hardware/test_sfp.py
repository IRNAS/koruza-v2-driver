import unittest
import smbus

from random import randrange

from ...hardware.sfp import Sfp

"""
Run tests with `sudo python3 -m unittest -v koruza_v2.koruza_v2_driver.test.test_hardware.test_sfp`

This will test one of the two SFPs in given KORUZA unit. 
See ./test_integration/test_sfp_monitor for integration test of both SFPs
"""

class TestSFPDriver(unittest.TestCase):

    # This runs once before test methods in this class are run
    @classmethod
    def setUpClass(cls):
        cls.driver = Sfp()  #use in all funtions

    """Init tests"""
    def test_class_init_good_address(self):
        """
        Test driver initialization with correct address.
        Expected value is not None.
        """
        self.assertIsNotNone(self.driver.i2c_bus, "Address is good, so i2c bus must be Not None")

    def test_get_diagnostics(self):
        """
        Test get_diagnostics with call to diagnostics register
        """

        ret = self.driver.get_diagnostics()
        expected_keys = ["temp", "tx_power_dBm", "tx_power", "rx_power_dBm", "rx_power"]

        for key, value in ret.items():
            if key not in expected_keys:
                self.fail(f"Unexpected key in sfp diagnostics dict: {key}")

            if value is None:
                self.fail(f"Value {value} with key {key} should not be None!")

    def test_get_module_info(self):
        """
        Test get_module_info which fills up on init(). All dict values should be populated.
        """

        ret = self.driver.get_module_info()
        expected_keys = ["manufacturer", "revision", "serial_num", "sfp_type", "connector", "bitrate", "wavelength"]

        for key, value in ret.items():
            if key not in expected_keys:
                self.fail(f"Unexpected key in sfp module_info dict: {key}")

            if value is None:
                self.fail(f"Value {value} with key {key} should not be None!")