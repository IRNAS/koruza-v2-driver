"""Made with https://cdn.hackaday.io/files/21599924091616/AN_2030_DDMI_for_SFP_Rev_E2.pdf"""
from smbus2 import SMBus
import numpy as np
import logging
import time

I2C_CHANNEL = 1

SFP_I2C_PROBE_BUS_MAX = 5
SFP_I2C_INFO_ADDRESS = 0x50
SFP_I2C_DIAG_ADDRESS = 0x51

SFP_MANUFACTURER_REG = 20
SFP_MANUFACTURER_LENGTH = 16

SFP_REVISION_REG = 56
SFP_REVISION_LENGTH = 4

SFP_SERIAL_NO_REG = 68
SFP_SERIAL_NO_LENGTH = 16

SFP_TYPE_REG = 0
SFP_CONNECTOR_REG = 2
SFP_BITRATE_REG = 12
SFP_WAVELENGTH_REG = 60
SFP_CHECKSUM_REG = 63

SFP_DIAG_MONITORING_REG = 92

# DIAGNOSTICS REGISTERS
SFP_DIAG_REG_START = 96  # msb at 96, lsb at 97
TEMP_OFFSET = 0
VCC_OFFSET = 2
TX_BIAS_OFFSET = 4
TX_POWER_OFFSET = 6
RX_POWER_OFFSET = 8
DIAG_DATA_LENGTH = 10

class Sfp():
    def __init__(self):
        """Init smbus channel and SFP driver on specified address."""

        self.data = {
            "module_info": {
                "manufacturer": None,
                "revision": None,
                "serial_num": None,
                "sfp_type": None,
                "connector": None,
                "bitrate": None,
                "wavelength": None
            },
            "diagnostics": {
                "temp": None,
                "tx_power_dBm": None,
                "rx_power_dBm": None,
                "tx_power": None,
                "rx_power": None
            }
        }

        try:
            self.i2c_bus = SMBus(I2C_CHANNEL)
            self.init()
        except Exception as e:
            logging.error("An error occured during")
            raise Exception(e)
            self.i2c_bus = None
   
    def __del__(self):
        """Driver destructor."""
        self.i2c_bus = None

    def init(self):
        """Init and read all info registers"""
        
        try:
            manufacturer = self.i2c_bus.read_i2c_block_data(SFP_I2C_INFO_ADDRESS, SFP_MANUFACTURER_REG, SFP_MANUFACTURER_LENGTH)
            self.data["module_info"]["manufacturer"] = "".join(chr(x) for x in manufacturer)
            # print(f'Manufacturer: {self.data["manufacturer"]}')
        except Exception as e:
            raise ValueError(f"An error occured during manufacturer data i2c read: {e}")

        try:    
            revision = self.i2c_bus.read_i2c_block_data(SFP_I2C_INFO_ADDRESS, SFP_REVISION_REG, SFP_REVISION_LENGTH)
            self.data["module_info"]["revision"] = "".join(chr(x) for x in revision)
            # print(f'Revision: {self.data["revision"]}')
        except Exception as e:
            raise ValueError(f"An error occured during revision i2c read: {e}")

        try:    
            serial_num = self.i2c_bus.read_i2c_block_data(SFP_I2C_INFO_ADDRESS, SFP_SERIAL_NO_REG, SFP_SERIAL_NO_LENGTH)
            self.data["module_info"]["serial_num"] = "".join(chr(x) for x in serial_num)
            # print(f'Serial_num: {self.data["serial_num"]}')
        except Exception as e:
            raise ValueError(f"An error occured during serial number i2c read: {e}")

        try:    
            self.data["module_info"]["sfp_type"] = self.i2c_bus.read_byte_data(SFP_I2C_INFO_ADDRESS, SFP_TYPE_REG)
            # print(f'Sfp type: {self.data["sfp_type"]}')
        except Exception as e:
            raise ValueError(f"An error occured during sfp type i2c read: {e}")
        
        try:
            self.data["module_info"]["connector"] = self.i2c_bus.read_byte_data(SFP_I2C_INFO_ADDRESS, SFP_CONNECTOR_REG)
            # print(f'Connector type: {self.data["connector"]}')
        except Exception as e:
            raise ValueError(f"An error occured during connector type i2c read: {e}")

        try:    
            self.data["module_info"]["bitrate"] = self.i2c_bus.read_byte_data(SFP_I2C_INFO_ADDRESS, SFP_BITRATE_REG) * 100
            # print(f'Bitrate: {self.data["bitrate"]}')
        except Exception as e:
            raise ValueError(f"An error occured during bitrate i2c read: {e}")

        try:    
            wavelength = self.i2c_bus.read_word_data(SFP_I2C_INFO_ADDRESS, SFP_WAVELENGTH_REG)
            self.data["module_info"]["wavelength"] = (wavelength & 0xff) * 256 + ((wavelength & 0xff00) >> 8)
            # print(f'Wavelength: {self.data["wavelength"]}')
        except Exception as e:
            raise ValueError(f"An error occured during wavelength i2c read: {e}")

        try:    
            self.diag_settings = self.i2c_bus.read_byte_data(SFP_I2C_INFO_ADDRESS, SFP_DIAG_MONITORING_REG)
            # print(f"Diagnostics settings: {bin(self.diag_settings)}")  # if bit 5 is set the SFP is internally calibrated
        except Exception as e:
            raise ValueError(f"An error occured during diagnostics settings i2c read: {e}")

    def convert_to_fp(self, number, num_bits, divisor):
        """Convert num_bits bit number to a floating point number"""
        val = 0
        for bit in range(0, num_bits):
            val += (number & (1 << bit)) / divisor
        return val

    def convert_to_dB(self, mW):
        """Convert mW to dB and return value"""
        if mW == 0.0:
            return -40.0  # -40.0 is lower limit
        return 10 * np.log10(mW)

    def get_diagnostics(self):
        """Get sfp module diagnostics"""

        diagnostics_block = self.i2c_bus.read_i2c_block_data(SFP_I2C_DIAG_ADDRESS, SFP_DIAG_REG_START, DIAG_DATA_LENGTH)
        temp_bytes = diagnostics_block[TEMP_OFFSET: VCC_OFFSET]
        temp_h = float(np.int8(temp_bytes[0]))  # signed int8
        temp_l = self.convert_to_fp(temp_bytes[1], 8, 256)
        temp = temp_h + temp_l
        # print(f"Temp: {temp}")
        self.data["diagnostics"]["temp"] = temp

        # next is transciever supply voltage - skip this for now

        # next is tx bias current in uA - skip

        # next is tx output power in mW
        tx_bytes = diagnostics_block[TX_POWER_OFFSET:RX_POWER_OFFSET]
        tx_power = float(np.uint16((tx_bytes[0] << 8) | tx_bytes[1]) / 10000)  # LSB is equal to 100 uW, so the range is [0, 6.5535]mW
        # print(f"Tx power: {tx_power}mW")
        self.data["diagnostics"]["tx_power"] = tx_power
        tx_power_dbm = round(self.convert_to_dB(tx_power), 3)
        # print(f"Tx power: {tx_power_dbm}dBm")
        self.data["diagnostics"]["tx_power_dBm"] = float(tx_power_dbm)

        # next is rx received power in mW
        rx_bytes = diagnostics_block[RX_POWER_OFFSET:]
        rx_power = float(np.uint16((rx_bytes[0] << 8) | rx_bytes[1]) / 10000) # LSB is equal to 100 uW, so the range is [0, 6.5535]mW
        # print(f"Rx power: {rx_power}mW")
        self.data["diagnostics"]["rx_power"] = rx_power
        rx_power_dbm = round(self.convert_to_dB(rx_power), 3)
        # print(f"Rx power: {rx_power_dbm}dBm")
        self.data["diagnostics"]["rx_power_dBm"] = float(rx_power_dbm)

        return self.data["diagnostics"]

    def get_module_info(self):
        """Get data"""
        return self.data["module_info"]

# sfp = Sfp()
# while True:
#     sfp.get_diagnostics()
#     time.sleep(5)