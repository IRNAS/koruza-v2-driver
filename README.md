# koruza-v2-driver

## Description
KORUZA v2 Pro firmware enables core functionality of KORUZA units:
* Motor control
* SFP monitoring
* RPC interfacing with outside modules

Wrappers are used to abstract low level hardware drivers. Firmware is therefore more readable, easier to maintain, test and scale. The below code diagram displays how firmware modules are bundled together to make the KORUZA v2 Pro main code.

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

### Unit data
Each unit stores local LED state, motor positions and calibration values in a .json file. Before running the code for the first time move the included `data.json` file into the `data` folder.

A The structure of the `data.json` file is as seen below:
```
{
    "calibration": {
        "offset_x": 280,
        "offset_y": 528
    },
    "motors": {
        "last_x": -5794,
        "last_y": 2936
    },
    "led": true,
    "zoom": true
}
```
## Dependencies and older versions

* [KORUZA driver](https://github.com/IRNAS/koruza-driver) - Previous version of the Driver for KORUZA Pro units.

## License
Firmware and software originating from KORUZA v2 Pro project, including KORUZA v2 Pro Driver, is licensed under [GNU General Public License v3.0](https://github.com/IRNAS/koruza-v2-driver/blob/master/LICENSE).

Open-source licensing means the hardware, firmware, software and documentation may be used without paying a royalty, and knowing one will be able to use their version forever. One is also free to make changes, but if one shares these changes, they have to do so under the same conditions they are using themselves. KORUZA, KORUZA v2 Pro and IRNAS are all names and marks of IRNAS LTD. These names and terms may only be used to attribute the appropriate entity as required by the Open Licence referred to above. The names and marks may not be used in any other way, and in particular may not be used to imply endorsement or authorization of any hardware one is designing, making or selling.
