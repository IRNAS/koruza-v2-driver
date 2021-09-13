import unittest
import smbus

from random import randrange

from ...hardware.pca9546a import Pca9546a

"""Run tests with `sudo python3 -m unittest -v koruza_v2.koruza_v2_driver.test.test_hardware.test_pca9546a`"""

class TestPca9546aDriver(unittest.TestCase):

    # This runs once before test methods in this class are run
    @classmethod
    def setUpClass(cls):
        cls.driverGood = Pca9546a(0x70)  #use in all funtions
        cls.driverBad = Pca9546a(0x69)


    """Init tests"""
    def test_class_init_good_address(self):
        """
        Test driver initialization with correct address.
        Expected value is not None.
        """
        self.assertIsNotNone(self.driverGood.i2c_bus, "Address is good, so i2c bus must be Not None")

    def test_class_init_bad_address(self):
        """
        Test driver initialization with incorrect chip address.
        Expected value is None.
        """
        self.assertIsNone(self.driverBad.i2c_bus, "Address is bad, so i2c bus must be None")


    """Control byte settings tests"""
    def test_select_channel(self):
        """
        Test all good channel configurations. Values from 0 to 15.
        Expected value is True.
        Read register after setting it. Expected return value is the set value.
        """

        for i in range(0, 16):  # write all possible values to register
            with self.subTest():
                ret = self.driverGood.select_channel(val=i)
                self.assertTrue(ret, "Return value should be True!")

                config_reg = self.driverGood.read_config_register()
                self.assertEqual(config_reg, i, f"Set value {i} should match read value {config_reg}")

    def test_select_channel_wrong_type(self):
        """
        Test select_channel with wrong input types.
        Expected input type is `integer`.
        Expected return value is False.
        """
        inputs = [None, "string", 0.0001, 1.0, -1.0, {}]
        for input in inputs:
            with self.subTest():
                ret = self.driverGood.select_channel(val=input)
                self.assertFalse(ret, "Return value should be False!")

    def test_select_channel_out_of_bounds(self):
        """
        Test select_channel with out of bound values.
        Test values < 0 and > 15.
        Expected return value is False.
        """
        inputs = [-1, 16, 2**12, -2**16]
        for input in inputs:
            with self.subTest():
                ret = self.driverGood.select_channel(val=input)
                self.assertFalse(ret, "Return value should be False!")

    """
    Control byte settings test with wrong address.
    Repeat above tests with uninitialized driver.
    """
    def test_select_channel_bad_addr(self):
        """
        Test all good channel configurations. Values from 0 to 15.
        Expected value is True.
        Read register after setting it. Expected return value is the set value.
        """

        for i in range(0, 16):  # write all possible values to register
            with self.subTest():
                ret = self.driverBad.select_channel(val=i)
                self.assertFalse(ret, "Return value should be False!")

                config_reg = self.driverBad.read_config_register()
                self.assertIsNone(config_reg, f"Read value {config_reg} should be None")

    def test_select_channel_wrong_type_bad_addr(self):
        """
        Test select_channel with wrong input types.
        Expected input type is `integer`.
        Expected return value is False.
        """
        inputs = [None, "string", 0.0001, 1.0, -1.0, {}]
        for input in inputs:
            with self.subTest():
                ret = self.driverBad.select_channel(val=input)
                self.assertFalse(ret, "Return value should be False!")

    def test_select_channel_out_of_bounds_bad_addr(self):
        """
        Test select_channel with out of bound values.
        Test values < 0 and > 15.
        Expected return value is False.
        """
        inputs = [-1, 16, 2**12, -2**16]
        for input in inputs:
            with self.subTest():
                ret = self.driverBad.select_channel(val=input)
                self.assertFalse(ret, "Return value should be False!")

if __name__ == '__main__':
    unittest.main()