"""
Pca9554 driver, NXP Semiconductors
8 bit I2C expander, 8 GPIO ports
I2C SMBus protocol
Manual: PCA9554_9554A.pdf
Copyright (C) 2019 Vid Rajtmajer <vid@irnas.eu>
"""
import logging
from smbus2 import SMBus

from ..src.constants import I2C_CHANNEL


class Pca9546():
    def __init__(self, address):
        """Init smbus channel and Pca9546 driver on specified address."""
        try:
            self.i2c_bus = SMBus(I2C_CHANNEL)
            self.i2c_address = address              # whatever we see on RPi
            if self.read_config_register() is None:
                raise ValueError
        except ValueError:
            logging.error("Pca9546 ERROR: No device found on address {}!".format(hex(address)))
            self.i2c_bus = None
        except:
            logging.error("Bus on channel {} is not available. Error raised by Pca9546.".format(I2C_CHANNEL))
            logging.info("Available busses are listed as /dev/i2c*")
            self.i2c_bus = None
   
    def __del__(self):
        """Driver destructor."""
        self.i2c_bus = None

    def read_config_register(self):
        try:
            return self.i2c_bus.read_byte(self.i2c_address)
        except:
            return None

    def select_channel(self, val=None, ch0=0, ch1=0, ch2=0, ch3=0):
        """

        """
        if val is None:
            val = ch0 | (ch1<<1) | (ch2<<2) | (ch3<<3)
        try:
            self.i2c_bus.write_byte(self.i2c_address, val)
            return True
        except:
            return False