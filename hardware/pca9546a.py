"""
Pca9546 driver, NXP Semiconductors
4 bit I2C expander, 4 GPIO ports
I2C SMBus protocol
Datasheet: https://www.nxp.com/docs/en/data-sheet/PCA9546A.pdf
"""
import logging
from smbus2 import SMBus

from ...src.constants import I2C_CHANNEL

log = logging.getLogger()

class Pca9546a():
    def __init__(self, address):
        """Init smbus channel and Pca9546 driver on specified address."""
        try:
            self.i2c_bus = SMBus(I2C_CHANNEL)
            self.i2c_address = address              # whatever we see on RPi
            if self.read_config_register() is None:
                raise ValueError
        except ValueError:
            log.error("Pca9546 ERROR: No device found on address {}!".format(hex(address)))
            self.i2c_bus = None
        except:
            log.error("Bus on channel {} is not available. Error raised by Pca9546.".format(I2C_CHANNEL))
            log.info("Available busses are listed as /dev/i2c*")
            self.i2c_bus = None
   
    def __del__(self):
        """Driver destructor."""
        self.i2c_bus = None

    def read_config_register(self):
        try:
            return self.i2c_bus.read_byte(self.i2c_address)
        except Exception as e:
            log.error(f"An exception occured when trying to read config register: {e}")
            return None

    def select_channel(self, val=None, ch0=0, ch1=0, ch2=0, ch3=0):
        """
        Set internal register to desired combination of channels.
        """

        if type(val) is not int:
            log.error(f"Input value must be an integer!")
            return False

        if val < 0 or val > 15:
            log.error(f"Specified channel configuration must be between 0000 (0 dec) and 1111 (15 dec)")
            return False

        if ch0 < 0 or ch0 > 1:
            log.error(f"Channel 0 must be set to either 0 or 1")
            return False

        if ch1 < 0 or ch1 > 1:
            log.error(f"Channel 1 must be set to either 0 or 1")
            return False
        
        if ch2 < 0 or ch2 > 1:
            log.error(f"Channel 2 must be set to either 0 or 1")
            return False

        if ch3 < 0 or ch3 > 1:
            log.error(f"Channel 3 must be set to either 0 or 1")
            return False

        if val is None:
            val = ch0 | (ch1<<1) | (ch2<<2) | (ch3<<3)
        try:
            self.i2c_bus.write_byte(self.i2c_address, val)
            return True
        except Exception as e:
            log.error(f"An exception occured when trying to write config register: {e}")
            return False
