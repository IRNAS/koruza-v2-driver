# koruza-v2-driver

## Contents and Structure

### Hardware
Low level drivers interfacing directly with I2C devices are placed in the `hardware` folder.
* pca9546a: Used to switch between SFP's
* sfp: Low level I2C driver to communicate with the SFP

### Wrappers
Wrappers for above drivers are placed in the `src` folder.
* sfp_monitor: wraps the `pca9546a` driver and the `sfp driver` to provide high level monitoring of both SFP's
* motor_control: provides a high level interface for the [KORUZA Move Driver Firmware](https://github.com/IRNAS/koruza-move-driver-firmware). The KORUZA Move Driver uses the TLV encoding scheme and the hardware serial interface to exchange commands with the Compute Module
* led_control: wraps the `rpi_ws281x` driver to provide a high level control of the KORUZA LED diode
* gpio_control: provides high level control of the Compute Module GPIO pins
* communication: wraps the TLV encoding scheme to provide a easy to use interface
* koruza: encapsulates all wrappers and exposes methods for interaction with the code

### Main Code
* main: serves `koruza` methods using the XML-RPC protocol. This enables users to write their own UI and other expansion modules if they so desire. 